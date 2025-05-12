import subprocess
from pathlib import Path
from typing import Dict
from yaml import safe_load

# First try importing via site-packages path, then try directly from "src"
try:
    from autopatch.tools.logger import logger
except ImportError:
    from tools.logger import logger


def run_command(command, raise_on_failure=True, without_log=False, shell=False, cwd=None):
    try:
        command_str = command if shell else ' '.join(command)
        if not without_log:
            logger.debug(f"Running command: {command_str}")
        result = subprocess.run(command, capture_output=True, text=True, shell=shell, cwd=cwd)
        if result.returncode != 0:
            error_message = f"Command failed: {command_str}\n{result.stderr.strip()}"
            if not without_log:
                logger.error(error_message)
            if raise_on_failure:
                raise RuntimeError(error_message)
        return result
    except Exception as e:
        if raise_on_failure:
            raise RuntimeError(f"Error running command: {e}") from e

def load_cas_credentials(path: str = '~/.cas/credentials') -> Dict[str, str]:
    try:
        with open(Path(path).expanduser()) as f:
            content = safe_load(f)
            if not content:
                raise ValueError(f"Credentials file at {path} is empty or contains invalid content.")
            return {
                'username': content['immudb_username'],
                'password': content['immudb_password'],
                'database': content['immudb_database'],
                'immudb_address': content['immudb_address'],
            }
    except FileNotFoundError:
        logger.error(f"Credentials file not found at {path}")
        raise
    except KeyError as e:
        logger.error(f"Missing required key in credentials file: {e}")
        raise
