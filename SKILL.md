---
name: almalinux-autopatch
description: Create and maintain AlmaLinux autopatch configs for RPM packages. Use when working in autopatch/ repos, creating config.yaml for package debranding, adding patches, modifying spec files, or when the user mentions autopatch, debranding, or AlmaLinux package customization.
---

# AlmaLinux Autopatch

Autopatch automates modifications to upstream Enterprise Linux source packages for AlmaLinux rebuilds. Each package gets a git repo under the [autopatch](https://git.almalinux.org/autopatch) namespace with a `config.yaml` that declares spec changes, patches, and branding. The corresponding RPM dist-git sources live under [rpms](https://git.almalinux.org/rpms/).

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

Appends a suffix to the RPM Release tag. Preferred over `replace` for release changes -- works regardless of upstream release number.

```yaml
  - modify_release:
    - suffix: ".alma.1"
      enabled: true
```

Increment the number (`.alma.2`, `.alma.3`) when making additional changes to the same upstream version.

Set `auto_increment: true` to bump the trailing number automatically instead of editing the config by hand. The next iteration is derived from the git tags already present in the rpms repo (`changed/<branch>/<NVR>.alma.<N>`): the suffix becomes the highest existing `N` plus one, falling back to the number written in `suffix` when none exists. The count resets automatically when the upstream version changes (a different tag base). The trailing number in `suffix` must be present and acts as the starting value.

```yaml
  - modify_release:
    - suffix: ".alma.1"   # trailing number is the starting value
      auto_increment: true
```

### replace

String replacement in spec or source files. Supports glob patterns in `target`. Use `find` for literal strings, `rfind` for regex.

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
```

- `count`: number of replacements (-1 = all, default). Always set explicitly.
- Multi-line values use YAML `|` block scalar with indentation.

### changelog_entry

Adds a `%changelog` entry and uses the lines as git commit messages.

```yaml
  - changelog_entry:
    - name: "Andrew Lukoshko"
      email: "alukoshko@almalinux.org"
      line:
        - "fix(nftables): batch ipset elements to avoid O(n^2) insertion cost"
        - "Resolves: almalinux/almalinux-deploy#186"
```

### add_files

Adds patches or source files. Files must exist in `files/` directory. Automatically adds `PatchNNN:` or `SourceNNN:` to the spec.

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
      modify_spec: false          # add file without touching spec
```

- `number`: integer or `"Latest"` (auto-assigns next available number)
- `modify_spec`: boolean, default true. Set false for files referenced manually via `replace`.
- `insert_almalinux_line`: boolean, default true.

Patch numbering convention:
- `1000+` for AlmaLinux-specific patches
- `2000+` for driver/hardware patches (e.g. kernel PCI IDs)
- `9000+` for source files (certs, keys)

### delete_line

Removes exact lines from a file. Does not support glob patterns.

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
      section: "install"        # global, description, build, install, files, etc.
      location: "bottom"        # top or bottom
      content: |
              install -p -m 0644 %{SOURCE550} %{buildroot}%{_sysconfdir}/yum.repos.d/
```

Optional `subpackage:` targets a specific subpackage instead of main.

### run_script

Executes a custom script from `scripts/` directory.

```yaml
  - run_script:
    - script: "custom_script.sh"
      cwd: "rpms"               # "rpms" (default) or "autopatch"
```

## Common Patterns

### Minimal: patch-only package

Most common pattern -- add a single fix with release bump.

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

### Debranding package

Replace upstream vendor references with AlmaLinux throughout the spec.

```yaml
actions:
  - replace:
    - target: "spec"
      find: "Upstream Vendor Linux"      # the upstream distribution's product name
      replace: "AlmaLinux"
    - target: "spec"
      find: "https://bugs.example.com/"  # the upstream bug tracker URL
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

### Secure boot / signing

Replace upstream certificates and signing references.

```yaml
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

### Architecture enablement (RISC-V)

Add RISC-V support by adjusting arch lists and adding patches.

```yaml
  - replace:
    - target: "spec"
      find: "ExclusiveArch:  %{java_arches}"
      replace: "ExclusiveArch:  %{java_arches} riscv64"
      count: 1

  - add_files:
    - type: "patch"
      name: "1001-Add-support-for-riscv64.patch"
      number: 1001
```

## Workflow: Creating a New Autopatch Config

1. **Clone/init the autopatch repo** for the package on the correct branch (`a8`, `a9`, `a10s`, etc.)
2. **Identify changes needed** by diffing the AlmaLinux dist-git branch against the upstream import. Upstream branches map to AlmaLinux branches as follows:

   | Upstream | AlmaLinux |
   |---|---|
   | `c8` | `a8` |
   | `c9` | `a9` |
   | `c10` | `a10` |
   | `c10s` | `a10s` |

   For example, to see what AlmaLinux changed in a package for EL8:
   ```
   git log c8..a8 --oneline
   ```
3. **Create `config.yaml`** using the action types above
4. **Place patch/source files** in `files/` directory
5. **Use `modify_release`** (not `replace`) for the release suffix
6. **Always include `changelog_entry`** -- it drives both the spec changelog and git commit messages
7. **Commit and push** to the matching branch

## Important Notes

- Action order matters: `replace` and `delete_line` run before `add_files` adds new spec lines.
- The `spec` target keyword refers to the package's spec file (autopatch resolves the actual filename).
- Glob patterns (e.g. `"kernel*.config"`) work in `replace` target but not in `delete_line`.
- Multi-line `find`/`replace` values must preserve exact indentation from the original file.
- When a patch is generated against a tree with earlier patches applied, verify context lines match post-patch state (use `patch --fuzz=0` to test, since `%autosetup` uses `--fuzz=0`).
