"""Ground station representation and topocentric geometry.

Provides WGS84-based geodetic to ECEF conversion for a ground station,
topocentric ENU transformation for satellite positions, and elevation angle
computation.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Tuple
import math

_A = 6378.137  # km
_F = 1.0 / 298.257223563
_E2 = _F * (2 - _F)


@dataclass
class GroundStation:
    """Observer location on WGS84 ellipsoid.

    Attributes:
        lat_deg: Geodetic latitude in degrees.
        lon_deg: Geodetic longitude in degrees.
        alt_m: Orthometric height in meters.
    """

    lat_deg: float
    lon_deg: float
    alt_m: float

    @property
    def lat_rad(self) -> float:
        """Latitude in radians."""
        return math.radians(self.lat_deg)

    @property
    def lon_rad(self) -> float:
        """Longitude in radians."""
        return math.radians(self.lon_deg)

    @property
    def alt_km(self) -> float:
        """Altitude in kilometers."""
        return self.alt_m / 1000.0

    def ecef_km(self) -> Tuple[float, float, float]:
        """Observer ECEF coordinates in kilometers.

        Returns:
            (x, y, z) in kilometers.
        """
        lat = self.lat_rad
        lon = self.lon_rad
        sin_lat = math.sin(lat)
        cos_lat = math.cos(lat)
        N = _A / math.sqrt(1.0 - _E2 * sin_lat * sin_lat)
        x = (N + self.alt_km) * cos_lat * math.cos(lon)
        y = (N + self.alt_km) * cos_lat * math.sin(lon)
        z = (N * (1 - _E2) + self.alt_km) * sin_lat
        return (x, y, z)

    def enu_from_ecef(self, sat_ecef_km: Tuple[float, float, float]) -> Tuple[float, float, float]:
        """Transform satellite ECEF to local ENU.

        Args:
            sat_ecef_km: Satellite ECEF (x, y, z) in kilometers.

        Returns:
            Tuple of (east, north, up) in kilometers.
        """
        x_e, y_e, z_e = sat_ecef_km
        xs, ys, zs = self.ecef_km()
        dx, dy, dz = x_e - xs, y_e - ys, z_e - zs

        lat = self.lat_rad
        lon = self.lon_rad
        sin_lat = math.sin(lat)
        cos_lat = math.cos(lat)
        sin_lon = math.sin(lon)
        cos_lon = math.cos(lon)

        e = -sin_lon * dx + cos_lon * dy
        n = -sin_lat * cos_lon * dx - sin_lat * sin_lon * dy + cos_lat * dz
        u = cos_lat * cos_lon * dx + cos_lat * sin_lon * dy + sin_lat * dz
        return (e, n, u)

    def elevation_deg(self, sat_ecef_km: Tuple[float, float, float]) -> float:
        """Elevation angle of satellite in degrees.

        Args:
            sat_ecef_km: Satellite position in ECEF (km).

        Returns:
            Elevation angle in degrees (positive above horizon).
        """
        e, n, u = self.enu_from_ecef(sat_ecef_km)
        horiz = math.hypot(e, n)
        return math.degrees(math.atan2(u, horiz))
