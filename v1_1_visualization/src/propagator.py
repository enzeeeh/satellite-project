"""Copy of v1_0's propagator to keep physics identical"""
from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Tuple

from sgp4.api import Satrec, jday

@dataclass
class TemEci:
    dt: datetime
    r_km: Tuple[float, float, float]
    v_km_s: Tuple[float, float, float]


def satrec_from_tle(line1: str, line2: str) -> Satrec:
    return Satrec.twoline2rv(line1, line2)


def propagate_teme(sat: Satrec, dt: datetime) -> TemEci:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    jd, fr = jday(dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second + dt.microsecond / 1e6)
    error_code, r, v = sat.sgp4(jd, fr)
    if error_code != 0:
        raise RuntimeError(f"SGP4 propagation error code {error_code} at {dt.isoformat()}")
    return TemEci(dt=dt, r_km=(r[0], r[1], r[2]), v_km_s=(v[0], v[1], v[2]))


def gmst_angle(dt: datetime) -> float:
    import math
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    jd, fr = jday(dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second + dt.microsecond / 1e6)
    jd_ut1 = jd + fr
    t_ut1 = (jd_ut1 - 2451545.0) / 36525.0
    gmst_sec = 67310.54841 + (876600.0 * 3600.0 + 8640184.812866) * t_ut1 \
               + 0.093104 * t_ut1**2 - 6.2e-6 * t_ut1**3
    gmst_rad = math.fmod(gmst_sec * (2.0 * math.pi / 86400.0), 2.0 * math.pi)
    if gmst_rad < 0:
        gmst_rad += 2.0 * math.pi
    return gmst_rad


def teme_to_ecef(r_teme_km: Tuple[float, float, float], gmst_rad: float) -> Tuple[float, float, float]:
    import math
    x, y, z = r_teme_km
    cg = math.cos(gmst_rad)
    sg = math.sin(gmst_rad)
    x_e = cg * x + sg * y
    y_e = -sg * x + cg * y
    z_e = z
    return (x_e, y_e, z_e)
