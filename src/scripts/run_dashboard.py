#!/usr/bin/env python3
"""Run Streamlit dashboard."""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8501)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument(
        "--file-watcher-type",
        default="none",
        choices=["auto", "watchdog", "poll", "none"],
        help="Streamlit file watcher mode. Use 'none' to avoid torch watcher issues.",
    )
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
        "--server.fileWatcherType",
        args.file_watcher_type,
    ]
    environment = os.environ.copy()
    environment.setdefault("STREAMLIT_SERVER_FILE_WATCHER_TYPE", args.file_watcher_type)
    environment.setdefault("HF_HUB_DISABLE_PROGRESS_BARS", "1")
    environment.setdefault("TRANSFORMERS_VERBOSITY", "error")
    subprocess.run(command, check=True, env=environment)


if __name__ == "__main__":
    main()
