# AlmaLinux Autopatch Tool

Autopatch automates the modifications AlmaLinux applies to
source packages before rebuilding them: **debranding, AlmaLinux-specific patches,
and release/changelog bookkeeping**. Instead of editing spec files by hand on
every upstream update, each package's modifications are described once in a
declarative `config.yaml` and applied automatically.

```
upstream push (c9)  ──►  webhook  ──►  apply config.yaml  ──►  commit + tag + push (a9)
```

## Why it exists

AlmaLinux is a downstream rebuild. Every upstream package needs the same kinds of
mechanical changes — replace the upstream vendor's name, swap certificates, add
patches, bump the release, write a changelog entry — repeated across hundreds of
packages on every update. Autopatch turns those changes into version-controlled
data and runs them automatically, verifiably, and reproducibly.

## How it works (in brief)

Autopatch operates on two git repos per package on `git.almalinux.org`:

- **`autopatch/<pkg>`** — human-authored config repo: `config.yaml` + `files/` +
  `scripts/`. Branches are AlmaLinux branches (`a8`, `a9`, `a10s`, …).
- **`rpms/<pkg>`** — dist-git: the actual spec file + sources. Holds upstream
  imports (`c8`, `c9`, …) and the AlmaLinux results (`a8`, `a9`, …).

On each upstream update, Autopatch:

1. maps the upstream branch to the config branch (`c9` → `a9`);
2. resets the AlmaLinux branch to the fresh upstream import;
3. applies the package's `config.yaml` (an ordered list of *actions*);
4. commits (changelog lines become commit messages), tags, pushes, and notarizes.

If a run fails because upstream changed, an optional AI recovery agent can analyze
the failure and propose a fix as a pull request.

## Quick start

Validate a config:

```bash
autopatch_validate_config path/to/config.yaml
# from a source checkout:
python validate_config.py path/to/config.yaml
```

Apply a config to a local package checkout (no git):

```bash
autopatch_package_patching --config config.yaml --targetdir ./mypackage
```

Run the full debranding workflow for a package (needs git/SSH access):

```bash
autopatch -p <package> -b c9
```

A minimal `config.yaml` (add one patch, bump release, write changelog):

```yaml
actions:
  - modify_release:
    - suffix: ".alma.1"
      enabled: true
  - changelog_entry:
    - name: "Author Name"
      email: "user@almalinux.org"
      line:
        - "Add fix for ..."
  - add_files:
    - type: "patch"
      name: "1000-fix-description.patch"
      number: 1000
```

## Documentation

| Document | What's inside |
|----------|---------------|
| [docs/configuration.md](docs/configuration.md) | Complete `config.yaml` reference: the `parameters` block and all eight action types, with fields, examples, ordering rules, and common patterns. |
| [docs/writing-actions.md](docs/writing-actions.md) | Developer guide: how the action engine works and how to add a new action type, with a worked example and testing instructions. |
| [docs/deployment.md](docs/deployment.md) | CLI tools, the webhook service, runtime environment variables, Ansible deployment, the AI agent container, and RPM packaging. |
| [SKILL.md](SKILL.md) | Task-oriented cheat sheet for config authors (real-world debranding/patching patterns). |
| [conf_example.yaml](conf_example.yaml) | Annotated example config. |
| [agent/README.md](agent/README.md) | Design of the AI recovery agent (container, orchestrator, data flow). |

## Repository layout

```
autopatch-tool/
├── src/                       # core library + web service + agent host side
│   ├── actions_handler.py     #   config parser + action engine (the core)
│   ├── debranding.py          #   end-to-end orchestration
│   ├── webserv.py             #   Flask webhook server
│   └── tools/                 #   rpm, git, branch, slack, helpers
├── agent/                     # AI recovery container (Claude Code)
├── ansible/                   # deployment role
├── tests/                     # pytest suite + fixture configs
├── autopatch_standalone.py    # CLI  -> `autopatch`
├── package_patching.py        # CLI  -> `autopatch_package_patching`
├── validate_config.py         # CLI  -> `autopatch_validate_config`
├── autopatch.spec, Makefile   # RPM packaging
└── conf_example.yaml          # annotated config example
```

## Development

```bash
python -m pytest tests/ -v          # run the test suite
python -m pytest tests/test_actions.py -v   # just the action engine
```

See [docs/writing-actions.md](docs/writing-actions.md) for how to extend the
engine and add fixture-based tests.

## License

GPLv3+. See [LICENSE](LICENSE).
```
