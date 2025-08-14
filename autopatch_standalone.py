#!/usr/bin/env python3

import argparse
import os
import sys

# First try importing via site-packages path, then try directly from "src"
try:
    import autopatch.tools.rpm
    from autopatch.actions_handler import ConfigReader
except ImportError:
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
    import src.tools.rpm
    from actions_handler import ConfigReader

def main():
    parser = argparse.ArgumentParser(
       description="Simple Autopatch invocation script"
    )

    parser.add_argument(
        '--config',
        type=str,
        help='config file',
        required=True,
    )
    parser.add_argument(
        '--targetdir',
        type=str,
        help='Target directory',
        required=True,
    )
    args = parser.parse_args()

    config = ConfigReader(args.config)
    config.apply_actions(args.targetdir)

if __name__ == "__main__":
    main()
