## Deployment Guide

#### Prerequisites

Before deploying, ensure the following dependencies and configurations are met:

- Ansible installed on the control node.
- SSH access to the target server.
- Required credentials stored securely in `ansible/roles/deploy/vars/main.yml`.
- Ansible inventory file (`inventory.ini`) with the target server IP and SSH key.

#### Deployment Steps

##### 1. Define Required Variables

Ensure the following variables are set in `ansible/roles/deploy/vars/main.yml`:

```yaml
---
# CAS credentials for notarization
deploy_cas_signer_id: "your_signer_id"
deploy_cas_api_key: "your_api_key"
deploy_immudb_username: "your_username"
deploy_immudb_password: "your_password"
deploy_immudb_database: "your_database"
deploy_immudb_address: "your_immudb_address"

# Slack credentials to send notifications
deploy_slack_token: "your_slack_token"

# Git authentication key
deploy_auth_key: "your_git_auth_key"

# SSH keys for git.almalinux.org
deploy_ssh_private_key: "your_private_key"
deploy_ssh_public_key: "your_public_key"
```

##### 2. Configure Ansible Inventory

Define the target hosts in your Ansible inventory file (e.g., `inventory.ini`):

```ini
[deploy_servers]
your-server-ip ansible_user=your_user ansible_ssh_private_key_file=your_key
```

##### 3. Running the Deployment

Execute the deployment playbook with:

```bash
ansible-playbook -i inventory.ini main.yml
```

##### 4. Verification

After deployment, verify that the service is running properly:

```bash
systemctl status almalinux-autopatch.service
```


## Configuration File Format

#### 1. actions (Main Block)

##### 1.1 replace – String Replacement

- **Description**: Replaces a specified strings with anothers.
- **Fields**:
  - `target`: Path to the file or “spec” (indicates the spec file). Glob patterns are supported.
  - `find`: String to search for (supports multi-lines, mutually exclusive to `rfind`).
  - `rfind`: regex string to search for (supports multi-lines, mutually exclusive to `find`).
  - `replace`: String to replace with (supports multi-lines).
  - `count`: Number of replacements (default is -1, which replaces all occurrences).

**Example**:
```yaml
  - replace:
    - target: "*.conf"
      find: "RHEL"
      replace: "AlmaLinux"
      count: 1
    - target: "spec"
      find: |
            %if 0%{?rhel}
            RHEL
      replace: |
            %if 0%{?almalinux}
            AlmaLinux
    - target: "spec"
      rfind: "Requires:.*clang.*"
      replace: "Requires: clang = %{epoch}:%{version}-%{release}"
      count: 1
```

##### 1.2 delete_line – Line Deletion

- **Description**: Deletes specified lines.
- **Fields**:
  - `target`: Path to the file or “spec”. Does not support glob patterns.
  - `lines`:  List of lines to delete (supports multi-lines).

**Example**:
```yaml
  - delete_line:
    - target: "README.md"
      lines:
        - "line1"
        - |
            hello world
            additional line
```

##### 1.3 modify_release – Release Number Modification

- **Description**: Adds a suffix to the release number.
- **Fields**:
  - `suffix`: Suffix to append to the release number.
  - `enabled`: Enables or disables the modification (default is true).

**Example**:
```yaml
  - modify_release:
    - suffix: ".mycustom.1"
      enabled: true
```

##### 1.4 changelog_entry – Adding Changelog Entries

- **Description**: Adds entries to the changelog.
- **Fields**:
  - `name`: Author’s name.
  - `email`: Author’s email.
  - `line`: Lines to add to the changelog (also used as commit messages).

**Example**:
```yaml
  - changelog_entry:
    - name: "eabdullin"
      email: "eabdullin@almalinux.org"
      line:
        - "Updated branding to AlmaLinux"
        - "Fixed a typo in the README"
```

##### 1.5 add_files – Adding Files

- **Description**: Adds source files or patches.
- **Fields**:
  - `type`: File type (patch or source).
  - `name`: File name. Should be placed in the `files` directory of the autopatch namespace repository.
  - `number`: Patch/file number or “Latest” (default is “Latest”).

**Example**:
```yaml
  - add_files:
    - type: "patch"
      name: "my_patch.patch"
      number: "Latest"
    - type: "source"
      name: "additional_source.tar.gz"
      number: 1000
```

##### 1.6 delete_files – Deleting Files

- **Description**: Deletes files from the repository.
- **Fields**:
  - `file_name`: File name to delete.

**Example**:
```yaml
    - delete_files:
      - file_name: "file1.txt"
      - file_name: "file2"
```

##### 1.7. run_custom_scripts - Running Custom Scripts

- **Description**: Executes user-defined scripts to prepare the package before performing other actions (e.g., creating symbolic links).
- **Fields**: 
  - `script`: script name. Should be placed in the `scripts` directory of autopatch namespace repository
  - `cwd`: "rpms" or "autopatch" ('rpms' by default).

**Example**:
```yaml
- run_script:
    - script: "custom_script.sh"
      cwd: "rpms"

```

##### 1.8 add_line – Add a line

- **Description**: Adds a line to a section within the spec file.
- **Fields**:
  - `target`: Path to the “spec” (indicates the spec file).
  - `section`: Spec file section to target (global, description, build, install, files, etc).
  - `subpackage`: Optional name of the subpackage to target. If not set, target the main package.
  - `location`: Location to add content ('top' or 'bottom') to the section.
  - `content`: Actual content to add (supports multi-lines).

**Example**:
```yaml
  - add_line:
    - target: "spec"
      section: "install"
      location: "bottom"
      content: |
              # Customized SOURCE550 installation
              install -p -m 0644 %{SOURCE550} %{buildroot}%{_sysconfdir}/yum.repos.d/
```
