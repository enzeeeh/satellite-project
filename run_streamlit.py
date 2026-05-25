"""
Launcher script: runs streamlit and logs output to streamlit.log
Run this from the project root:
    python run_streamlit.py
"""
import subprocess, sys, os, pathlib

root = pathlib.Path(__file__).parent
streamlit_exe = root / ".venv" / "Scripts" / "streamlit.exe"
log_file = root / "streamlit.log"

with open(log_file, "w") as f:
    proc = subprocess.Popen(
        [str(streamlit_exe), "run", "app.py",
         "--server.port", "8501",
         "--server.headless", "true"],
        cwd=str(root),
        stdout=f,
        stderr=subprocess.STDOUT,
    )
    print(f"Streamlit PID: {proc.pid}")
    print(f"Waiting for startup...")
    import time
    time.sleep(15)
    if proc.poll() is not None:
        print(f"Process exited with code: {proc.returncode}")
    else:
        print("Process is still running OK")
