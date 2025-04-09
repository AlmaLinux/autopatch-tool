import yaml
from pathlib import Path
import datetime
import textwrap
import shutil
import re

from tools.logger import logger
from tools.tools import run_command
import tools.rpm

class ActionNotAppliedError(Exception):
    """
    Raised when the action verification fails, indicating that the expected changes were not applied.
    """
    def __init__(self, action_name: str, reason: str = "Verification failed"):
        self.action_name = action_name
        self.reason = reason
        super().__init__(f"Action '{action_name}' was not applied successfully: {reason}")


def read_file_data(path_to_file: Path) -> list[str]:
    logger.debug(f"Reading file: {path_to_file}")
    with open(path_to_file, "r") as f:
        info = [line.rstrip("\n") for line in f.readlines()]
        
    if info is None or not info:
        raise ValueError("File is empty")
    return info

def write_file_data(path_to_file: Path, data: list[str]):
    logger.debug(f"Writing file: {path_to_file}")
    with open(path_to_file, "w") as f:
        f.writelines(f"{line}\n" for line in data)


def process_lines(file_path: Path, target: str, find_lines:list[str], replace_lines:list[str], entry_count:int):
    counter = 0
    i = 0
    file = read_file_data(file_path)

    change_made = False

    while i < len(file):
        if target == "spec":
            # if tools.rpm.is_spec_comment(file[i]):
            #     i += 1
            #     continue
            if tools.rpm.is_changelog(file[i]):
                break

        if len(find_lines) == 1:
            # Skip comments in spec file only with target as spec and find_lines as single line
            if target == "spec":
                if tools.rpm.is_spec_comment(file[i]) and not tools.rpm.is_spec_comment(find_lines[0]):
                    i += 1
                    continue
            line = file[i]
            count_in_line = line.count(find_lines[0])
            if count_in_line > 0:
                for _ in range(count_in_line):
                    if entry_count != -1 and counter >= entry_count:
                        break
                    if not replace_lines and line.strip() == find_lines[0]:
                        del file[i]
                        change_made = True
                        logger.debug(f"Deleted line '{find_lines[0]}' at line {i+1}")
                        i -= 1 
                        break
                    else:
                        file[i] = file[i].replace(find_lines[0], "\n".join(replace_lines) if replace_lines else "", 1)
                        change_made = True
                        logger.debug(f"Replaced '{find_lines[0]}' with '{replace_lines}' in line {i+1}")
                    counter += 1
        else:
            stripped_block = [line.lstrip() for line in file[i:i + len(find_lines)]]
            stripped_find_lines = [line.lstrip() for line in find_lines]

            if stripped_block == stripped_find_lines:
                if entry_count != -1 and counter >= entry_count:
                    break
                
                if not replace_lines:
                    del file[i:i + len(find_lines)]
                    change_made = True
                    logger.debug(f"Deleted block of lines {i+1}-{i+len(find_lines)}.")
                    i -= len(find_lines)
                else:
                    formatted_replace_lines = [
                        file[i][:len(file[i]) - len(file[i].lstrip())] + line
                        for line in replace_lines
                    ]
                    file[i:i + len(find_lines)] = formatted_replace_lines
                    change_made = True
                    logger.debug(f"Replaced lines {i+1}-{i+len(find_lines)} with {replace_lines}.")
                counter += 1
                i += len(replace_lines) - 1
        i += 1

    if not replace_lines and not change_made:
        raise ActionNotAppliedError("DeleteAction", f"No changes made for '{find_lines}' in {file_path}")
    elif not change_made:
        raise ActionNotAppliedError("ReplaceAction", f"No changes made for '{find_lines}' in {file_path}")

    write_file_data(file_path, file)


