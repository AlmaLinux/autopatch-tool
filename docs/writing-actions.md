# Writing New Actions (Developer Guide)

This guide explains how the action engine works internally and how to add a new
action type (a new YAML key under `actions:`). All of it lives in
[`src/actions_handler.py`](../src/actions_handler.py), with RPM-specific helpers
in [`src/tools/rpm.py`](../src/tools/rpm.py).

If you only want to *write configs*, read [configuration.md](configuration.md)
instead.

## The model: Entry + Action

Every action type is a pair of classes:

| Class | Base | Responsibility |
|-------|------|----------------|
| `…Entry` | `BaseEntry` | Validate one YAML entry's keys/types; resolve the target file. |
| `…Action` | `BaseAction` | Hold a list of entries and `execute()` them against the package. |

`ConfigReader` ties them together:

```python
class ConfigReader:
    ACTION_MAP = {
        "replace": ReplaceAction,
        "delete_line": DeleteLineAction,
        "changelog_entry": ChangelogAction,
        "modify_release": ModifyReleaseAction,
        "delete_files": DeleteFilesAction,
        "add_files": AddFilesAction,
        "run_script": RunScriptAction,
        "add_line": AddLineAction,
        # ← register your new action here
    }
```

Flow when a config is applied:

```
ConfigReader(config_path)
  ├─ _load_config()        # YAML → dict
  ├─ _validate_config()    # top-level shape; action type ∈ ACTION_MAP
  ├─ build GlobalParameters from parameters:
  └─ for each action block:
        ACTION_MAP[type](entries, config_source, global_parameters)
            └─ BaseAction._create_entries() → [ENTRY_CLASS(...), ...]

ConfigReader.apply_actions(package_path)
  └─ for each action: action.execute(package_path)   # in order
```

## `BaseEntry` contract

```python
class MyEntry(BaseEntry):
    ALLOWED_KEYS = {            # key -> expected type (or tuple of types)
        "target": str,
        "count": int,
        "number": (str, int),   # multiple accepted types
    }
    REQUIRED_KEYS = {"target"}  # subset of ALLOWED_KEYS that must be present
```

`BaseEntry.__init__` runs `_validate_keys(kwargs)`, which:

- rejects unknown keys (anything not in `ALLOWED_KEYS`);
- rejects missing `REQUIRED_KEYS`;
- type-checks every provided value against `ALLOWED_KEYS`;
- rejects empty values for required keys (except booleans).

Then it stores every kwarg as an attribute (`self.<key> = value`) and saves
`self.global_parameters`.

Two things you usually do in your Entry's `__init__`:

1. **Apply defaults** for optional keys:
   ```python
   def __init__(self, global_parameters, **kwargs):
       super().__init__(global_parameters, **kwargs)
       self.count = kwargs.get("count", -1)
   ```
2. **Set `self.target`** — the file the action operates on. This is consumed by
   the inherited helpers:
   - `get_target_file_name(package_path, first=True)` — if `target == "spec"`,
     finds the single `*.spec`; otherwise finds files matching `self.target`
     (glob-aware, skips `tests/` dirs). Returns one path, or a list when
     `first=False`.
   - `get_file_name(package_path, name, first=True)` — generic recursive lookup.

   If your action doesn't operate on a file, set `self.target = ""`.

Add any extra validation you need and `raise ValueError`/`TypeError` with a
clear message (see `ReplaceEntry` for the mutually-exclusive `find`/`rfind`
pattern, or `AddFilesEntry._validate_number`).

## `BaseAction` contract

```python
class MyAction(BaseAction):
    ENTRY_CLASS = MyEntry

    def execute(self, package_path: Path):
        for entry in self.entries:
            ...
```

- `ENTRY_CLASS` tells the base how to build entries.
- `self.entries` — the validated entry objects.
- `self.config_source` — `Path` to the `config.yaml`. Use
  `self.config_source.parent / "files"` and `… / "scripts"` to reach bundled
  files (as `AddFilesAction` and `RunScriptAction` do).
- `self.global_parameters` — the `GlobalParameters` instance.
- `execute(package_path)` is **the only method you must implement.** It receives
  the path to the package working tree (the dist-git checkout).

## Helpers you should reuse

From `actions_handler.py`:

| Helper | Use |
|--------|-----|
| `read_file_data(path) -> list[str]` | Read a file as a list of lines (newlines stripped). Raises on empty. |
| `write_file_data(path, lines)` | Write a list of lines back. |
| `process_lines(path, target, find_lines, replace_lines, count, is_regex=False)` | The shared find/replace/delete engine used by `replace` and `delete_line`. Pass `replace_lines=""` to delete. Raises `ActionNotAppliedError` if nothing changed. |
| `ActionNotAppliedError(action_name, reason)` | Raise when your action verifies it changed nothing — this is how the engine surfaces stale configs. |

From `tools/rpm.py` (when working with spec files):

