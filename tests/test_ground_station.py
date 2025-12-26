"""Tests for ground station geometry."""
import pytest
import math
from src.core.ground_station import GroundStation


def test_ground_station_properties():
    """Test GroundStation property conversions."""
    gs = GroundStation(lat_deg=40.0, lon_deg=-105.0, alt_m=1600.0)
    
    assert abs(gs.lat_rad - math.radians(40.0)) < 1e-10
    assert abs(gs.lon_rad - math.radians(-105.0)) < 1e-10
    assert abs(gs.alt_km - 1.6) < 1e-10


def test_ground_station_ecef_conversion():
    """Test ECEF position computation."""
    gs = GroundStation(lat_deg=0.0, lon_deg=0.0, alt_m=0.0)
    x, y, z = gs.ecef_km()
    
    # At equator, prime meridian, sea level: x ≈ 6378.137 km, y ≈ 0, z ≈ 0
    assert abs(x - 6378.137) < 0.01
    assert abs(y) < 0.01
    assert abs(z) < 0.01


def test_ground_station_ecef_pole():
    """Test ECEF at north pole."""
    gs = GroundStation(lat_deg=90.0, lon_deg=0.0, alt_m=0.0)
    x, y, z = gs.ecef_km()
    
    # At north pole: x ≈ 0, y ≈ 0, z ≈ 6356.752 km (polar radius)
    assert abs(x) < 0.01
    assert abs(y) < 0.01
    assert abs(z - 6356.752) < 0.01


def test_elevation_angle_overhead():
    """Test elevation when satellite is directly overhead."""
    gs = GroundStation(lat_deg=0.0, lon_deg=0.0, alt_m=0.0)
    
    # Satellite 400 km directly above station (radially outward from center)
    # Station at (6378.137, 0, 0), satellite at (6378.137 + 400, 0, 0)
    sat_ecef = (6378.137 + 400.0, 0.0, 0.0)
    elevation = gs.elevation_deg(sat_ecef)
    
    # Should be near 90° (directly overhead along radial direction)
    assert elevation > 85.0


def test_elevation_angle_on_horizon():
    """Test elevation angle calculation for satellite on horizon (tangent to Earth surface)."""
    gs = GroundStation(lat_deg=0.0, lon_deg=0.0, alt_m=0.0)
    
    # Satellite at 400 km altitude on the horizon
    # For a spherical Earth approximation:
    # - Observer at radius R = 6378.137 km
    # - Satellite at radius r = R + 400 km
    # - Horizon angle: arccos(R/r) from zenith, measured from Earth center
    # - For tangent to horizon: theta = arccos(6378.137 / 6778.137) ≈ 19.86°
    # - Place satellite at this angular distance from observer
    R = 6378.137
    h = 400.0
    r = R + h
    
    # Horizon angle from Earth center
    horizon_angle_rad = math.acos(R / r)
    horizon_angle_deg = math.degrees(horizon_angle_rad)
    
    # Place satellite on equator at this angular distance
    sat_lat = 0.0
    sat_lon = horizon_angle_deg
    sat_alt = h
    
    # Convert to ECEF
    sat_lat_rad = math.radians(sat_lat)
    sat_lon_rad = math.radians(sat_lon)
    a = 6378.137
    f = 1 / 298.257223563
    e2 = 2 * f - f * f
    N = a / math.sqrt(1 - e2 * math.sin(sat_lat_rad) ** 2)
    sat_ecef_x = (N + sat_alt) * math.cos(sat_lat_rad) * math.cos(sat_lon_rad)
    sat_ecef_y = (N + sat_alt) * math.cos(sat_lat_rad) * math.sin(sat_lon_rad)
    sat_ecef_z = (N * (1 - e2) + sat_alt) * math.sin(sat_lat_rad)
    sat_ecef = (sat_ecef_x, sat_ecef_y, sat_ecef_z)
    
    elevation = gs.elevation_deg(sat_ecef)
    
    # Elevation should be close to 0° (within ±3° due to WGS84 vs spherical approximation)
    assert abs(elevation) < 3.0, f"Expected elevation near 0°, got {elevation}°"


def test_elevation_angle_below_horizon():
    """Test elevation when satellite is below horizon."""
    gs = GroundStation(lat_deg=0.0, lon_deg=0.0, alt_m=0.0)
    
    # Satellite on opposite side of Earth
    sat_ecef = (-6378.137, 0.0, 0.0)
    elevation = gs.elevation_deg(sat_ecef)
    
    # Should be negative (below horizon)
    assert elevation < 0.0
