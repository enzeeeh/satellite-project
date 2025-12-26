"""Compatibility shim that re-exports shared pass detection."""
from satcore.pass_detector import PassEvent, detect_passes  # type: ignore

__all__ = ["PassEvent", "detect_passes"]
