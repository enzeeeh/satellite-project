"""Integration tests for LEO satellite pass prediction.

Tests v1.0, v1.1, v1.2 pass prediction using real TLE data (AO-91, AO-95).
"""
from datetime import datetime, timedelta
import pytest
from src.core import GroundStation, detect_passes, load_tle, propagate_satellite


@pytest.fixture
def boulder_station():
    """Boulder, CO ground station for all tests."""
    return GroundStation(lat_deg=40.0, lon_deg=-105.0, alt_m=1600.0)


@pytest.fixture
def iss_like_orbit():
    """Low Earth Orbit parameters similar to ISS/AO-95."""
    # AO-95 TLE
    name, line1, line2 = load_tle("data/tle_leo/AO-95.txt")
    return name, line1, line2


@pytest.fixture
def ao91_orbit():
    """AO-91 amateur radio satellite."""
    name, line1, line2 = load_tle("data/tle_leo/AO-91.txt")
    return name, line1, line2


def test_ao95_tle_loads():
    """Verify AO-95 TLE loads without error."""
    name, line1, line2 = load_tle("data/tle_leo/AO-95.txt")
    assert "AO" in name or "FUNCUBE" in name
    assert line1.startswith("1 ")
    assert line2.startswith("2 ")


def test_ao91_tle_loads():
    """Verify AO-91 TLE loads without error."""
    name, line1, line2 = load_tle("data/tle_leo/AO-91.txt")
    assert "AO" in name or "FUNCUBE" in name
    assert line1.startswith("1 ")
    assert line2.startswith("2 ")


def test_ao95_propagation(iss_like_orbit):
    """Test propagation of AO-95 to known time."""
    name, line1, line2 = iss_like_orbit
    
    # Propagate to a specific time
    dt = datetime(2024, 12, 24, 0, 0, 0)
    pos_ecef, vel_ecef = propagate_satellite(line1, line2, dt)
    
    # Position should be ~500-600 km altitude (6378 + 600 = 6978 km radius)
    assert isinstance(pos_ecef, tuple)
    assert len(pos_ecef) == 3
    r = (pos_ecef[0]**2 + pos_ecef[1]**2 + pos_ecef[2]**2) ** 0.5
    assert 6378 < r < 7000, f"Radius {r} km is outside LEO range"


def test_ao91_propagation(ao91_orbit):
    """Test propagation of AO-91 to known time."""
    name, line1, line2 = ao91_orbit
    
    dt = datetime(2024, 12, 24, 0, 0, 0)
    pos_ecef, vel_ecef = propagate_satellite(line1, line2, dt)
    
    # Position should be ~500-600 km altitude (6378 + 600 = 6978 km radius)
    assert isinstance(pos_ecef, tuple)
    assert len(pos_ecef) == 3
    r = (pos_ecef[0]**2 + pos_ecef[1]**2 + pos_ecef[2]**2) ** 0.5
    assert 6378 < r < 7000, f"Radius {r} km is outside LEO range"


def test_ao95_pass_prediction_24h(iss_like_orbit, boulder_station):
    """Predict AO-95 passes over Boulder for 24 hours.
    
    LEO satellites at 40°N have 1-2 passes per day, so we expect at least 1.
    """
    name, line1, line2 = iss_like_orbit
    
    start = datetime(2024, 12, 24, 0, 0, 0)
    end = start + timedelta(hours=24)
    
    # Propagate every 5 minutes
    times = []
    elevations = []
    current = start
    while current <= end:
        times.append(current)
        pos_ecef, _ = propagate_satellite(line1, line2, current)
        elev = boulder_station.elevation_deg(pos_ecef)
        elevations.append(elev)
        current += timedelta(minutes=5)
    
    # Detect passes above 10° elevation
    passes = detect_passes(times, elevations, threshold_deg=10.0)
    
    # At 40°N latitude, expect at least 1 pass in 24h for LEO sat at 97° inclination
    assert len(passes) >= 1, f"Expected ≥1 pass, got {len(passes)}"
    
    # Each pass should have max elevation > threshold
    for p in passes:
        assert p.max_elevation_deg >= 10.0


def test_ao91_pass_prediction_24h(ao91_orbit, boulder_station):
    """Predict AO-91 passes over Boulder for 24 hours."""
    name, line1, line2 = ao91_orbit
    
    start = datetime(2024, 12, 24, 0, 0, 0)
    end = start + timedelta(hours=24)
    
    # Propagate every 5 minutes
    times = []
    elevations = []
    current = start
    while current <= end:
        times.append(current)
        pos_ecef, _ = propagate_satellite(line1, line2, current)
        elev = boulder_station.elevation_deg(pos_ecef)
        elevations.append(elev)
        current += timedelta(minutes=5)
    
    passes = detect_passes(times, elevations, threshold_deg=10.0)
    
    assert len(passes) >= 1, f"Expected ≥1 pass, got {len(passes)}"
    for p in passes:
        assert p.max_elevation_deg >= 10.0


def test_pass_event_attributes(iss_like_orbit, boulder_station):
    """Verify PassEvent has required attributes and sensible values."""
    name, line1, line2 = iss_like_orbit
    
    start = datetime(2024, 12, 24, 0, 0, 0)
    end = start + timedelta(hours=24)
    
    times = []
    elevations = []
    current = start
    while current <= end:
        times.append(current)
        pos_ecef, _ = propagate_satellite(line1, line2, current)
        elev = boulder_station.elevation_deg(pos_ecef)
        elevations.append(elev)
        current += timedelta(minutes=5)
    
    passes = detect_passes(times, elevations, threshold_deg=10.0)
    
    if passes:
        p = passes[0]
        # Verify event structure
        assert p.start_time < p.max_time < p.end_time
        assert p.max_elevation_deg >= 10.0
        # Duration should be reasonable (5-30 minutes for LEO)
        duration = (p.end_time - p.start_time).total_seconds() / 60
        assert 5 < duration < 30, f"Pass duration {duration}m seems unrealistic"


def test_different_stations_different_passes(iss_like_orbit):
    """Verify different stations predict different passes."""
    name, line1, line2 = iss_like_orbit
    
    # Boulder, CO
    boulder = GroundStation(lat_deg=40.0, lon_deg=-105.0, alt_m=1600.0)
    # San Francisco, CA
    sf = GroundStation(lat_deg=37.8, lon_deg=-122.4, alt_m=0.0)
    
    start = datetime(2024, 12, 24, 0, 0, 0)
    end = start + timedelta(hours=24)
    
    times = []
    elevations_boulder = []
    elevations_sf = []
    current = start
    while current <= end:
        times.append(current)
        pos_ecef, _ = propagate_satellite(line1, line2, current)
        elevations_boulder.append(boulder.elevation_deg(pos_ecef))
        elevations_sf.append(sf.elevation_deg(pos_ecef))
        current += timedelta(minutes=5)
    
    passes_boulder = detect_passes(times, elevations_boulder, threshold_deg=10.0)
    passes_sf = detect_passes(times, elevations_sf, threshold_deg=10.0)
    
    # Passes should differ between locations (but both should exist for LEO)
    # At minimum, max elevations should differ
    if passes_boulder and passes_sf:
        assert passes_boulder[0].max_elevation_deg != passes_sf[0].max_elevation_deg