# Base Entry class
class BaseEntry:
    ALLOWED_KEYS = {}
    REQUIRED_KEYS = set()

    def __init__(self, **kwargs):
        self._validate_keys(kwargs)
        self._initialize_attributes(kwargs)

    def _validate_keys(self, kwargs):
        missing_keys = self.REQUIRED_KEYS - set(kwargs.keys())
        extra_keys = set(kwargs.keys()) - set(self.ALLOWED_KEYS.keys())

        if extra_keys:
            raise ValueError(f"Unexpected keys: {', '.join(extra_keys)}. Allowed keys: {', '.join(self.ALLOWED_KEYS.keys())}")

        if missing_keys:
            raise ValueError(f"Missing required keys: {', '.join(missing_keys)}")

        for key, expected_type in self.ALLOWED_KEYS.items():
            actual_value = kwargs.get(key)
            if actual_value is not None:
                # Check if expected_type is a tuple (multiple types) or a single type
                if not isinstance(actual_value, expected_type if isinstance(expected_type, tuple) else (expected_type,)):
                    expected_type_names = (
                        ', '.join(t.__name__ for t in expected_type) if isinstance(expected_type, tuple) else expected_type.__name__
                    )
                    raise TypeError(
                        f"Invalid type for '{key}': expected {expected_type_names}, got {type(actual_value).__name__}"
                    )
        for key in self.REQUIRED_KEYS:
            actual_value = kwargs.get(key)
            if not isinstance(actual_value, bool):
                if not actual_value:
                    raise ValueError(f"Value for '{key}' cannot be empty.")


    def _initialize_attributes(self, kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)

    def __repr__(self):
        attributes = ', '.join(f"{key}={getattr(self, key)}" for key in self.ALLOWED_KEYS)
        return f"{self.__class__.__name__}({attributes})"

    def get_file_name(self, package_path: Path, file_name: str, first: bool = True):
        files = list()

        for f in Path(package_path).rglob(file_name):
            try:
                index = f.parts.index(package_path.name)
                if len(f.parts) > index + 1 and f.parts[index + 1] == "tests":
                    continue
            except ValueError:
                pass
            
            files.append(f)

        if not files:
            raise FileNotFoundError(f"File '{file_name}' not found in '{package_path}'")

        return files[0] if first else files

    def get_target_file_name(self, package_path: Path, first: bool = True):
        if 'spec' == self.target:
            spec_files = self.get_file_name(package_path, "*.spec", first=False)
            if len(spec_files) > 1:
                raise Exception(f"More than one .spec file present in {package_path}")
            if len(spec_files) == 0:
                raise Exception(f"No .spec file present in {package_path}")
            return spec_files[0] if first else spec_files
        return self.get_file_name(package_path, self.target, first)


# Base Action class
class BaseAction:
    ENTRY_CLASS = None

    def __init__(self, data, config_source: Path = None):
        self.entries = self._create_entries(data)
        self.config_source = config_source

    def _create_entries(self, data):
        entries = []
        for entry_data in data if isinstance(data, list) else [data]:
            if not isinstance(entry_data, dict):
                raise ValueError(f"Invalid format: expected a dictionary, got {type(entry_data).__name__}")
            logger.debug(f"Processing entry data: {entry_data}")
            entry = self.ENTRY_CLASS(**entry_data)
            entries.append(entry)
        return entries

    def execute(self, package_path: Path):
        raise NotImplementedError("Subclasses must implement the execute method.")


# Actions and Entries
class DeleteFilesEntry(BaseEntry):
    ALLOWED_KEYS = {
        "file_name": str
    }
    REQUIRED_KEYS = {"file_name"}

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.target = self.file_name

class DeleteFilesAction(BaseAction):
    ENTRY_CLASS = DeleteFilesEntry

    def _find_metadata_source_file(self, package_path: Path):
        for filename in [f".{package_path.name}.metadata", "sources"]:
            metadata_file = package_path / filename
            logger.debug(f"Checking metadata file: {metadata_file}")
            if metadata_file.exists() and metadata_file.is_file():
                return metadata_file
        raise ActionNotAppliedError("DeleteFilesAction", "Metadata file not found")

    def _delete_file_from_source_file(self, file_name: str, package_path: Path):
        metadata_file = self._find_metadata_source_file(package_path)
        metadata = read_file_data(metadata_file)

        for i, line in enumerate(metadata):
            # example of line: SHA512 (fwupd-1.9.26.tar.xz) = 04684f0be26c1daec9966e62c7db103cce923bb361657c66111e085e9a388e812250ac18774ef83eac672852489acc2ab21b9d7c94a28a8e5564e8bb7d67c0ba
            if re.match(rf"SHA512 \({file_name}\)", line):
                del metadata[i]
                break
            # example if line: b2620c36bd23ca699567fd4e4add039ee4375247 SOURCES/DBXUpdate-20100307-x64.cab
            elif re.match(rf"[0-9a-f]{{40}} {file_name}", line):
                del metadata[i]
                break
        write_file_data(metadata_file, metadata)

    def _delete_files(self, entry: DeleteFilesEntry, package_path: Path):
        try:
            file_path = entry.get_target_file_name(package_path, first=True)
            if file_path.exists():
                file_path.unlink()
                logger.debug(f"Deleted file: {file_path}")
        except FileNotFoundError:
            if self._find_metadata_source_file(package_path):
                self._delete_file_from_source_file(entry.file_name, package_path)
                logger.debug(f"Deleted file from metadata: {entry.file_name}")
            else:
                raise ActionNotAppliedError("DeleteFilesAction", f"File not found: {file_path}")

    def execute(self, package_path: Path):
        for entry in self.entries:
            self._delete_files(entry, package_path)


