import os
import re
from enum import Enum
from tempfile import NamedTemporaryFile
from pathlib import Path

# First try importing via site-packages path, then try directly from "src"
try:
    from autopatch.tools.logger import logger
    from autopatch.tools.tools import run_command
except ImportError:
    from tools.logger import logger
    from tools.tools import run_command

rpmspec_definition = {
    "__python3": "/usr/bin/python3",
    "ldconfig_scriptlets(n:)": "%{nil}",
    "forgemeta": "%{nil}",
    "gometa": "%{nil}",
    "efi_has_alt_arch": "0",
    "dist": "%{nil}",
    "rhel": "8",
}

AUTORELEASE_FINAL_LINE = '}%{?-e:.%{-e*}}%{?-s:.%{-s*}}%{!?-n:%{?dist}}'

class PatchDirectiveType(Enum):
    """
    Enum for patch directive types.
    """
    CLASSIC = 0
    UPPER_P_W_SPACE = 1
    KERNEL = 2
    PATCHES_FILE = 3
    AUTOSETUP = 4
    UPPER_P_N_SPACE = 5

class DirectiveType(Enum):
    """
    Enum for source directive types.
    """
    PATCH = "Patch"
    SOURCE = "Source"

class RPMSpecFileParsingError(Exception):
    """Raised when there is an error parsing RPM spec file"""

def is_spec_comment(line: str) -> bool:
    """
    Check if a line is a comment in a spec file.
    """
    return line.startswith("#")

def is_changelog(line: str) -> bool:
    """
    Check if a line is a start of changelog in a spec file.
    """
    return "%changelog" == line.strip('\n \t')

def is_release(line: str) -> bool:
    """
    Check if a line is a release line in a spec file.
    """
    return line.startswith("Release:")

def spec_contains_autochangelog(spec: list[str]) -> bool:
    """
    Check if a spec file contains an autochangelog block.
    """
    return "%autochangelog" in spec

def spec_contains_autosetup(spec: list[str]) -> bool:
    """
    Check if a spec file uses an autosetup macro.
    """
    for line in spec:
        if "%autosetup" in line or "%forgeautosetup" in line or "%autopatch" in line:
            return True
    return False


def prepare_spec_file_data_with_rpmspec(spec: list[str], spec_file_path) -> list[str]:
    """
    Read a spec file with updated release attribute using rpmspec utility.
    Parameters
    ----------
    spec : list of str
        all changelog_info of spec-file.
    Returns
    -------
    list of str
    """
    try:
        repo_path = Path(spec_file_path)
        source_path = repo_path.parent
        if repo_path.parent.name == "SPECS":
            source_path = repo_path.parent.parent / "SOURCES"

        definitions = ["--define", f"_sourcedir {source_path}"]

        for key, value in rpmspec_definition.items():
            definitions.extend(["--define", f"{key} {value}"])

        with NamedTemporaryFile("w", delete=False) as tmp_file:
            tmp_file.write("\n".join(spec))
            tmp_file.flush()
            tmp_file_path = tmp_file.name
        result = run_command(["rpmspec", "--parse", tmp_file_path, *definitions])
        os.remove(tmp_file_path)

        return list(map(lambda s: f"{s}\n", result.stdout.splitlines()))

    except Exception as err:
        raise RPMSpecFileParsingError("Failed to parse spec data with rpmspec") from err


def get_version_information(spec: list[str], ignore_macros: bool) -> tuple[str, ...]:
    """
    Gets epoch, version and release (last in the file).
    Parameters
    ----------
    spec : list of str
        all changelog_info of spec-file.
    Returns
    -------
    tuple of str
        EVR of package.
    """
    try:
        epoch, version, release = None, None, None
        for i, line in enumerate(spec):
            if epoch is None and line.startswith("Epoch:"):
                epoch = line.rstrip().split()[-1]
            if version is None and line.startswith("Version:"):
                version = line.rstrip().split()[-1]
            if release is None and line.startswith("Release:"):
                release = spec[i].rstrip().split()[-1]
        if release and not ignore_macros:
            release = _analyze_string(release, spec)
        if version and not ignore_macros:
            version = _analyze_string(version, spec)
        return epoch, version, release
    except Exception as err:
        raise RPMSpecFileParsingError("Failed to parse epoch/version/release") from err


