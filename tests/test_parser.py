import re
import pytest
from actions_handler import (
    AddFilesEntry,
    ReplaceEntry,
    DeleteLineEntry,
    ChangelogEntry,
    DeleteFilesEntry,
    AddFilesAction,
    ReplaceAction,
    DeleteLineAction,
    ChangelogAction,
    DeleteFilesAction,
    ConfigReader
)

@pytest.fixture
def create_temp_config_file(tmp_path):
    def _create_temp_config_file(config_string):
        temp_file = tmp_path / "temp_config.yaml"
        temp_file.write_text(config_string)
        return temp_file
    return _create_temp_config_file


def test_add_files_entry_valid():
    entry = AddFilesEntry(type="source", name="example.tar.gz", number=1)
    assert entry.type == "source"
    assert entry.name == "example.tar.gz"
    assert entry.number == 1

def test_add_files_entry_invalid_type():
    with pytest.raises(ValueError, match="Invalid file type"):
        AddFilesEntry(type="invalid", name="example.tar.gz", number=1)

def test_add_files_entry_extra_keys():
    with pytest.raises(ValueError, match="Unexpected keys"):
        AddFilesEntry(type="source", name="example.tar.gz", number=1, extra_key="extra_value")


def test_replace_entry_valid():
    entry = ReplaceEntry(target="spec", find="RHEL", replace="MyLinux", count=2)
    assert entry.target == "spec"
    assert entry.find == "RHEL"
    assert entry.replace == "MyLinux"
    assert entry.count == 2


def test_replace_entry_default_count():
    entry = ReplaceEntry(target="spec", find="RHEL", replace="MyLinux")
    assert entry.count == -1

def test_replace_entry_extra_keys():
    with pytest.raises(ValueError, match="Unexpected keys"):
        ReplaceEntry(target="spec", find="RHEL", replace="MyLinux", count=1, extra_key="extra_value")

def test_replace_empty_target():
    with pytest.raises(ValueError, match="Value for 'target' cannot be empty."):
        ReplaceEntry(target="", find="RHEL", replace="MyLinux", count=1)

def test_delete_line_entry_valid():
    entry = DeleteLineEntry(target="README.md", lines=["line1", "line2"])
    assert entry.target == "README.md"
    assert entry.lines == ["line1", "line2"]

def test_delete_line_entry_extra_keys():
    with pytest.raises(ValueError, match="Unexpected keys"):
        DeleteLineEntry(target="spec", lines=["line1", "line2"], extra_key="extra_value")


def test_changelog_entry_valid():
    entry = ChangelogEntry(name="AlmaLinux", email="almalinux@example.com", line=["Updated changelog"])
    assert entry.name == "AlmaLinux"
    assert entry.email == "almalinux@example.com"
    assert entry.line == ["Updated changelog"]

def test_changelog_entry_extra_keys():
    with pytest.raises(ValueError, match="Unexpected keys"):
        ChangelogEntry(name="AlmaLinux", email="almalinux@example.com", line=["Updated changelog"], extra_key="extra_value")

def test_changelog_empty_nmae():
    with pytest.raises(ValueError, match="Value for 'email' cannot be empty."):
        ChangelogEntry(name="AlmaLinux", email="", line=["Updated changelog"])


def test_delete_files_entry_valid():
    entry = DeleteFilesEntry(file_name="unnecessary_file.txt")
    assert entry.file_name == "unnecessary_file.txt"

def test_delete_files_entry_extra_keys():
    with pytest.raises(ValueError, match="Unexpected keys: extra_key"):
        DeleteFilesEntry(file_name="unnecessary_file.txt", extra_key="extra_value")


def test_add_files_action():
    action_data = [
        {"type": "source", "name": "example.tar.gz", "number": 1},
        {"type": "patch", "name": "fix.patch", "number": 2},
    ]
    action = AddFilesAction(action_data)
    assert len(action.entries) == 2
    assert isinstance(action.entries[0], AddFilesEntry)
    assert action.entries[0].type == "source"

def test_replace_action():
    action_data = [{"target": "spec", "find": "RHEL", "replace": "MyLinux", "count": 1}]
    action = ReplaceAction(action_data)
    assert len(action.entries) == 1
    assert isinstance(action.entries[0], ReplaceEntry)
    assert action.entries[0].replace == "MyLinux"

def test_delete_line_action():
    action_data = [{"target": "README.md", "lines": ["line1", "line2"]}]
    action = DeleteLineAction(action_data)
    assert len(action.entries) == 1
    assert isinstance(action.entries[0], DeleteLineEntry)
    assert "line1" in action.entries[0].lines

def test_changelog_action():
    action_data = [{"name": "AlmaLinux", "email": "almalinux@example.com", "line": ["Updated branding"]}]
    action = ChangelogAction(action_data)
    assert len(action.entries) == 1
    assert isinstance(action.entries[0], ChangelogEntry)
    assert "Updated branding" in action.entries[0].line

