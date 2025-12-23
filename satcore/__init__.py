"""Shared core utilities for pass prediction.

This package centralizes the SGP4 propagation helpers, ground station
geometry, pass detection, and TLE loading used across project versions.
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