class ReplaceEntry(BaseEntry):
    ALLOWED_KEYS = {
        "target": str,
        "find": str,
        "replace": str,
        "count": int,
    }
    REQUIRED_KEYS = {"target", "find", "replace"}

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.count = kwargs.get("count", -1)

class ReplaceAction(BaseAction):
    ENTRY_CLASS = ReplaceEntry

    def execute(self, package_path: Path):
        for entry in self.entries:
            file_paths = entry.get_target_file_name(package_path, first=False)
            find_lines = entry.find.splitlines() if "\n" in entry.find else [entry.find]
            replace_lines = entry.replace.splitlines() if "\n" in entry.replace else [entry.replace]

            for file_path in file_paths:
                logger.info(f"Applying: {entry} to {file_path}")
                process_lines(file_path, entry.target, find_lines, replace_lines, entry.count)


class ModifyReleaseEntry(BaseEntry):
    ALLOWED_KEYS = {
        "suffix": str,
        "enabled": bool,
    }
    REQUIRED_KEYS = {"suffix"}

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.enabled = kwargs.get("enabled", True)
        self.target = "spec"

class ModifyReleaseAction(BaseAction):
    ENTRY_CLASS = ModifyReleaseEntry

    def execute(self, package_path: Path):
        for entry in self.entries:
            if not entry.enabled:
                logger.info("ModifyRelease action is disabled")
                return
            logger.info(f"Modifying release: {entry}")

            file_path = entry.get_target_file_name(package_path)
            file = read_file_data(file_path)

            for i, line in enumerate(file):
                if tools.rpm.is_release(line):
                    release = line.split(":")[1].strip()
                    if "%autorelease" in release:
                        logger.info("Skipping setting release as it is set to %autorelease")
                        break
                    file[i] += entry.suffix
                    break
            else:
                raise ActionNotAppliedError("ModifyReleaseAction", "Release line not found in spec file")
            write_file_data(file_path, file)


class RunScriptEntry(BaseEntry):
    ALLOWED_KEYS = {
        "script": str,
        "cwd": str
    }
    REQUIRED_KEYS = {"script"}

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.cwd = kwargs.get("cwd", "rpms")
        self.target = ""
        self.verify_cwd()
    
    def verify_cwd(self):
        if self.cwd in ["rpms", "autopatch"]:
            return
        raise ValueError(f"Invalid value for 'cwd'. Must be 'rpms' or 'autopatch'")

class RunScriptAction(BaseAction):
    ENTRY_CLASS = RunScriptEntry

    def execute(self, package_path: Path):
        for entry in self.entries:
            logger.info(f"Running script: {entry}")

            script_file = (self.config_source.parent / "scripts") / entry.script

            entry.cwd = package_path if entry.cwd == "rpms" else self.config_source.parent

            if not script_file.exists():
                raise FileNotFoundError(f"Script file '{script_file}' does not exist")
            
            run_command(["bash", str(script_file)], cwd=entry.cwd, raise_on_failure=True)


class ChangelogEntry(BaseEntry):
    ALLOWED_KEYS = {
        "name": str,
        "email": str,
        "line": list,
    }
    REQUIRED_KEYS = {"name", "email", "line"}

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not self.line or not any(self.line):
            raise ValueError("Line cannot be an empty list")
        self.target = "spec"

