"""
Propagation and coordinate transforms.
- Uses SGP4 to propagate TEME position vectors (km)
- Converts TEME position to ECEF with a simple GMST rotation (approximate)
- Provides Julian date helpers via sgp4.api

Note: This is a minimal, practical approach for pass prediction. For
high-precision work, account for equation of the equinoxes, polar motion,
UT1-UTC, and IAU 2006/2000A models.
"""
from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import List, Tuple

from sgp4.api import Satrec, jday

@dataclass
class TemEci:
    """Container for TEME position/velocity at a timestamp."""
    dt: datetime
    r_km: Tuple[float, float, float]
    v_km_s: Tuple[float, float, float]


def satrec_from_tle(line1: str, line2: str) -> Satrec:
    """Create a Satrec object from TLE lines."""
    return Satrec.twoline2rv(line1, line2)


def propagate_teme(sat: Satrec, dt: datetime) -> TemEci:
    """Propagate the satellite to the given UTC datetime.

    Args:
        sat: Initialized Satrec object.
        dt: UTC datetime (timezone-aware preferred).

    Returns:
        TemEci with TEME position (km) and velocity (km/s).

    Raises:
        RuntimeError: If SGP4 returns a non-zero error code.
    """
    if dt.tzinfo is None:
        # Treat naive as UTC for simplicity
        dt = dt.replace(tzinfo=timezone.utc)

    jd, fr = jday(dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second + dt.microsecond / 1e6)
    error_code, r, v = sat.sgp4(jd, fr)
    if error_code != 0:
        raise RuntimeError(f"SGP4 propagation error code {error_code} at {dt.isoformat()}")
    return TemEci(dt=dt, r_km=(r[0], r[1], r[2]), v_km_s=(v[0], v[1], v[2]))


def gmst_angle(dt: datetime) -> float:
    """Compute GMST angle (radians) from UTC datetime.
    
    Uses the simplified IAU 1982 GMST formula.
    """
    import math
    
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    
    # Get Julian date
    jd, fr = jday(dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second + dt.microsecond / 1e6)
    jd_ut1 = jd + fr
    
    # Days since J2000.0
    t_ut1 = (jd_ut1 - 2451545.0) / 36525.0
    
    # GMST in seconds (IAU 1982 formula)
    gmst_sec = 67310.54841 + (876600.0 * 3600.0 + 8640184.812866) * t_ut1 \
               + 0.093104 * t_ut1**2 - 6.2e-6 * t_ut1**3
    
    # Convert to radians and normalize to [0, 2π)
    gmst_rad = math.fmod(gmst_sec * (2.0 * math.pi / 86400.0), 2.0 * math.pi)
    if gmst_rad < 0:
        gmst_rad += 2.0 * math.pi
    
    return gmst_rad


def teme_to_ecef(r_teme_km: Tuple[float, float, float], gmst_rad: float) -> Tuple[float, float, float]:
    """Rotate TEME to ECEF using a simple Z-rotation by GMST.

    Args:
        r_teme_km: TEME position vector (km)
        gmst_rad: GMST angle in radians

    Returns:
        ECEF position vector (km)
    """
    import math

    x, y, z = r_teme_km
    cg = math.cos(gmst_rad)
    sg = math.sin(gmst_rad)

    x_e = cg * x + sg * y
    y_e = -sg * x + cg * y
    z_e = z
    return (x_e, y_e, z_e)


def propagate_satellite(line1: str, line2: str, dt: datetime) -> Tuple[Tuple, Tuple]:
    """
    Propagate satellite and return ECEF position/velocity.
    
    Args:
        line1: TLE line 1
        line2: TLE line 2
        dt: UTC datetime
    
    Returns:
        (pos_ecef_km, vel_ecef_km) where vel is rotated TEME velocity
    """
    sat = satrec_from_tle(line1, line2)
    teme = propagate_teme(sat, dt)
    gmst_rad = gmst_angle(dt)
    pos_ecef = teme_to_ecef(teme.r_km, gmst_rad)
    
    # Rotate velocity too
    vel_ecef = teme_to_ecef(teme.v_km_s, gmst_rad)
    
    return pos_ecef, vel_ecef