def _analyze_string(s: str, spec: list[str]) -> str:
    """
    Parses variable (ignores %{?.*}, recursively finds value of %{.*}).
    Parameters
    ----------
    s : str
        value of variable from spec-file.
    spec : list of str
        all changelog_info of spec-file.
    Returns
    -------
    str
        real value of variable (without other variables).
    """
    i = 0
    answer = ""
    while i < len(s):
        if s[i] == "%":
            i += 2
            variable = ""
            if s[i] == "?":
                counter = 1
                while counter != 0:
                    if s[i] == "{":
                        counter += 1
                    if s[i] == "}":
                        counter -= 1
                    i += 1
            else:
                while s[i] != "}":
                    variable += s[i]
                    i += 1
            if variable:
                answer += _get_value_from_variable(variable, spec)
                i += 1
        else:
            answer += s[i]
            i += 1
    return answer


def _get_value_from_variable(variable: str, spec: list[str]) -> str:
    """
    Gets real value of variable.
    Parameters
    ----------
    variable : str
        value of variable from spec-file.
    spec : list of str
        all changelog_info of spec-file.
    Returns
    -------
    str
        real value of variable (without other variables).
    """
    for line in spec:
        if variable in line and (line.startswith("%define") or line.startswith("%global")):
            if "shortcommit" in line:
                continue
            # check full name alignment
            if line.split()[1] != variable:
                continue
            # recursion
            value = _analyze_string(line.split()[-1], spec)
            return value
    raise Exception(f"Variable {variable} is used but not defined in specfile")


def find_last_directive(spec: list[str], directive_type: DirectiveType):
    """
    Find the last directive of the given type in the spec file.
    Parameters
    ----------
    spec : list of str
        all changelog_info of spec-file.
    directive_type : DirectiveType
        type of directive to find Source or Patch.
    """
    last_directive_number = None
    last_directive_index = None  # To track the last directive regardless of block
    directives_without_numbers = False

    in_conditional = False
    last_endif_index = None

    for i, line in enumerate(spec):
        # Track conditional blocks
        if re.match(r"^%endif\b", line) or re.match(r"^popd\b", line):
            in_conditional = True
            last_endif_index = i - 1
        elif (
            (re.match(r"^%if*", line) or re.match(r"^pushd*", line)) and
            in_conditional
        ):
            in_conditional = False

        # Track the last directive
        if (result := re.match(rf"{directive_type.value}([0-9]*):", line)):
            if not in_conditional:
                last_directive_index = i
            if result.group(1):
                last_directive_number = int(result.group(1))
            else:
                # Directive is used in unnumbered way
                last_directive_number = 0
                directives_without_numbers = True
            break

    # Adjust the position to be after the last %endif if needed
    if last_directive_index is None and last_endif_index is not None:
        last_directive_index = last_endif_index

    if last_directive_number is None:
        if directive_type == DirectiveType.PATCH:
            logger.warning(f"No {directive_type} directives found in spec file, creating a new block")
            return find_last_directive(spec, DirectiveType.SOURCE)
        else:
            raise RPMSpecFileParsingError(f"No {directive_type} directives found in spec file")

    return (last_directive_number, last_directive_index, directives_without_numbers)


def find_almalinux_block(spec: list[str], directive_type: str):
    """
    Find the almalinux block in the spec file.
    Parameters
    ----------
    spec : list of str
        all changelog_info of spec-file.
    directive_type : str
        type of directive to find Source or Patch.
    """
    for _, line in enumerate(spec):
        if re.match(rf"^# AlmaLinux {directive_type}*$", line, re.IGNORECASE):
            return True
    return False


def get_patch_directive_type(line: str) -> PatchDirectiveType:
    """
    Get the type of patch directive from a line in the spec file.
    """
    line = line.strip()

    if re.match(r"^%patch[0-9]{1,5}", line):
        return PatchDirectiveType.CLASSIC
    if re.match(r"^%patch\s+-P\s+[0-9]{1,5}", line):
        return PatchDirectiveType.UPPER_P_W_SPACE
    if re.match(r"^%patch\s+-P[0-9]{1,5}", line):
        return PatchDirectiveType.UPPER_P_N_SPACE
    if re.match(r"^(ApplyOptionalPatch|ApplyPatch)", line):
        return PatchDirectiveType.KERNEL
    return None


