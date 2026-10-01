import pytest
from pathlib import Path
import shutil
import os
from freezegun import freeze_time
import difflib
from src.actions_handler import ConfigReader, AddFilesAction, DeleteFilesAction, read_file_data

RESULTS_DIR = Path(__file__).parent / "results"
CONFIGS_DIR = Path(__file__).parent / "configs"

@pytest.fixture(scope="session", autouse=True)
def clean_results(request):
    if RESULTS_DIR.exists():
        shutil.rmtree(RESULTS_DIR)
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    yield

    if request.session.testsfailed == 0:
        shutil.rmtree(RESULTS_DIR)

def get_test_cases():
    cases = []
    for case_dir in CONFIGS_DIR.iterdir():
        if case_dir.is_dir():
            yaml_file = (case_dir / "autopatch") / f"{case_dir.name}.yaml"
            spec_input = case_dir / f"{case_dir.name}.spec"
            expected_output = case_dir / "expected"
            if yaml_file.exists() and spec_input.exists() and expected_output.exists():
                cases.append((case_dir.name, yaml_file, spec_input, expected_output))
    return cases

def copy_files(src_dir, dest_dir):
    for root, _, files in os.walk(src_dir):
        for file in files:
            if file not in ["expected", "autopatch", f"{src_dir.name}.yaml"] and not file.endswith(".expected"):
                src_file = Path(root) / file
                rel_path = src_file.relative_to(src_dir)
                dest_file = dest_dir / rel_path
                dest_file.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src_file, dest_file)

def create_file(file_to_create: Path):
    if not file_to_create.parent.exists():
        os.makedirs(file_to_create.parent, exist_ok=True)
    with open(file_to_create, "w") as f:
        f.write(" ")

def create_placeholder(file_to_create: Path):
    """Create a placeholder unless the file already exists.

    Returns the paths the caller must remove afterwards: the placeholder and
    any directories created for it (deepest first). Existing fixture files are
    left untouched and are never scheduled for deletion.
    """
    if file_to_create.exists():
        return []
    created = [file_to_create]
    parent = file_to_create.parent
    while not parent.exists():
        created.append(parent)
        parent = parent.parent
    create_file(file_to_create)
    return created

def delete_test_files(files_to_delete):
    for file in files_to_delete:
        if file.exists():
            if file.is_dir():
                shutil.rmtree(file)
            else:
                os.remove(file)

def compare_file(file1, file2, diff_output_dir):
    diff = difflib.unified_diff(
        file1.read_text().splitlines(keepends=True),
        file2.read_text().splitlines(keepends=True),
        fromfile="expected",
        tofile="result",
        lineterm=""
    )
    diff_text = "\n".join(diff)
    if diff_text:
        diff_file = diff_output_dir / f"{file1.stem}.diff"
        diff_file.write_text(diff_text)
        pytest.fail(f"File mismatch. Diff saved to {diff_file}")

def compare_files(sources_dir, result_case_dir, diff_output_dir):
    for root, _, files in os.walk(sources_dir):
        for file in files:
            if 'scripts' in root:
                continue
            if (file not in ["expected", "autopatch", "scripts", f"{sources_dir.name}.yaml"] and not file.endswith(".spec") )and file.endswith(".expected"):
                src_file = Path(root) / file.replace(".expected", "")
                rel_path = src_file.relative_to(sources_dir)
                dest_file = result_case_dir / rel_path
                expected_file = src_file.with_suffix(src_file.suffix + ".expected")
                compare_file(expected_file, dest_file, diff_output_dir)

def process_actions(config, yaml_file, result_case_dir, case_name):
    files_to_delete = []
    for action in config.actions:
        if isinstance(action, AddFilesAction):
            for entry in action.entries:
                # For syslinux test, file should be created by script
                if entry.name != "syslinux64.exe":
                    file_to_create = yaml_file.parent / "files" / entry.name
                    files_to_delete.extend(create_placeholder(file_to_create))
                    files_to_delete.append(result_case_dir / entry.name)
        elif isinstance(action, DeleteFilesAction):
            for entry in action.entries:
                file_to_create = result_case_dir / entry.file_name
                create_file(file_to_create)
    return files_to_delete

@freeze_time("2025-01-14")
@pytest.mark.parametrize("case_name, yaml_file, spec_input, expected_output", get_test_cases())
def test_apply_actions(case_name, yaml_file, spec_input, expected_output):
    result_case_dir = RESULTS_DIR / spec_input.stem
    sources_dir = CONFIGS_DIR / case_name
    os.makedirs(result_case_dir, exist_ok=True)

    result_spec = result_case_dir / spec_input.name
    result_spec.write_text(spec_input.read_text())

    copy_files(sources_dir, result_case_dir)

    config = ConfigReader(yaml_file)
    files_to_delete = process_actions(config, yaml_file, result_case_dir, case_name)

    try:
        config.apply_actions(result_spec.parent)
    finally:
        delete_test_files(files_to_delete)

    compare_file(expected_output, result_spec, result_case_dir)
    compare_files(sources_dir, result_case_dir, result_case_dir)

    result_spec.unlink()


def test_read_file_data_allows_empty_patches_file(tmp_path):
    patches_file = tmp_path / "pesign.patches"
    patches_file.write_text("")
    assert read_file_data(patches_file) == []


def test_read_file_data_rejects_empty_spec(tmp_path):
    spec_file = tmp_path / "pesign.spec"
    spec_file.write_text("")
    with pytest.raises(ValueError, match="File is empty"):
        read_file_data(spec_file)
