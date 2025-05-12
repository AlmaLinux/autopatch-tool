from setuptools import setup, find_packages

setup(
    name="autopatch",
    version="1.0.0",
    description="Tool for autopatching source content for debranding/modification",
    author="AlmaLinux",
    author_email="info@almalinux.org",
    url="https://github.com/almalinux/autopatch-tool",
    packages=["autopatch", "autopatch.tools"],
    package_dir={
        "autopatch": "src",
        "autopatch.tools": "src/tools",
    },
    entry_points={
        "console_scripts": [
            "autopatch=autopatch_standalone:main",
            "autopatch_package_patching=package_patching:main",
            "autopatch_validate_config=validate_config:main",
        ],
    },
    py_modules=["autopatch_standalone", "package_patching", "validate_config"],
    python_requires=">=3.6",
)