def generate_patch_apply_line(
    patch_number: str,
    patch_stem: str,
    patch_directive_type: PatchDirectiveType,
    no_backup: bool
) -> str:
    """
    Generate a patch apply line for a spec file.
    With selected patch directive type.
    Parameters
    ----------
    patch_number : str
        number of patch to apply.
    patch_stem : str
        stem of patch file.
    patch_directive_type : PatchDirectiveType
        type of patch directive to use.
    no_backup : bool
        if True, doesn't adds '-b .{patch_stem}' to the line.
    """
    apply_line = ""
    if patch_directive_type == PatchDirectiveType.CLASSIC:
        apply_line = f"""%patch{patch_number} -p1"""
    elif patch_directive_type == PatchDirectiveType.UPPER_P_W_SPACE:
        apply_line = f"""%patch -P {patch_number} -p1"""
    elif patch_directive_type == PatchDirectiveType.UPPER_P_N_SPACE:
        apply_line = f"""%patch -P{patch_number} -p1"""
    elif patch_directive_type == PatchDirectiveType.KERNEL:
        apply_line = f"""ApplyPatch {patch_stem}.patch"""
    else:
        raise RPMSpecFileParsingError("Unknown patch directive type")
    if not no_backup and patch_directive_type != PatchDirectiveType.KERNEL:
        apply_line += f" -b .{patch_stem}"
    return apply_line


def define_type_patch_directive_type(
    spec: list[str],
    package_name: str,
    patches_file: bool
) -> PatchDirectiveType:
    """
    Get the type of patch directive.
    With all possible ways to apply a patch.
    """
    if patches_file:
        return PatchDirectiveType.PATCHES_FILE
    if package_name == 'kernel':
        return PatchDirectiveType.KERNEL
    if spec_contains_autosetup(spec):
        return PatchDirectiveType.AUTOSETUP
    for line in spec:
        directive_type = get_patch_directive_type(line)
        if directive_type is not None:
            return directive_type
    return None


def find_index_to_insert(spec: list[str]) -> int:
    """
    Find the index to insert a patch directive.
    """
    in_conditional = False
    conditional_start_index = None
    last_patch_apply_index = None
    for i, line in enumerate(spec):
        # Track conditional blocks
        if last_patch_apply_index is None and (re.match(r"^%endif\b", line) or re.match(r"^popd\b", line)):
            in_conditional = True
            conditional_start_index = i
        elif (
            in_conditional and
            (re.match(r"^%if*", line) or re.match(r"^pushd*", line))
        ):
            in_conditional = False
            if last_patch_apply_index is None:
                # If we haven't found a patch yet, this conditional block isn't relevant
                conditional_start_index = None
        # Track the last %patch directive regardless of block
        patch_directive = get_patch_directive_type(line)
        if (
            last_patch_apply_index is None and
            patch_directive is not None
        ):
            last_patch_apply_index = i
    insert_index = (conditional_start_index if conditional_start_index is not None
                    else last_patch_apply_index)

    return insert_index


def find_setup_line(spec: list[str]) -> int:
    """
    Find the index of the %setup in the spec file.
    """
    for i, line in enumerate(spec):
        if re.match(r"^%setup\b", line):
            return i
    return None


def get_ids_of_patches(spec: list[str]) -> list[int]:
    """
    Get the ids of all patches in the spec file.
    """
    patches = []
    for line in spec:
        if (result := re.match(r"^Patch([0-9]+):", line)):
            patches.append(int(result.group(1)))
    return patches


def insert_almalinux_line(spec: list[str], directive_type: DirectiveType, insert_index: int) -> None:
    """
    Insert 'Applying AlmaLinux' line into the spec file.
    """
    almalinux_block_exists = False

    for _, line in enumerate(spec):
        if re.match(rf"^# Applying AlmaLinux {directive_type.value}*$", line, re.IGNORECASE):
            almalinux_block_exists = True
    if not almalinux_block_exists:
        spec.insert(insert_index, f"\n# Applying AlmaLinux {directive_type.value}")


