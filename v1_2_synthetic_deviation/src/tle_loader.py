"""Compatibility shim that re-exports shared TLE loader."""
from satcore.tle_loader import load_tle  # type: ignore

__all__ = ["load_tle"]
