"""Compatibility shim that re-exports shared ground station helpers."""
from satcore.ground_station import GroundStation  # type: ignore

__all__ = ["GroundStation"]
