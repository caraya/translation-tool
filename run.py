#!/usr/bin/env python3
import sys
import os
from pathlib import Path
import multiprocessing

if __name__ == "__main__":
    multiprocessing.freeze_support()
    
    # Determine mode: CLI or GUI
    # If arguments are provided (other than script name), use CLI. Otherwise GUI.
    use_gui = len(sys.argv) == 1

    # 1. If running as a PyInstaller binary (frozen)
    if getattr(sys, 'frozen', False):
        if use_gui:
            from src.gui import main
            main()
        else:
            from src.main import app
            app()
        sys.exit(0)

    # 2. If running as a script, try to auto-detect .venv relative to this script
    base_dir = Path(__file__).parent.resolve()
    venv_dir = base_dir / ".venv"
    venv_python = venv_dir / "bin" / "python"

    # Check if we are currently running inside the venv
    # We compare sys.prefix to the expected venv directory
    # We use os.path.samefile to handle potential symlink/path differences robustly
    try:
        is_in_venv = os.path.samefile(sys.prefix, venv_dir)
    except (OSError, ValueError):
        is_in_venv = False

    # If .venv exists and we aren't using it, re-execute this script with it
    if venv_python.exists() and not is_in_venv:
        # os.execv replaces the current process with the new one
        os.execv(str(venv_python), [str(venv_python)] + sys.argv)

    # 3. Import and run the app (now running inside venv if available)
    try:
        if use_gui:
            from src.gui import main
            main()
        else:
            from src.main import app
            app()
    except ImportError as e:
        print("\n❌ Error: Application dependencies are missing.")
        
        if not venv_dir.exists():
            print("\nIt looks like the virtual environment is not set up yet.")
            print("Please run the following commands to set it up:\n")
            print("  python3 -m venv .venv")
            print("  ./.venv/bin/pip install -r requirements.txt")
            print("\nThen try running this script again.")
        else:
            print(f"\nDetails: {e}")
            print(f"Current Python: {sys.executable}")
            print("Try installing dependencies: ./.venv/bin/pip install -r requirements.txt")
        
        sys.exit(1)
