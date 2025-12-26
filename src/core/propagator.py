"""Propagation and coordinate transforms.

Provides thin wrappers around SGP4 for TEME propagation, Greenwich Mean
Sidereal Time (GMST) calculation, and a simplified TEME→ECEF rotation.

Notes:
- The TEME→ECEF conversion here uses a basic Z-axis rotation by GMST and
    intentionally ignores polar motion, UT1-UTC offsets, and nutation.
    For high-precision applications, consider using Astropy or IAU2006 models.
"""
from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Tuple

from sgp4.api import Satrec, jday


@dataclass
class TemEci:
    """TEME state at a timestamp.

    Attributes:
        dt: UTC datetime corresponding to this state.
        r_km: TEME position vector in kilometers (x, y, z).
        v_km_s: TEME velocity vector in kilometers/second (vx, vy, vz).
    """

    dt: datetime
    r_km: Tuple[float, float, float]
    v_km_s: Tuple[float, float, float]


def satrec_from_tle(line1: str, line2: str) -> Satrec:
    """Create an SGP4 `Satrec` from TLE lines.

    Args:
        line1: First TLE line (must start with "1 ").
        line2: Second TLE line (must start with "2 ").

    Returns:
        Initialized `Satrec` ready for propagation.
    """
    return Satrec.twoline2rv(line1, line2)


def propagate_teme(sat: Satrec, dt: datetime) -> TemEci:
    """Propagate to a UTC datetime in TEME frame.

    Args:
        sat: Initialized Satrec object.
        dt: UTC datetime (timezone-aware preferred).

    Returns:
        TemEci with TEME position (km) and velocity (km/s).

    Raises:
        RuntimeError: If SGP4 returns a non-zero error code.
    """
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)

    jd, fr = jday(dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second + dt.microsecond / 1e6)
    error_code, r, v = sat.sgp4(jd, fr)
    if error_code != 0:
        raise RuntimeError(f"SGP4 propagation error code {error_code} at {dt.isoformat()}")
    return TemEci(dt=dt, r_km=(r[0], r[1], r[2]), v_km_s=(v[0], v[1], v[2]))


def gmst_angle(dt: datetime) -> float:
    """Compute GMST angle in radians.

    Uses the IAU 1982 formula based on UT1 and Julian date. This is
    sufficient for many visualization and pass-prediction tasks.

    Args:
        dt: UTC datetime (naive treated as UTC).

    Returns:
        GMST angle in radians in the range [0, 2π).
    """
    import math

    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)

    jd, fr = jday(dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second + dt.microsecond / 1e6)
    jd_ut1 = jd + fr
    t_ut1 = (jd_ut1 - 2451545.0) / 36525.0
    gmst_sec = 67310.54841 + (876600.0 * 3600.0 + 8640184.812866) * t_ut1 + 0.093104 * t_ut1**2 - 6.2e-6 * t_ut1**3
    gmst_rad = math.fmod(gmst_sec * (2.0 * math.pi / 86400.0), 2.0 * math.pi)
    if gmst_rad < 0:
        gmst_rad += 2.0 * math.pi
    return gmst_rad


def teme_to_ecef(r_teme_km: Tuple[float, float, float], gmst_rad: float) -> Tuple[float, float, float]:
    """Rotate a TEME vector into ECEF via GMST.

    This function applies a Z-axis rotation by the GMST angle. It does not
    account for polar motion, UT1-UTC offset, or nutation (which are small).

    Args:
        r_teme_km: Position vector in TEME (x, y, z) in kilometers.
        gmst_rad: GMST angle in radians.

    Returns:
        Position vector in ECEF (x, y, z) in kilometers.
    """
    import math

    x_teme, y_teme, z_teme = r_teme_km
    cos_gmst = math.cos(gmst_rad)
    sin_gmst = math.sin(gmst_rad)

    x_ecef = cos_gmst * x_teme + sin_gmst * y_teme
    y_ecef = -sin_gmst * x_teme + cos_gmst * y_teme
    z_ecef = z_teme

    return (x_ecef, y_ecef, z_ecef)


def propagate_satellite(line1: str, line2: str, dt: datetime) -> Tuple[Tuple[float, float, float], Tuple[float, float, float]]:
    """Convenience helper: propagate a TLE to ECEF position/velocity.

    Args:
        line1: First TLE line starting with "1 ".
        line2: Second TLE line starting with "2 ".
        dt: UTC datetime to propagate to.

    Returns:
        Tuple of (position_ecef_km, velocity_ecef_km_s).
    """

    sat = satrec_from_tle(line1, line2)
    teme = propagate_teme(sat, dt)
    gmst_rad = gmst_angle(dt)
    pos_ecef = teme_to_ecef(teme.r_km, gmst_rad)
    vel_ecef = teme_to_ecef(teme.v_km_s, gmst_rad)
    return pos_ecef, vel_ecef
