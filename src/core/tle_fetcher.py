"""Live TLE fetcher from CelesTrak and Space-Track.

Fetches fresh Two-Line Element data from public sources and caches it
locally so the system works offline if a previous fetch succeeded.

Sources:
- CelesTrak: free, no account required, uses NORAD catalog ID.
- Space-Track: requires a free account at space-track.org.
  Set SPACETRACK_USER and SPACETRACK_PASS in a .env file at the
  project root (never commit this file).

Usage:
    from src.core.tle_fetcher import fetch_tle_celestrak, fetch_tle_spacetrack

    name, line1, line2 = fetch_tle_celestrak(norad_id=43017)
    name, line1, line2 = fetch_tle_spacetrack(norad_id=43017)
"""
from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Tuple

import requests

# Base URLs
_CELESTRAK_URL = "https://celestrak.org/NORAD/elements/gp.php?CATNR={norad_id}&FORMAT=TLE"
_SPACETRACK_LOGIN_URL = "https://www.space-track.org/ajaxauth/login"
_SPACETRACK_TLE_URL = (
    "https://www.space-track.org/basicspacedata/query/class/gp/"
    "NORAD_CAT_ID/{norad_id}/orderby/EPOCH%20desc/limit/1/format/tle"
)

# Default local cache directory
_CACHE_DIR = Path(__file__).resolve().parents[2] / "data" / "tle_cache"

_REQUEST_TIMEOUT = 10  # seconds


def _parse_tle_text(text: str) -> Tuple[str, str, str]:
    """Parse raw TLE text into (name, line1, line2).

    Expects the standard 3-line TLE format:
        SATELLITE NAME
        1 NNNNN...
        2 NNNNN...

    Raises:
        ValueError: If fewer than 3 non-blank lines are found or TLE
            lines do not start with the expected line numbers.
    """
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    if len(lines) < 3:
        raise ValueError(
            f"Expected at least 3 TLE lines, got {len(lines)}. "
            "Response may be empty or malformed."
        )
    name = lines[0]
    line1 = lines[1]
    line2 = lines[2]
    if not line1.startswith("1 ") or not line2.startswith("2 "):
        raise ValueError(
            f"TLE lines do not match expected format.\n"
            f"  Line 1: {line1!r}\n"
            f"  Line 2: {line2!r}"
        )
    return name, line1, line2


def _cache_path(norad_id: int, source: str) -> Path:
    """Return the local cache file path for a given NORAD ID and source."""
    _CACHE_DIR.mkdir(parents=True, exist_ok=True)
    return _CACHE_DIR / f"{norad_id}_{source}.txt"


def _write_cache(norad_id: int, source: str, name: str, line1: str, line2: str) -> None:
    """Write a TLE to the local cache."""
    path = _cache_path(norad_id, source)
    path.write_text(f"{name}\n{line1}\n{line2}\n", encoding="utf-8")


def _read_cache(norad_id: int, source: str) -> Tuple[str, str, str] | None:
    """Read a TLE from the local cache. Returns None if not found."""
    path = _cache_path(norad_id, source)
    if path.exists():
        return _parse_tle_text(path.read_text(encoding="utf-8"))
    return None


def fetch_tle_celestrak(
    norad_id: int,
    use_cache_on_failure: bool = True,
) -> Tuple[str, str, str]:
    """Fetch the latest TLE for a satellite from CelesTrak.

    Args:
        norad_id: NORAD catalog number (e.g. 43017 for AO-91).
        use_cache_on_failure: If True, falls back to the local cached TLE
            when the network request fails.

    Returns:
        (name, line1, line2) strings.

    Raises:
        RuntimeError: If fetch fails and no cache is available.
    """
    url = _CELESTRAK_URL.format(norad_id=norad_id)
    try:
        resp = requests.get(url, timeout=_REQUEST_TIMEOUT)
        resp.raise_for_status()
        name, line1, line2 = _parse_tle_text(resp.text)
        _write_cache(norad_id, "celestrak", name, line1, line2)
        return name, line1, line2
    except Exception as exc:
        if use_cache_on_failure:
            cached = _read_cache(norad_id, "celestrak")
            if cached:
                return cached
        raise RuntimeError(
            f"Failed to fetch TLE for NORAD ID {norad_id} from CelesTrak: {exc}"
        ) from exc


def fetch_tle_spacetrack(
    norad_id: int,
    use_cache_on_failure: bool = True,
) -> Tuple[str, str, str]:
    """Fetch the latest TLE for a satellite from Space-Track.org.

    Reads credentials from environment variables SPACETRACK_USER and
    SPACETRACK_PASS. Set these in a .env file at the project root and
    load it with python-dotenv, or export them in your shell.

    Args:
        norad_id: NORAD catalog number.
        use_cache_on_failure: If True, falls back to the local cached TLE
            when the network request or login fails.

    Returns:
        (name, line1, line2) strings.

    Raises:
        RuntimeError: If credentials are missing, login fails, fetch fails,
            and no cache is available.
    """
    user = os.environ.get("SPACETRACK_USER")
    password = os.environ.get("SPACETRACK_PASS")

    if not user or not password:
        if use_cache_on_failure:
            cached = _read_cache(norad_id, "spacetrack")
            if cached:
                return cached
        raise RuntimeError(
            "SPACETRACK_USER and SPACETRACK_PASS environment variables are not set. "
            "Add them to a .env file at the project root."
        )

    try:
        session = requests.Session()
        login_resp = session.post(
            _SPACETRACK_LOGIN_URL,
            data={"identity": user, "password": password},
            timeout=_REQUEST_TIMEOUT,
        )
        login_resp.raise_for_status()

        tle_resp = session.get(
            _SPACETRACK_TLE_URL.format(norad_id=norad_id),
            timeout=_REQUEST_TIMEOUT,
        )
        tle_resp.raise_for_status()

        # Space-Track returns 2-line format (no name line), prepend NORAD ID as name
        raw = tle_resp.text.strip()
        lines = [ln.strip() for ln in raw.splitlines() if ln.strip()]
        if len(lines) >= 2:
            raw = f"NORAD-{norad_id}\n{lines[0]}\n{lines[1]}"

        name, line1, line2 = _parse_tle_text(raw)
        _write_cache(norad_id, "spacetrack", name, line1, line2)
        return name, line1, line2
    except Exception as exc:
        if use_cache_on_failure:
            cached = _read_cache(norad_id, "spacetrack")
            if cached:
                return cached
        raise RuntimeError(
            f"Failed to fetch TLE for NORAD ID {norad_id} from Space-Track: {exc}"
        ) from exc
