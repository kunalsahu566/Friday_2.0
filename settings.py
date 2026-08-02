"""Small, dependency-free local environment loader for Friday settings."""

import os
import sys
from pathlib import Path


def load_local_env():
    """Load optional settings from source or Friday's macOS app-support folder."""
    env_files = [Path(__file__).with_name(".env")]
    if sys.platform == "darwin":
        env_files.append(Path.home() / "Library" / "Application Support" / "Friday2" / ".env")
    for env_file in env_files:
        if not env_file.exists():
            continue
        for raw_line in env_file.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


load_local_env()
