"""Copy of v1_0's TLE loader to keep physics identical"""
from typing import Tuple

def load_tle(path: str) -> Tuple[str, str, str]:
    with open(path, "r", encoding="utf-8") as f:
        lines = [ln.strip() for ln in f.readlines()]
    content = [ln for ln in lines if ln and not ln.startswith("#")]
    if len(content) < 3:
        raise ValueError(
            f"TLE file '{path}' must contain at least 3 non-empty lines (name, line1, line2)."
        )
    name, line1, line2 = content[0], content[1], content[2]
    if not (line1.startswith("1 ") and line2.startswith("2 ")):
        raise ValueError("TLE lines must start with '1 ' and '2 '.")
    return name, line1, line2
