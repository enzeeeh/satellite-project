"""TLE loader utility.

Reads a TLE file containing at least three non-empty lines (name, line 1,
line 2). Lines beginning with "#" are treated as comments and ignored.
"""
from typing import Tuple


def load_tle(path: str) -> Tuple[str, str, str]:
    """Load a TLE from a text file.

    The file should contain a name line followed by TLE lines 1 and 2.
    Lines starting with "#" and blank lines are ignored.

    Args:
        path: Path to the TLE file.

    Returns:
        (name, line1, line2)

    Raises:
        ValueError: If the file does not contain a valid TLE.
    """
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
