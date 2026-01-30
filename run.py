#!/usr/bin/env python3
"""
Quick start script for CyberOps Companion.

Usage:
    python run.py          # Start the web UI
    python run.py --cli    # Show CLI options
"""

import sys
import subprocess
from pathlib import Path


def main():
    """Main entry point."""
    # Add project root to path
    project_root = Path(__file__).parent
    sys.path.insert(0, str(project_root))

    # Check for CLI mode
    if "--cli" in sys.argv or "-c" in sys.argv:
        from src.cli import main as cli_main
        cli_main()
        return

    # Default: Start Streamlit UI
    app_path = project_root / "src" / "ui" / "app.py"

    print("Starting CyberOps Companion...")
    print("Open http://localhost:8501 in your browser")
    print("Press Ctrl+C to stop\n")

    subprocess.run([
        sys.executable, "-m", "streamlit", "run",
        str(app_path),
        "--server.port", "8501",
        "--server.address", "localhost",
        "--browser.gatherUsageStats", "false",
    ])


if __name__ == "__main__":
    main()
