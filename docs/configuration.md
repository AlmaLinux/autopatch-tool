# Configuration Reference (`config.yaml`)

This is the complete reference for the Autopatch config file — the declarative
description of how a package's spec and sources should be modified. It is the
canonical, expanded version of [`conf_example.yaml`](../conf_example.yaml).

> Looking for a quick task-oriented cheat sheet with real-world patterns?
> See [`SKILL.md`](../SKILL.md). This document is the exhaustive reference.

## Where the config lives

In the `autopatch/<package>` repo, on the AlmaLinux branch (`a8`, `a9`, `a10s`, …):

```
<package>/
├── config.yaml       # required — the default config for this branch
├── config-*.yaml     # optional — additional configs (need custom_target_branch)
├── files/            # patches & source files referenced by add_files
└── scripts/          # shell scripts referenced by run_script
```

Autopatch processes **every** file in the package directory whose name starts
with `config` and ends with `.yaml` (see `get_config_files` in
[`debranding.py`](../src/debranding.py)). Any file other than `config.yaml` must
set `custom_target_branch` (see below), otherwise the run fails — this prevents
two configs from silently writing to the same branch.

## Top-level structure

A config has two top-level keys: an optional `parameters:` block and a required
`actions:` list.

```yaml
parameters:          # optional — global behavior switches
  insert_almalinux_line: true
  # ...

actions:             # required — ordered list of action blocks
  - <action_type>:
    - <entry>
    - <entry>
  - <action_type>:
    - <entry>
```