def apply_patch(
        spec: list[str],
        patch_name: str,
        directive_type:DirectiveType,
        package_name: str,
        patches_file: bool,
        patch_number: int = -1,
        insert_almalinux: bool = True,
        no_backup: bool = False,
    ) -> None:
    # pylint: disable=too-many-positional-arguments
    # pylint: disable=too-many-arguments
    # pylint: disable=too-many-branches
    """
    Append changelog_info to project's specfile which apply certain patch.
    Patches are added after the last patch in the "AlmaLinux patches" block.
    If no such block exists, it will be created after the last patch directive.
    """
    spec.reverse()
    last_patch_number, last_patch_index, patches_without_numbers = find_last_directive(
        spec, directive_type
    )

    if not find_almalinux_block(spec, directive_type.value) and insert_almalinux:
        spec.insert(last_patch_index, f"\n# AlmaLinux {directive_type.value}")
    # Insert new patch after the last patch
    if patches_without_numbers:
        new_patch_number = ""
    else:
        new_patch_number = str(last_patch_number + 1)
        if patch_number != -1:
            if patch_number in get_ids_of_patches(spec):
                logger.error(f"patch_number {patch_number} already exists in the spec file")
                raise RPMSpecFileParsingError(
                    f"patch_number {patch_number} already exists in the spec file"
                )
            new_patch_number = str(patch_number)
    spec.insert(last_patch_index, f"{directive_type.value}{new_patch_number}: {patch_name}")

    patch_directive_type = define_type_patch_directive_type(spec, package_name, patches_file)

    # Doesn't need to apply patch directive for autosetup package and for packes with patches file
    if (
        directive_type == DirectiveType.PATCH and
        patch_directive_type != PatchDirectiveType.PATCHES_FILE
    ):
        insert_index = find_index_to_insert(spec)
        logger.debug(f"Patch directive type: {patch_directive_type} and insert index: {insert_index}")

        if insert_index is not None:
            if (
                patch_directive_type != PatchDirectiveType.AUTOSETUP and
                patch_directive_type != PatchDirectiveType.PATCHES_FILE
                ):
                if insert_almalinux:
                    insert_almalinux_line(spec, directive_type, insert_index)

                spec.insert(
                    insert_index,
                    generate_patch_apply_line(
                        new_patch_number,
                        ''.join(patch_name.split('.')[:-1]),
                        patch_directive_type,
                        no_backup
                    )
                )
        else:
            if patch_directive_type != PatchDirectiveType.AUTOSETUP:
                insert_index = find_setup_line(spec)
                logger.debug(f"Insert index: {insert_index}")
                if insert_index is not None:
                    if insert_almalinux:
                        insert_almalinux_line(spec, directive_type, insert_index)

                    patch_directive_type = PatchDirectiveType.UPPER_P_W_SPACE
                    spec.insert(
                        insert_index, 
                        generate_patch_apply_line(
                                new_patch_number,
                                ''.join(patch_name.split('.')[:-1]),
                                patch_directive_type,
                                no_backup
                            )
                        )
                else:
                    raise RPMSpecFileParsingError("Failed to find a place to insert patch directive")
            else:
                logger.info("Skipping applying patch directive for autosetup package")

        if patch_directive_type is None:
            raise RPMSpecFileParsingError("Unknown patch directive type")
    spec.reverse()


