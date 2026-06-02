import pytest

from src.tools.rpm import extract_el_version, get_rpmspec_definitions


@pytest.mark.parametrize(
    "branch, expected",
    [
        ("c8", "8"),
        ("c9", "9"),
        ("c10", "10"),
        ("c8s", "8"),
        ("c10s", "10"),
        ("c8-beta", "8"),
        ("a8", "8"),
        ("a9", "9"),
        ("a10", "10"),
        ("a10s", "10"),
        ("a10-beta", "10"),
    ],
)
def test_extract_el_version_valid(branch, expected):
    assert extract_el_version(branch) == expected


@pytest.mark.parametrize(
    "branch",
    [
        "main",
        "rawhide",
        "fedora",
        "",
        "b8",
    ],
)
def test_extract_el_version_invalid(branch):
    with pytest.raises(ValueError, match="Cannot extract EL version"):
        extract_el_version(branch)


def test_get_rpmspec_definitions_default():
    # The EL version maps onto the real RPM "%{?rhel}" macro.
    definitions = get_rpmspec_definitions()
    assert definitions["rhel"] == "8"


def test_get_rpmspec_definitions_custom():
    definitions = get_rpmspec_definitions("10")
    assert definitions["rhel"] == "10"
