#!/usr/bin/env python3
"""Run Streamlit dashboard."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8501)
    parser.add_argument("--host", default="127.0.0.1")
    args = parser.parse_args()

    app_path = Path("dashboard/app/app.py")
    if not app_path.exists():
        raise FileNotFoundError(f"Dashboard app not found: {app_path}")

    command = [
        sys.executable,
        "-m",
        "streamlit",
        "run",
        str(app_path),
        "--server.address",
        args.host,
        "--server.port",
        str(args.port),
    ]
    subprocess.run(command, check=True)


if __name__ == "__main__":
    main()