def find_section_boundaries(spec: list[str], section: str, subpackage: str = None) -> tuple:
    """
    Find the start and end indices of the specified section in the spec file
    If subpackage is specified, find the sections instead for that subpackage

    Parameters
    ----------
    spec : list of str
        All content of the spec file.
    section : str
        Section name (global, description, build, install, etc.).
    subpackage : str, optional
        Name of the subpackage. If None, targets the main package.

    Returns
    -------
    tuple
        (starting_index, ending_index) of the section.
    """

    logger.debug(f"Looking for section '{section}' boundaries" + (f" in subpackage '{subpackage}'" if subpackage else " in main package"))
    section_marker = f"%{section}"

    # There may be more here that i've missed?
    section_boundaries = [
        "%description", "%prep", "%build", "%install", "%check", "%clean",
        "%files", "%changelog", "%pre", "%post", "%preun", "%postun", "%package",
        "%triggerin", "%triggerun", "%triggerpostun", "%verifyscript", "%pretrans", "%posttrans"
    ]

    # The "global" section is special since it's not explicitly labeled as such
    # in spec file terminology
    if section == "global":
        if subpackage is not None:
            # We're looking for the "global" section of a specific subpackage
            for i, line in enumerate(spec):
                clean_line = line.strip()
                if any(clean_line.startswith(pattern) for pattern in [f"%package {subpackage}", f"%package -n {subpackage}"]):
                    logger.debug(f"Found our subpackage '{subpackage}' at line {i+1}")
                    starting_index = i  # Start after the package declaration
                    # Now find where this section ends
                    for j in range(i + 1, len(spec)):
                        next_line = spec[j].strip()
                        # Section ends at next package or section marker
                        if next_line.startswith("%package"):
                            return (starting_index, j - 1)
                        elif any(next_line.startswith(marker) for marker in section_boundaries if marker != "%package"):
                            return (starting_index, j - 1)
                    # If we didn't find an end marker, section runs to the end of file
                    return (starting_index, len(spec) - 1)
            # If we got here, we didn't find a subpackage
            pkg_list = [line.strip() for line in spec if line.strip().startswith('%package')]
            raise RPMSpecFileParsingError(
                f"Couldn't find subpackage '{subpackage}'. Available packages: {pkg_list}"
            )
        else:
            # For the main package's global section, we simply need to find the first section marker
            for i, line in enumerate(spec):
                if any(line.strip().startswith(marker) for marker in section_boundaries):
                    return (0, i - 1)  # Global section runs from start to first section marker

            # If no section markers found, the whole file is the global section? Doesn't seem right
            raise RPMSpecFileParsingError(
                "Couldn't find any sections inside the spec. Is this expected?"
            )

    # For "normal" (non-global) sections, we need to keep track of which package we're in
    current_pkg = None
    if subpackage is None:
        in_target_pkg = True
    else:
        in_target_pkg = False

    for i, line in enumerate(spec):
        clean_line = line.strip()

        # This logic is a bit confusing, but we need to keep track of which package we are in
        # The code supports both "%package subpackage" and "%package -n subpackage" definitions
        if clean_line.startswith("%package"):
            parts = clean_line.split()
            if len(parts) >= 3 and parts[1] == "-n":
                # %package -n format
                current_pkg = parts[2]
                in_target_pkg = (current_pkg == subpackage)
                logger.debug(f"Now in subpackage: {current_pkg} (line {i+1})")
            elif len(parts) >= 2:
                # Standard %package format
                current_pkg = parts[1]
                in_target_pkg = (current_pkg == subpackage)
                logger.debug(f"Now in subpackage: {current_pkg} (line {i+1})")

        # Check if this line is our target section
        if clean_line.startswith(section_marker):
            # For sections that can specify a subpackage directly (like %files etc)
            if section_marker in ["%files", "%description", "%pre", "%post", "%preun", "%postun"]:
                parts = clean_line.split()

                # Check for -n format in the section marker
                if len(parts) >= 3 and parts[1] == "-n":
                    section_pkg = parts[2]
                    if subpackage is not None and section_pkg == subpackage:
                        starting_index = i
                        logger.debug(f"Found {section} for subpackage {subpackage} (-n format) at line {i+1}")
                    else:
                        continue  # Not our target subpackage
                elif len(parts) >= 2:
                    section_pkg = parts[1]
                    if subpackage is not None and section_pkg == subpackage:
                        starting_index = i
                        logger.debug(f"Found {section} for subpackage {subpackage} at line {i+1}")
                    else:
                        continue  # Not our target subpackage
                else:
                    # No subpackage specified in the section marker
                    if subpackage is None:
                        starting_index = i
                        logger.debug(f"Found {section} for main package at line {i+1}")
                    else:
                        continue  # We're looking for a specific subpackage
            else:
                # For general sections like %build, %install that apply to a package
                if in_target_pkg or subpackage is None:
                    starting_index = i
                    logger.debug(f"Found {section} at line {i+1}")
                else:
                    continue  # Not in our target package

            # Now find where this section ends
            for j in range(i + 1, len(spec)):
                if any(spec[j].strip().startswith(marker) for marker in section_boundaries):
                    logger.debug(f"Section {section} ends at line {j}")
                    return (starting_index, j - 1)

            # If we didn't find an end marker, section runs to the end of file
            logger.debug(f"Section {section} runs to the end of the file")
            return (starting_index, len(spec) - 1)

    # If we get here, we couldn't find the section
    if subpackage:
        raise RPMSpecFileParsingError(
            f"Couldn't find section '{section}' for subpackage '{subpackage}'"
        )
    else:
        raise RPMSpecFileParsingError(f"Couldn't find section '{section}' in the spec file")

def add_line_to_section(spec: list[str], section: str, location: str,
                       content: str, subpackage: str = None) -> list[str]:
    """
    Add a line to the specified section of the spec file.

    Parameters
    ----------
    spec : list of str
        All content of the spec file.
    section : str
        Section name (global, description, build, install, etc.).
    location : str
        Where to add the line within the section (top or bottom).
    content : str
        Content to add.
    subpackage : str, optional
        Name of the subpackage. If None, targets the main package.

    Returns
    -------
    list of str
        Updated spec file content.
    """
    try:
        # Find the boundaries of our target section
        starting_index, ending_index = find_section_boundaries(spec, section, subpackage)
        # Figure out where to put the new content
        if location.lower() == "top":
            insert_idx = starting_index + 1
            # For the main package global section, insert at the very beginning
            if section == "global" and subpackage is None and starting_index == 0:
                insert_idx = 0
        elif location.lower() == "bottom":
            insert_idx = ending_index + 1
        else:
            raise ValueError(f"Invalid location '{location}'. Must be 'top' or 'bottom'")
        if not content.endswith('\n'):
            content += '\n'
        spec.insert(insert_idx, content)
        logger.debug(f"Added content at line {insert_idx+1}")
        return spec
    except Exception as e:
        raise RPMSpecFileParsingError(f"Failed to add line to section '{section}': {str(e)}")
