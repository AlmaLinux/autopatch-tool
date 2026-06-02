# AlmaLinux Autopatch Config Format

Autopatch automates modifications to CentOS/RHEL source packages for AlmaLinux rebuilds. Each package gets a git repo under the `autopatch` namespace with a `config.yaml` that declares spec changes, patches, and branding. The corresponding RPM dist-git sources live under `rpms`.

## Repository Layout

```
<package>/
├── config.yaml       # Required - declares all modifications
├── files/            # Patches, sources, certs referenced by add_files
└── scripts/          # Optional - custom scripts for run_script action
```

Branch names follow AlmaLinux convention: `a8`, `a9`, `a10`, `a10s` (stream), `a10-beta`.

## config.yaml Structure

Top-level key is `actions:`, containing an ordered list of action blocks. Actions execute in order.

```yaml
actions:
  - <action_type>:
      ...
```

## Action Reference

### modify_release

Appends a suffix to the RPM Release tag. Preferred over `replace` for release changes.

```yaml
  - modify_release:
    - suffix: ".alma.1"
      enabled: true
```

Set `auto_increment: true` to bump the trailing number automatically from existing git tags (`changed/<branch>/<NVR>.alma.<N>`) instead of editing the config by hand. The suffix becomes the highest existing `N` plus one (falling back to the configured number when none exists), and resets when the upstream version changes. The trailing number must be present and is the starting value.

```yaml
  - modify_release:
    - suffix: ".alma.1"
      auto_increment: true
```

### replace

String replacement in spec or source files. Supports glob patterns in `target`. Use `find` for literal strings, `rfind` for regex.

```yaml
  - replace:
    - target: "spec"
      find: "Red Hat Enterprise Linux"
      replace: "AlmaLinux"
      count: 2
    - target: "spec"
      rfind: "Requires:.*clang.*"
      replace: "Requires: clang = %{epoch}:%{version}-%{release}"
      count: 1
```

- `count`: number of replacements (-1 = all, default). Always set explicitly.
- Multi-line values use YAML `|` block scalar with indentation.

### changelog_entry

Adds a `%changelog` entry and uses the lines as git commit messages.

```yaml
  - changelog_entry:
    - name: "Author Name"
      email: "user@almalinux.org"
      line:
        - "Description of the change"
```

### add_files

Adds patches or source files. Files must exist in `files/` directory.

```yaml
  - add_files:
    - type: "patch"
      name: "1000-fix-something.patch"
      number: 1000
    - type: "source"
      name: "almalinux.pem"
      number: 9000
      modify_spec: false
```

- `number`: integer or `"Latest"` (auto-assigns next available number)
- `modify_spec`: boolean, default true
- Patch numbering: `1000+` for AlmaLinux-specific, `2000+` for driver patches, `9000+` for source files

### delete_line

Removes exact lines from a file.

```yaml
  - delete_line:
    - target: "spec"
      lines:
        - "ExcludeArch: ppc64le"
```

### delete_files

Removes files from the package repo.

```yaml
  - delete_files:
    - file_name: "old-cert.cer"
```

### add_line

Inserts content into a specific spec section.

```yaml
  - add_line:
    - target: "spec"
      section: "install"
      location: "bottom"
      content: |
              install -p -m 0644 %{SOURCE550} %{buildroot}%{_sysconfdir}/yum.repos.d/
```

### run_script

Executes a custom script from `scripts/` directory.

```yaml
  - run_script:
    - script: "custom_script.sh"
      cwd: "rpms"
```

## Important Notes

- Action order matters: `replace` and `delete_line` run before `add_files` adds new spec lines.
- The `spec` target keyword refers to the package's spec file (autopatch resolves the actual filename).
- Glob patterns work in `replace` target but not in `delete_line`.
- Multi-line `find`/`replace` values must preserve exact indentation from the original file.
