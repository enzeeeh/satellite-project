"""Compatibility shim that re-exports shared propagation helpers."""
from satcore.propagator import (  # type: ignore
    TemEci,
    gmst_angle,
    propagate_satellite,
    propagate_teme,
    satrec_from_tle,
    teme_to_ecef,
)

__all__ = [
    "TemEci",
    "gmst_angle",
    "propagate_satellite",
    "propagate_teme",
    "satrec_from_tle",
    "teme_to_ecef",
]
