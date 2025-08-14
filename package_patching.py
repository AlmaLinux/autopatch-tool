#!/usr/bin/env python3
import os
import sys
from logging import INFO, DEBUG

# First try importing via site-packages path, then try directly from "src"
try:
    from autopatch.tools.logger import logger
    from autopatch.debranding import apply_modifications
except ImportError:
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
    from src.tools.logger import logger
    from src.debranding import apply_modifications

import argparse

logger.setLevel(INFO)

def get_args():
    parser = argparse.ArgumentParser(
        description="Script for autopatching packages"
    ) 
    parser.add_argument(
        '-p',
        '--package',
        type=str,
        help='Package name',
        required=True,
    )
    parser.add_argument(
        '-b',
        '--branch',
        type=str,
        help='Upstream branch to apply changes to',
        required=True,
    )
    parser.add_argument(
        '-t',
        '--target-branch',
        type=str,
        help='Target branch to apply changes to, if not set, it will generated automatically, by replacing "c" with "a". Also this branch will be used to read a config file',
        required=False,
    )
    parser.add_argument(
        '--set-custom-tag',
        type=str,
        help='Set custom tag, otherwise it will be generated automatically',
        required=False,
        default=""
    )
    parser.add_argument(
        '--no-tag',
        action='store_true',
        help='Disable tagging',
        required=False
    )
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Enable debug output',
        required=False,
    )
    args = parser.parse_args()
    return args


def main():
    args = get_args()
    if args.debug:
        logger.setLevel(DEBUG)
    apply_modifications(args.package, args.branch, args.set_custom_tag, args.no_tag, args.target_branch)

if __name__ == "__main__":
    main()
