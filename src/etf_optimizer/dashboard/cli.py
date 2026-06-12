from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def main() -> int:
    app_path = Path(__file__).with_name("app.py")
    return subprocess.run([sys.executable, "-m", "streamlit", "run", str(app_path)], check=False).returncode