- `actions` is an **ordered list**. Actions execute top-to-bottom; ordering
  matters (see [Action ordering](#action-ordering)).
- Each action block is a single-key mapping (`replace:`, `add_files:`, …) whose
  value is a **list of entries**. Even a single entry must be a list item (`-`).

## `parameters` — global parameters

All parameters are optional. Defaults are taken from
[`GlobalParameters`](../src/actions_handler.py).

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `insert_almalinux_line` | bool | `true` | Whether `add_files` inserts the `# AlmaLinux Patch/Source` marker block and the `# Applying AlmaLinux …` apply line into the spec. Per-entry `insert_almalinux_line` in `add_files` overrides this. |
| `custom_target_branch` | str | `""` | Push the result to this branch instead of the auto-derived one. Also selects which branch a non-default `config-*.yaml` targets. |
| `pre_clean` | bool | `false` | Wipe the package working tree before merging the upstream branch. Use only when the package has file-type conflicts that block a normal merge. |
| `ignore_version_macros` | bool | `false` | Use the **raw** `Version:` from the spec for the changelog EVR instead of resolving macros via `rpmspec`. |
| `ignore_release_macros` | bool | `false` | Use the **raw** `Release:` for the changelog EVR instead of resolving macros. |
| `tag_prefix` | str | `""` | Prefix prepended to the git tag Autopatch creates. |
| `el_version` | str | auto (`"8"`) | Enterprise Linux major version used when resolving spec macros. Normally derived automatically from the branch name (`c9` → `9`); set it only to override.|

```yaml
parameters:
  insert_almalinux_line: true
  custom_target_branch: "a9-custom"
  pre_clean: false
  ignore_version_macros: false
  ignore_release_macros: false
  tag_prefix: "my-prefix-"
```

## Actions

There are eight action types. The table is followed by a detailed section for
each.

| Action | Purpose | Required keys |
|--------|---------|---------------|
| [`replace`](#replace) | Find & replace strings (literal or regex) | `target`, (`find` or `rfind`), `replace` |
| [`delete_line`](#delete_line) | Delete exact lines/blocks | `target`, `lines` |
| [`modify_release`](#modify_release) | Append a suffix to `Release:` | `suffix` |
| [`changelog_entry`](#changelog_entry) | Add a `%changelog` entry (and commit message) | `name`, `email`, `line` |
| [`add_files`](#add_files) | Add a patch or source file | `type`, `name` |
| [`delete_files`](#delete_files) | Remove a file (incl. lookaside metadata) | `file_name` |
| [`run_script`](#run_script) | Run a custom shell script | `script` |
| [`add_line`](#add_line) | Insert content into a spec section | `target`, `section`, `location`, `content` |

The special `target` value **`"spec"`** means "the package's `.spec` file";
Autopatch finds the single `*.spec` file automatically (and errors if there are
zero or more than one).

### `replace`

String replacement in the spec or any source file.

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `target` | str | — | `"spec"` or a file path. **Glob patterns are supported** (e.g. `"*.config"`, `"kernel*.config"`). |
| `find` | str | — | Literal string to search for. Mutually exclusive with `rfind`. Multi-line supported via `|`. |
| `rfind` | str | — | Regular expression to search for. Mutually exclusive with `find`. |
| `replace` | str | — | Replacement string. Multi-line supported via `|`. An empty value deletes the match. |
| `count` | int | `-1` | Number of replacements; `-1` = all occurrences. **Always set it explicitly** for predictability. |

```yaml
  - replace:
    - target: "spec"
      find: "Upstream Vendor Linux"      # the upstream distribution's product name
      replace: "AlmaLinux"
      count: 2
    - target: "*.config"
      find: "# CONFIG_FOO is not set"
      replace: "CONFIG_FOO=y"
      count: 1
    - target: "spec"
      rfind: "Requires:.*clang.*"
      replace: "Requires: clang = %{epoch}:%{version}-%{release}"
      count: 1
    - target: "spec"
      find: |
            %global vendor_name Upstream Vendor
            %global vendor_bug https://bugs.example.com/
      replace: |
            %global vendor_name AlmaLinux
            %global vendor_bug https://bugs.almalinux.org/
```

Notes:
- In a spec file, processing **stops at `%changelog`** — `replace` never touches
  the changelog.
- Comment lines (`#…`) in a spec are skipped unless your `find` itself is a
  comment.
- Multi-line `find`/`replace` is matched ignoring leading indentation; the
  original indentation of the matched block is preserved on the replacement.

### `delete_line`

Delete exact lines or multi-line blocks. **Does not support glob patterns** in
`target`.

| Field | Type | Description |
|-------|------|-------------|
| `target` | str | `"spec"` or a single file path. |
| `lines` | list | List of lines/blocks to delete. Each item may be multi-line (`|`). |

```yaml
  - delete_line:
    - target: "spec"
      lines:
        - "ExcludeArch: ppc64le"
        - |
          if [ "$KernelExtension" == "gz" ]; then
                gzip -f9 $SignImage
          fi
```

### `modify_release`

Append a suffix to the `Release:` tag. Prefer this over a `replace` on the
release line — it works regardless of the upstream release number and handles
`%autorelease`.

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `suffix` | str | — | Suffix appended to `Release:` (e.g. `.alma.1`). |
| `enabled` | bool | `true` | Set `false` to disable without removing the block. |
| `auto_increment` | bool | `false` | Treat the trailing number of `suffix` as a starting value and bump it automatically based on existing git tags. |

```yaml
  - modify_release:
    - suffix: ".alma.1"
      enabled: true
```

- Increment the number (`.alma.2`, `.alma.3`, …) when you make further changes to
  the same upstream version.
- If the spec uses `%autorelease`, the suffix is appended to the autorelease
  final-line template instead of the literal `Release:` value.
- The combined suffix from all enabled `modify_release` entries is also appended
  to the git tag.

#### `auto_increment`

With `auto_increment: true` you no longer bump the suffix number by hand. The
trailing number of `suffix` is used as a *starting* value, and on every run the
tool resolves the next iteration from the tags that already exist in the rpms
repository:

- It looks for tags of the form `<tag_prefix><base_tag><stem><N>` (e.g.
  `changed/a9/<NVR>.alma.2`) and picks the highest existing `N` plus one.
- If no such tag exists yet, the number configured in `suffix` is used as-is.
- When the upstream version changes, no matching tags exist for the new version,
  so the count effectively resets to the starting value.

The resolved suffix is applied to both the spec `Release:` line and the git tag,
keeping the two in sync. For the same upstream version `.alma.1` becomes
`.alma.2`, `.alma.3`, … across successive runs.

```yaml
  - modify_release:
    - suffix: ".alma.1"
      enabled: true
      auto_increment: true
```

> **Note:** when `auto_increment` is enabled, `suffix` **must end with a number**
> (e.g. `.alma.1`). Otherwise the configuration is rejected with a validation
> error, since there is no trailing number to increment.

### `changelog_entry`

Add a `%changelog` entry. The `line` items double as the **git commit messages**
for the run.

| Field | Type | Description |
|-------|------|-------------|
| `name` | str | Author name. |
| `email` | str | Author email. |
| `line` | list | One or more changelog/commit lines. |

```yaml
  - changelog_entry:
    - name: "Andrew Lukoshko"
      email: "alukoshko@almalinux.org"
      line:
        - "fix(nftables): batch ipset elements to avoid O(n^2) insertion cost"
        - "Resolves: almalinux/almalinux-deploy#186"
```

- The EVR (epoch-version-release) for the entry header is computed from the spec
  (resolving macros via `rpmspec`, unless `ignore_*_macros` is set).
- If the spec uses `%autochangelog`, no literal entry is inserted; instead the
  first line is prefixed with `AlmaLinux changes:`.
- Long lines are wrapped at 80 columns.
- **Always include a `changelog_entry`** — it drives both the spec changelog and
  the commit message.

### `add_files`

Add a patch or source file to the package. The file **must exist in the config
repo's `files/` directory**. By default the spec is updated with a
`PatchNNN:`/`SourceNNN:` line (and, for patches, an apply directive).

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `type` | str | — | `"patch"` or `"source"`. |
| `name` | str | — | File name; must exist under `files/`. |
| `number` | int or `"Latest"` | `"Latest"` | Patch/Source number, or `"Latest"` to auto-assign the next free number. |
| `modify_spec` | bool | `true` | If `false`, only copy the file; don't edit the spec (use when you reference it manually via `replace`/`add_line`). |
| `insert_almalinux_line` | bool | inherits global | Insert the `# AlmaLinux …` marker / apply line. Overrides the global `insert_almalinux_line`. |
| `no_backup` | bool | `false` | For patches: omit the `-b .<stem>` backup suffix on the apply line. No effect for sources. |

```yaml
  - add_files:
    - type: "patch"
      name: "1000-fix-something.patch"
      number: 1000
    - type: "source"
      name: "almalinux.pem"
      number: 9000
    - type: "source"
      name: "extra-cert.cer"
      modify_spec: false        # copy only; spec untouched
```

Conventional numbering:

| Range | Use |
|-------|-----|
| `1000+` | AlmaLinux-specific patches |
| `2000+` | driver / hardware-enablement patches |
| `9000+` | source files (certs, keys) |

Autopatch detects the patch-apply style used by the spec (classic `%patchN`,
`%patch -P N`, kernel `ApplyPatch`, `%autosetup`, or a `*.patches` file) and
inserts the new directive in the matching style and location. If the package
uses a `SPECS/` + `SOURCES/` layout, added files land in `SOURCES/`.

### `delete_files`

Remove a file from the package. If the file is tracked in dist-git lookaside
metadata (`.<pkg>.metadata` or `sources`), the corresponding hash line is removed
too.

| Field | Type | Description |
|-------|------|-------------|
| `file_name` | str | Name of the file to delete (searched within the package). |

```yaml
  - delete_files:
    - file_name: "old-cert.cer"
    - file_name: "obsolete.patch"
```

### `run_script`

Run a custom shell script for preparation work the other actions can't express
(e.g. creating symlinks, generating files). The script must live in the config
repo's `scripts/` directory.

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `script` | str | — | Script file name under `scripts/`. |
| `cwd` | str | `"rpms"` | Working directory: `"rpms"` (the package/dist-git tree) or `"autopatch"` (the config repo). |

```yaml
  - run_script:
    - script: "custom_script.sh"
      cwd: "rpms"
```

The script is run with `bash`; a non-zero exit fails the run.

### `add_line`

Insert content into a specific spec section.

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `target` | str | — | Must be `"spec"`. |
| `section` | str | — | Section name: `global`, `description`, `prep`, `build`, `install`, `check`, `files`, `post`, … |
| `location` | str | — | `"top"` or `"bottom"` of the section. |
| `content` | str | — | Content to insert (multi-line via `|`). |
| `subpackage` | str | main package | Target a specific subpackage's section instead of the main package. |

```yaml
  - add_line:
    - target: "spec"
      section: "install"
      location: "bottom"
      content: |
              # Customized SOURCE550 installation
              install -p -m 0644 %{SOURCE550} %{buildroot}%{_sysconfdir}/yum.repos.d/
```

- `global` is the implicit pre-`%description` preamble section.
- For sections that can be tied to a subpackage (`%files`, `%description`,
  `%pre`, `%post`, …), `subpackage` selects the right one (both `%package foo`
  and `%package -n foo` forms are understood).

## Action ordering

Because actions run in declaration order, put **mutating-the-existing-spec**
actions before actions that **add new lines**:

1. `replace`, `delete_line` — edit the upstream spec while its content is still
   in the original form your `find` strings expect.
2. `add_files`, `add_line` — append AlmaLinux additions.
3. `modify_release`, `changelog_entry` — bookkeeping (order between these two
   doesn't matter; the changelog reads the already-suffixed release).

A common, safe template:

```yaml
actions:
  - replace: [ ... ]          # debrand / fix existing content
  - delete_line: [ ... ]      # remove unwanted lines
  - add_files: [ ... ]        # add patches / sources
  - add_line: [ ... ]         # add spec section content
  - modify_release:
    - suffix: ".alma.1"
  - changelog_entry:
    - name: "..."
      email: "..."
      line: [ "..." ]
```

## Common patterns

### Patch-only (most common)

```yaml
actions:
  - modify_release:
    - suffix: ".alma.1"
      enabled: true
  - changelog_entry:
    - name: "Author Name"
      email: "user@almalinux.org"
      line:
        - "Description of the fix"
  - add_files:
    - type: "patch"
      name: "1000-fix-description.patch"
      number: 1000
```

### Debranding

```yaml
actions:
  - replace:
    - target: "spec"
      find: "Upstream Vendor Linux"        # the upstream distribution's product name
      replace: "AlmaLinux"
    - target: "spec"
      find: "https://bugs.example.com/"    # the upstream bug tracker URL
      replace: "https://bugs.almalinux.org/"
      count: 1
  - modify_release:
    - suffix: ".alma.1"
      enabled: true
  - changelog_entry:
    - name: "Eduard Abdullin"
      email: "eabdullin@almalinux.org"
      line:
        - "Debrand for AlmaLinux"
```

### Secure boot / signing certificates

```yaml
actions:
  - replace:
    - target: "spec"
      find: |
            Source10: upstreamsecurebootca3.cer
            Source11: upstreamsecurebootca2.cer
      replace: |
            Source10: almalinuxsecurebootca0.cer
            Source11: almalinuxsecureboot0.cer
      count: 1
  - add_files:
    - type: "source"
      name: "almalinuxsecurebootca0.cer"
      modify_spec: false
    - type: "source"
      name: "almalinuxsecureboot0.cer"
      modify_spec: false
```

## Validate before you commit

```bash
autopatch_validate_config path/to/config.yaml
# or, from a source checkout:
python validate_config.py path/to/config.yaml
```

This parses and validates the config (keys, types, required fields, mutual
exclusivity of `find`/`rfind`, etc.) without touching any repo.

## Authoring tips

- **Prefer `modify_release` over `replace`** for the release suffix.
- **Set `count` explicitly** on `replace` to avoid surprising over-replacement.
- **Multi-line `find` must match the spec exactly**, including indentation of the
  first line's interior — Autopatch matches ignoring leading whitespace but
  preserves it on output.
- When generating a patch against a tree that already has earlier patches
  applied, verify it applies with `patch --fuzz=0` (since `%autosetup` uses
  `--fuzz=0`).
- An action that matches nothing raises `ActionNotAppliedError` and fails the
  run — this is intentional. If upstream changed and your `find` no longer
  matches, update the config (or let the AI agent propose a fix).
