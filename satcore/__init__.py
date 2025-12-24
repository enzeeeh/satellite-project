"""Shared core utilities for satellite pass prediction.

Centralizes orbit propagation helpers, ground station geometry, pass detection,
and TLE loading used across project versions (v1.0, v1.1, v1.2, v2.0).
"""

from .tle_loader import load_tle
from .propagator import (
    TemEci,
    satrec_from_tle,
    propagate_teme,
    gmst_angle,
    teme_to_ecef,
    propagate_satellite,
)
from .ground_station import GroundStation
from .pass_detector import PassEvent, detect_passes

__all__ = [
    "load_tle",
    "TemEci",
    "satrec_from_tle",
    "propagate_teme",
    "gmst_angle",
    "teme_to_ecef",
    "propagate_satellite",
    "GroundStation",
    "PassEvent",
    "detect_passes",
]