def test_delete_files_action():
    action_data = [{"file_name": "unnecessary_file.txt"}]
    action = DeleteFilesAction(action_data)
    assert len(action.entries) == 1
    assert isinstance(action.entries[0], DeleteFilesEntry)
    assert action.entries[0].file_name == "unnecessary_file.txt"


@pytest.mark.parametrize(
    "config_string, expected_actions, expected_error_message",
    [
        ("""
            """,
            ValueError,
            "Invalid configuration file: missing 'actions' section."
        ),
        ("""
            actions:
            """,
            ValueError,
            "Invalid configuration file: 'actions' section cannot be None."
        ),


        ("""
            actions:
              - delete_files:
                  - file_name: "old_file.txt"
            """,
            {"delete_files": [{"file_name": "old_file.txt", "target": "old_file.txt"}]},
            None
        ),
        ("""
            actions:
              - delete_files:
                  - "old_file.txt"
            """,
            ValueError,
            "Invalid format: expected a dictionary, got str"
        ),
        ("""
            actions:
              - delete_files:
                  - file_name: "old_file.txt"
                  - file_name: "old_file2.txt"
                  - file_name: "old_file3.txt"
            """,
            {"delete_files": [{"file_name": "old_file.txt", "target": "old_file.txt"}, {"file_name": "old_file2.txt", "target": "old_file2.txt"}, {"file_name": "old_file3.txt", "target": "old_file3.txt"}]},
            None
        ),
        ("""
            actions:
              - delete_files:
                  - file_name: "old_file.txt"
                  - wrong_key: "old_file2.txt"
            """,
            ValueError,
            "Unexpected keys: wrong_key"
        ),
        ("""
            actions:
              - delete_files:
            """,
            TypeError,
            "Action entries for 'delete_files' must be a list."
        ),


        ("""
            actions:
              - modify_release:
                - suffix: ".mycustom.1"
                  enabled: true
            """,
            {"modify_release": [{"suffix": ".mycustom.1", "enabled": True, "target": "spec"}]},
            None
        ),
        ("""
            actions:
              - modify_release:
                - suffix: ".mycustom.1"
            """,
            {"modify_release": [{"suffix": ".mycustom.1", "enabled": True, "target": "spec"}]},
            None
        ),
        ("""
            actions:
              - modify_release:
                - suffix: ".almalinux.1"
                  enabled: false
            """,
            {"modify_release": [{"suffix": ".almalinux.1", "enabled": False, "target": "spec"}]},
            None
        ),
        ("""
            actions:
              - modify_release:
                - enabled: false
            """,
            ValueError,
            "Missing required keys: suffix"
        ),
        ("""
            actions:
              - modify_release:
                suffix: ".mycustom.1"
            """,
            TypeError,
            "Action entries for 'modify_release' must be a list."
        ),
        ("""
            actions:
              - modify_release:
                enabled: False
            """,
            TypeError,
            "Action entries for 'modify_release' must be a list."
        ),


        ("""
            actions:
              - replace:
                  - target: "spec"
                    find: "RHEL"
                    replace: "MyCustomLinux"
                    count: -1
            """,
            {"replace": [
                {"target": "spec", "find": "RHEL", "replace": "MyCustomLinux", "count": -1},
            ]},
            None
        ),
        ("""
            actions:
              - replace:
                  - target: "spec"
                    rfind: "RHEL"
                    replace: "MyCustomLinux"
                    count: -1
            """,
            {"replace": [
                {"target": "spec", "rfind": "RHEL", "replace": "MyCustomLinux", "count": -1},
            ]},
            None
        ),
        ("""
            actions:
              - replace:
                  - target: "spec"
                    find: "RHEL"
                    replace: ""
            """,
            ValueError,
            "Value for 'replace' cannot be empty."
        ),
        ("""
            actions:
              - replace:
                  - target: "spec"
                    rfind: "RHEL"
                    replace: ""
            """,
            ValueError,
            "Value for 'replace' cannot be empty."
        ),
        ("""
            actions:
              - replace:
                  - target: "spec"
                    find: ""
                    replace: "AL"
            """,
            ValueError,
            "Value for 'find' or 'rfind' cannot be empty."
        ),
        ("""
            actions:
              - replace:
                  - target: "spec"
                    rfind: ""
                    replace: "AL"
            """,
            ValueError,
            "Value for 'find' or 'rfind' cannot be empty."
        ),
        ("""
            actions:
              - replace:
                  - target: "spec"
                    find: "RHEL"
                    replace: "MyCustomLinux"
                    count: 1
                  - target: "README.md"
                    find: "RHEL"
                    replace: "MyCustomLinux"
            """,
            {"replace": [
                {"target": "spec", "find": "RHEL", "replace": "MyCustomLinux", "count": 1},
                {"target": "README.md", "find": "RHEL", "replace": "MyCustomLinux", "count": -1},
            ]},
            None 
        ),
        ("""
            actions:
              - replace:
                  - target: "spec"
                    find: "RHEL"
                    replace: "MyCustomLinux"
                    count: 1
                  - find: "RHEL"
                    replace: "MyCustomLinux"
            """,
            ValueError,
            "Missing required keys: target"
        ),
        ("""
            actions:
              - replace:
                  - find: "RHEL"
                    replace: "MyCustomLinux"
                    count: 1
            """,
            ValueError,
            "Missing required keys: target"
        ),
        ("""
            actions:
              - replace:
                  - target: "spec"
                    find: "RHEL"
                    count: 1
            """,
            ValueError,
            "Missing required keys: replace"
        ),
        ("""
            actions:
              - replace:
                  - target: "spec"
                    replace: "MyCustomLinux"
                    count: 1
            """,
            ValueError,
            "Either 'find' or 'rfind' parameter must be provided"
        ),
        ("""
            actions:
              - replace:
                    find: "RHEL"
                    replace: "MyCustomLinux"
                    count: 1
            """,
            TypeError,
            "Action entries for 'replace' must be a list."
        ),
        ("""
            actions:
              - replace:
                  - target: 111
                    find: "RHEL"
                    replace: ""
            """,
            TypeError,
            "Invalid type for 'target': expected str, got int"
        ),
        ("""
            actions:
              - replace:
                  - target: "test"
                    find: "RHEL"
                    replace: ""
                    count: "1"
            """,
            TypeError,
            "Invalid type for 'count': expected int, got str"
        ),


        ("""
            actions:
              - delete_line:
                  - target: "README.md"
                    lines: ["line1", "line2"]
                """,
                {"delete_line": [{"target": "README.md", "lines": ["line1", "line2"]}]},
                None
        ),
        ("""
            actions:
              - delete_line:
                  - target: "README.md"
                    lines:
                      - line1
                      - line2
                """,
                {"delete_line": [{"target": "README.md", "lines": ["line1", "line2"]}]},
                None
        ),
        ("""
            actions:
              - delete_line:
                  - target: "README.md"
                    lines: ["line1", "line2"]
                    extra_key: "value"
            """,
            ValueError,
            "Unexpected keys: extra_key"
        ),
        ("""
            actions:
              - delete_line:
                  - target: "README.md"
            """,
            ValueError,
            "Missing required keys: lines"
        ),
        ("""
            actions:
              - delete_line:
                  - lines: ["line1", "line2"]
            """,
            ValueError,
            "Missing required keys: target"
        ),
        ("""
            actions:
              - delete_line:
                  - target: "README.md"
                    lines: "single_line"
            """,
            TypeError,
            "Invalid type for 'lines': expected list, got str"
        ),
        ("""
            actions:
              - delete_line:
                  - target: "README.md"
                    lines:
                      - |
                        line1
                        continuation of line
                      - another line
            """,
            {"delete_line": [{"target": "README.md", "lines": ["line1\ncontinuation of line\n", "another line"]}]},
            None
        ),

        ("""
            actions:
              - changelog_entry:
                  - name: "AlmaLinux"
                    email: "john@example.com"
                    line: 
                        - "Added a new feature"
            """,
            {"changelog_entry": [{"name": "AlmaLinux", "email": "john@example.com", "line": ["Added a new feature"], "target": "spec"}]},
            None
        ),
        ("""
            actions:
              - changelog_entry:
                  - name: "AlmaLinux"
                    email: "john@example.com"
                    line: 
                        - "Added a new feature"
                        - "Fixed a bug"
            """,
            {"changelog_entry": [{"name": "AlmaLinux", "email": "john@example.com", "line": ["Added a new feature", "Fixed a bug"], "target": "spec"}]},
            None
        ),
        ("""
            actions:
              - changelog_entry:
                  - name: "AlmaLinux"
                    email: "john@example.com"
                    line: 
                        - "Added a new feature"
                  - name: "AlmaLinux"
                    email: "john@example.com"
                    line: 
                        - "Fixed a bug"
            """,
            {"changelog_entry": [{"name": "AlmaLinux", "email": "john@example.com", "line": ["Added a new feature"], "target": "spec"}, {"name": "AlmaLinux", "email": "john@example.com", "line": ["Fixed a bug"], "target": "spec"}]},
            None
        ),
        ("""
            actions:
              - changelog_entry:
                  - name: "AlmaLinux"
                    line: ["Fixed bug"]
            """,
            ValueError,
            "Missing required keys: email"
        ),
        ("""
            actions:
              - changelog_entry:
                  - email: "john@example.com"
                    line: ["Initial commit"]
            """, ValueError,
            "Missing required keys: name"
        ),
        ("""
            actions:
              - changelog_entry:
                  - name: "AlmaLinux"
                    email: "john@example.com"
            """,
            ValueError,
            "Missing required keys: line"
        ),
        ("""
            actions:
              - changelog_entry:
                  - name: "AlmaLinux"
                    email: "john@example.com"
                    line: []
            """,
            ValueError,
            "Value for 'line' cannot be empty."
        ),
        ("""
            actions:
              - changelog_entry:
                  - name: "AlmaLinux"
                    email: "john@example.com"
                    line: ["Updated changelog"]
                    extra_key: "unexpected_value"
            """,
            ValueError,
            "Unexpected keys: extra_key"
        ),

        ("""
            actions:
              - add_files:
                  - type: "source"
                    name: "file.tar.gz"
                    number: 1
            """,
            {"add_files": [{"type": "source", "name": "file.tar.gz", "number": 1, "target": "spec", "modify_spec": True}]},
            None
        ),
        ("""
            actions:
              - add_files:
                  - type: "patch"
                    name: "file.tar.gz"
                    number: "Latest"
                    "modify_spec": False
            """,
            {"add_files": [{"type": "patch", "name": "file.tar.gz", "number": "Latest", "target": "spec", "modify_spec": False}]},
            None
        ),
        ("""
            actions:
              - add_files:
                  - type: "invalid"
                    name: "file.tar.gz"
                    number: 1
            """,
            ValueError,
            "Invalid file type 'invalid'. Allowed types:"
        ),
        ("""
            actions:
              - add_files:
                  - name: "file.tar.gz"
                    number: 1
            """,
            ValueError,
            "Missing required keys: type"
        ),
        ("""
            actions:
              - add_files:
                  - type: "patch"
                    number: 1
            """,
            ValueError,
            "Missing required keys: name"
        ),
        ("""
            actions:
              - add_files:
                  - type: "source"
                    name: "file.tar.gz"
            """,
            ValueError,
            "Missing required keys: number"
        ),
        ("""
            actions:
              - add_files:
                  - type: "source"
                    name: "file.tar.gz"
                    number: 1
                    extra_key: "unexpected"
            """,
            ValueError,
            "Unexpected keys: extra_key"
        ),
        ("""
            actions:
              - add_files:
                  - type: "source"
                    name: "file.tar.gz"
                    number: 1
                    extra_key: "unexpected"
            """,
            ValueError,
            "Unexpected keys: extra_key"
        ),
        ("""
            actions:
              - run_script:
                  - script: "source"
            """,
            {"run_script": [{"target": "", "script": "source", "cwd": "rpms"}]},
            None
        ),
        ("""
            actions:
              - run_script:
                  - script: ""
            """,
            ValueError,
            "Value for 'script' cannot be empty."
        ),
        ("""
            actions:
              - run_script:
            """,
            TypeError,
            "Action entries for 'run_script' must be a list."
        ),
        ("""
            actions:
              - run_scri:
            """,
            ValueError,
            "Unknown action type: run_scri"
        ),
    ]
)
def test_config_reader(create_temp_config_file, config_string, expected_actions, expected_error_message):
    if expected_error_message is not None:
        expected_exception_type = expected_actions if isinstance(expected_actions, type) else ValueError
        with pytest.raises(expected_exception_type, match=expected_error_message):
            temp_config = create_temp_config_file(config_string)
            config_reader = ConfigReader(temp_config)
    else:
        temp_config = create_temp_config_file(config_string)
        config_reader = ConfigReader(temp_config)

        assert len(expected_actions) == len(config_reader.actions), (
            f"Number of actions does not match: expected {len(expected_actions)}, got {len(config_reader.actions)}"
        )

        for action in config_reader.actions:
            action_name = next((k for k, v in ConfigReader.ACTION_MAP.items() if v == action.__class__), None)
            expected_entries = expected_actions.get(action_name, [])

            assert len(expected_entries) == len(action.entries), (
                f"Number of entries does not match for action '{action_name}': "
                f"expected {len(expected_entries)}, got {len(action.entries)}"
            )

            for i, expected_entry in enumerate(expected_entries):
                actual_entry = action.entries[i]

                for key, value in expected_entry.items():
                    actual_value = getattr(actual_entry, key, None)
                    assert actual_value == value, (
                        f"Invalid value for key '{key}' in action '{action_name}' entry {i}: "
                        f"expected {value}, got {actual_value}"
                    )

                actual_keys = set(actual_entry.__dict__.keys())
                expected_keys = set(expected_entry.keys())
                extra_keys = actual_keys - expected_keys
                assert not extra_keys, f"Unexpected keys: {', '.join(extra_keys)}"
