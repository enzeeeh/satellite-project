"""Core satellite physics and pass prediction library."""

from .tle_loader import load_tle
from .propagator import satrec_from_tle, propagate_teme, gmst_angle, teme_to_ecef, propagate_satellite, TemEci
from .ground_station import GroundStation
from .pass_detector import detect_passes, PassEvent

__all__ = [
    "load_tle",
    "satrec_from_tle",
    "propagate_teme",
    "gmst_angle",
    "teme_to_ecef",
    "propagate_satellite",
    "TemEci",
    "GroundStation",
    "detect_passes",
    "PassEvent",
]
