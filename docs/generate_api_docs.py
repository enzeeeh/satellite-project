"""Generate HTML API documentation for satcore using pdoc.

Outputs to docs/api/. Requires `pdoc` installed in the active environment.
Usage:
    python docs/generate_api_docs.py
"""
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "docs" / "api"


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    cmd = [sys.executable, "-m", "pdoc", "-o", str(OUT_DIR), "satcore"]
    print("Generating API docs:", " ".join(cmd))
    subprocess.check_call(cmd, cwd=str(ROOT))
    print(f"\n✓ API docs generated in: {OUT_DIR}")


if __name__ == "__main__":
    main()