class ChangelogAction(BaseAction):
    ENTRY_CLASS = ChangelogEntry

    def execute(self, package_path: Path):
        # Reverse the entries so that the latest entry is added first
        self.entries.reverse()
        for entry in self.entries:
            file_path = entry.get_target_file_name(package_path)
            spec_info = read_file_data(file_path)
            if tools.rpm.spec_contains_autochangelog(spec_info):
                logger.info("Skipping changelog entries as %autochangelog is present")
                if 'almalinux changes:' not in spec_info[0].lower():
                    entry.line[0] = f"AlmaLinux changes: {entry.line[0]}"
                    logger.info(f"Added 'AlmaLinux changes' to the top of the changelog {entry.line[0]}")
                break
            parsed_data = tools.rpm.prepare_spec_file_data_with_rpmspec(spec_info, file_path)
            epoch, version, release = tools.rpm.get_version_information(parsed_data)
            logger.info(f"Adding changelog entry: {entry}")
            for i, line in enumerate(spec_info):
                if line == "%changelog":
                    # Craft first line of changelog entry
                    full_version = f"{version}-{release}"
                    if epoch is not None:
                        full_version = f"{epoch}:{full_version}"
                    current_date = datetime.datetime.today().strftime("%a %b %d %Y")
                    change_info = f"* {current_date} {entry.name} <{entry.email}> - {full_version}"
                    spec_info.insert(i + 1, f"{change_info}")
                    changelog_msg_lines = []
                    for changelog_entry in entry.line:
                        changelog_msg_lines.extend(
                            textwrap.wrap(changelog_entry, 80, initial_indent="- ", subsequent_indent="  ")
                        )
                    spec_info.insert(i + 2, "\n".join(changelog_msg_lines) + "\n")
            
            write_file_data(file_path, spec_info)
        # Reverse the entries back to original order
        self.entries.reverse()


class AddFilesEntry(BaseEntry):
    ALLOWED_KEYS = {
        "type": str,
        "name": str,
        "number": (str, int),
        "modify_spec": bool,
    }
    REQUIRED_KEYS = {"type", "name", "number"}
    VALID_FILE_TYPES = {"patch", "source"}
    # VALID_FILE_TYPES = {"patch"}

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.modify_spec = kwargs.get("modify_spec", True)
        self._validate_file_type()
        self._validate_number()
        self.target = "spec"

    def _validate_file_type(self):
        if self.type not in self.VALID_FILE_TYPES:
            raise ValueError(f"Invalid file type '{self.type}'. Allowed types: {', '.join(self.VALID_FILE_TYPES)}")

    def _validate_number(self):
        if isinstance(self.number, str):
            if self.number != "Latest":
                raise ValueError("Invalid value for 'number'. Must be an integer or 'Latest'.")
        elif self.number < 1:
            raise ValueError("Invalid value for 'number'. Must be greater than 0.")

class AddFilesAction(BaseAction):
    ENTRY_CLASS = AddFilesEntry

    def copy_file_to_package(self, package_path: Path, file_name_to_copy: str):
        source_file = (self.config_source.parent / "files") / file_name_to_copy
        target_file = Path(package_path) / file_name_to_copy

        if (package_path / "SPECS").exists():
            target_file = package_path / "SOURCES" / file_name_to_copy
            target_file.parent.mkdir(parents=True, exist_ok=True)

        if target_file.exists():
            raise ActionNotAppliedError("AddFilesAction", f"File '{file_name_to_copy}' already exists in package")

        shutil.copy(source_file, target_file)
        logger.info(f"Copied file '{source_file}' to '{target_file}'")

    def execute(self, package_path: Path):
        for entry in self.entries:
            package_name = package_path.name
            is_patches_file = any(Path(package_path).rglob("*.patches"))
            if entry.type == "patch":
                directive_type = tools.rpm.DirectiveType.PATCH
                if is_patches_file:
                    entry.target = entry.get_file_name(package_path, "*.patches").name
            elif entry.type == "source":
                directive_type = tools.rpm.DirectiveType.SOURCE

            spec_file_path = entry.get_target_file_name(package_path)
            spec = read_file_data(spec_file_path)

            logger.info(f"Adding file: {entry}")

            if entry.modify_spec:
                tools.rpm.apply_patch(
                    spec,
                    entry.name,
                    directive_type,
                    package_name,
                    is_patches_file,
                    entry.number if entry.number != "Latest" else -1
                )
            self.copy_file_to_package(package_path, entry.name)

            write_file_data(spec_file_path, spec)


class DeleteLineEntry(BaseEntry):
    ALLOWED_KEYS = {
        "target": str,
        "lines": list,
    }
    REQUIRED_KEYS = {"target", "lines"}

class DeleteLineAction(BaseAction):
    ENTRY_CLASS = DeleteLineEntry

    def execute(self, package_path: Path):
        for entry in self.entries:
            file_path = entry.get_target_file_name(package_path)
            logger.info(f"Applying: {entry} to {file_path}")
            for line in entry.lines:
                logger.info(f"Deleting line: {line}")
                find_lines = line.splitlines() if "\n" in line else [line]

                process_lines(file_path, entry.target, find_lines, "", -1)


