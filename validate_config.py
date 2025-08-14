#!/usr/bin/env python3
import argparse
import sys
import os

# First try importing via site-packages path, then try directly from "src"
try:
    from autopatch.actions_handler import ConfigReader
except ImportError:
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
    from src.actions_handler import ConfigReader

def main():
    parser = argparse.ArgumentParser(description="Validate config")
    parser.add_argument("config_file", help="Path to config file")
    args = parser.parse_args()
    try:
        ConfigReader(args.config_file)
        # green color
        print("\033[92mConfig is valid\033[0m")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