| Helper | Use |
|--------|-----|
| `apply_patch(...)` | Insert a `PatchNNN:`/`SourceNNN:` + apply directive correctly. |
| `add_line_to_section(spec, section, location, content, subpackage)` | Insert into a spec section. |
| `find_section_boundaries(...)`, `get_version_information(...)`, `is_release(...)`, `is_changelog(...)`, `spec_contains_autosetup/autochangelog(...)` | Spec parsing primitives. |

From `tools/tools.py`:

| Helper | Use |
|--------|-----|
| `run_command(cmd, raise_on_failure=True, cwd=None, timeout=None)` | Run a subprocess (used by `run_script`). |

## Step-by-step: add a new action

We'll add an `append_file` action that appends content to the end of a file.

### 1. Define the Entry

```python
class AppendFileEntry(BaseEntry):
    """Entry for the AppendFileAction."""
    ALLOWED_KEYS = {
        "target": str,
        "content": str,
    }
    REQUIRED_KEYS = {"target", "content"}
    # `target` is inherited and consumed by get_target_file_name();
    # "spec" or a (glob) file path both work out of the box.
```

### 2. Define the Action

```python
class AppendFileAction(BaseAction):
    """Append `content` to the end of the target file(s)."""
    ENTRY_CLASS = AppendFileEntry

    def execute(self, package_path: Path):
        for entry in self.entries:
            # first=False → support glob targets matching several files
            for file_path in entry.get_target_file_name(package_path, first=False):
                logger.info(f"Appending to {file_path}: {entry}")
                data = read_file_data(file_path)
                new_lines = entry.content.splitlines()
                if not new_lines:
                    raise ActionNotAppliedError(
                        "AppendFileAction", "content is empty"
                    )
                data.extend(new_lines)
                write_file_data(file_path, data)
```

### 3. Register it in `ACTION_MAP`

```python
class ConfigReader:
    ACTION_MAP = {
        ...
        "add_line": AddLineAction,
        "append_file": AppendFileAction,   # ← new
    }
```

The YAML key (`append_file`) is exactly the `ACTION_MAP` key.

### 4. Use it in a config

```yaml
actions:
  - append_file:
    - target: "README.md"
      content: |
        This package was rebuilt by AlmaLinux Autopatch.
```

### 5. Document it

- Add an annotated block to [`conf_example.yaml`](../conf_example.yaml).
- Add a section to [configuration.md](configuration.md) and, if useful for
  config authors, to [`SKILL.md`](../SKILL.md).

### 6. Add a test

The suite in [`tests/test_actions.py`](../tests/test_actions.py) is fixture-driven
(see [Testing](#testing)). Add a fixture directory and an `expected/` tree, or a
targeted unit test for the new behavior.

## Conventions & gotchas

- **Fail loudly.** If an action expects to change something and doesn't, raise
  `ActionNotAppliedError`. Silent no-ops produce subtly wrong packages.
- **Respect spec semantics.** When editing a spec, stop at `%changelog` and skip
  comment lines where appropriate — reuse `process_lines`/`tools_rpm` rather than
  re-implementing.
- **Support globs where it makes sense.** Use
  `get_target_file_name(..., first=False)` and loop, like `ReplaceAction`.
- **Preserve indentation** when inserting/replacing multi-line content (see
  `_get_indent` / `_apply_indentation`).
- **Keep the container in sync.** The AI agent validates fixes with the same
  `autopatch_validate_config` / `autopatch` CLIs, so a new action automatically
  works there once it's in `actions_handler.py`. If you add new runtime files,
  update `agent/Containerfile`, `setup.py`, the `%files` list in
  `autopatch.spec`, and the `Makefile` tarball includes.
- **Use the shared logger** (`from tools.logger import logger`) — note the
  dual-import pattern (`autopatch.*` vs `*`) used throughout the codebase so the
  code runs both installed and from source.

## Testing

```bash
# install dev deps (pytest, freezegun, pyyaml, ...)
python -m pytest tests/ -v

# only the action engine
python -m pytest tests/test_actions.py -v
```

`tests/test_actions.py` discovers fixture cases under `tests/configs/<name>/`:

```
tests/configs/<name>/
├── <name>.spec              # input spec
├── autopatch/<name>.yaml    # the config to apply
├── autopatch/files/         # optional: files for add_files
└── expected/                # expected output tree (compared after applying)
```

For each case it copies the inputs into a results dir, runs `ConfigReader` +
`apply_actions`, and diffs the result against `expected/`. To add a case, create
those files; no code change is needed. Other suites:

| File | Covers |
|------|--------|
| `tests/test_parser.py` | config parsing/validation |
| `tests/test_git.py`, `tests/test_tools.py`, `tests/test_slack.py` | helpers |
| `tests/test_agent*.py` | AI recovery pipeline |

Run `autopatch_validate_config` on real configs as a fast sanity check before
running the full workflow.