class AddLineEntry(BaseEntry):
    ALLOWED_KEYS = {
        "target": str,
        "section": str,
        "location": str,
        "content": str,
        "subpackage": str,
    }
    REQUIRED_KEYS = {"target", "section", "location", "content"}

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._validate_target()
        self._validate_location()

    def _validate_target(self):
        if self.target not in ["spec"]:
            raise ValueError(f"Invalid target '{self.target}'. Currently only 'spec' is supported.")

    def _validate_location(self):
        if self.location not in ["top", "bottom"]:
            raise ValueError(f"Invalid location '{self.location}'. Must be 'top' or 'bottom'.")

class AddLineAction(BaseAction):
    ENTRY_CLASS = AddLineEntry

    def execute(self, package_path: Path):
        for entry in self.entries:
            file_path = entry.get_target_file_name(package_path)
            # Get subpackage if specified
            subpackage = getattr(entry, 'subpackage', None)
            logger.info(f"Adding line to {entry.section} section{f' in subpackage {subpackage}' if subpackage is not None else ''} at {entry.location}: {entry.content}")
            try:
                file_data = read_file_data(file_path)
                updated_data = tools.rpm.add_line_to_section(
                    file_data,
                    entry.section,
                    entry.location,
                    entry.content,
                    subpackage
                )
                write_file_data(file_path, updated_data)
                logger.info(f"Successfully added line to {entry.section} section")
            except Exception as e:
                raise ActionNotAppliedError("AddLineAction", str(e))

class ConfigReader:
    ACTION_MAP = {
        "replace": ReplaceAction, # Done
        "delete_line": DeleteLineAction, # Done
        "changelog_entry": ChangelogAction, # Done
        "modify_release": ModifyReleaseAction, # Done
        "delete_files": DeleteFilesAction, # Done
        "add_files": AddFilesAction,
        "run_script": RunScriptAction,
        "add_line": AddLineAction,
    }

    def __init__(self, config_source):
        if isinstance(config_source, (str, bytes, Path)):
            self.config_source = Path(config_source)
        else:
            self.config_source = config_source
        self.actions = []
        self._read_config()

    def _load_config(self):
        if isinstance(self.config_source, Path):
            with open(self.config_source, "r") as f:
                return yaml.safe_load(f)
        elif hasattr(self.config_source, "read"):
            return yaml.safe_load(self.config_source)
        else:
            raise TypeError("Invalid config source. Must be a file path or file-like object.")

    def _validate_config(self, config_data):
        if not config_data or "actions" not in config_data:
            raise ValueError("Invalid configuration file: missing 'actions' section.")

        actions_data = config_data.get("actions")
        if actions_data is None:
            raise ValueError("Invalid configuration file: 'actions' section cannot be None.")
        if not isinstance(actions_data, list):
            raise TypeError("Actions section must be a list of dictionaries.")

        for action_data in actions_data:
            if not isinstance(action_data, dict):
                raise TypeError(f"Invalid action format: {action_data}. Expected dictionary.")
            for action_type, action_entries in action_data.items():
                if action_type not in self.ACTION_MAP:
                    raise ValueError(f"Unknown action type: {action_type}")
                if not isinstance(action_entries, list):
                    raise TypeError(f"Action entries for '{action_type}' must be a list.")

    def _read_config(self):
        config_data = self._load_config()
        self._validate_config(config_data)

        actions_data = config_data.get("actions")
        for action_data in actions_data:
            for action_type, action_entries in action_data.items():
                action_class = self.ACTION_MAP[action_type]
                action_instance = action_class(action_entries, config_source=self.config_source)
                self.actions.append(action_instance)

    def apply_actions(self, package_path: Path):
        for action in self.actions:
            action.execute(Path(package_path))
    
    def get_changelog(self):
        """
        Returns a list of chagelog entries, email and name of latest entry
        (list, str, str)
        """
        changelog = []
        name = ""
        email = ""

        for action in self.actions:
            if not isinstance(action, ChangelogAction):
                continue
            for action_entry in action.entries:
                if not name:
                    name = action_entry.name
                    email = action_entry.email
                changelog.extend(action_entry.line)
        return changelog, name, email
    
    def get_release_suffix(self):
        """
        Returns release suffix from modify_release action
        """
        suffixes = []
        for action in self.actions:
            if not isinstance(action, ModifyReleaseAction):
                continue
            for action_entry in action.entries:
                if action_entry.enabled:
                    suffixes.append(action_entry.suffix)

        return ''.join(suffixes)
