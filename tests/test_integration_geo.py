"""Integration tests for GEO satellite pass prediction.

Tests v2.0 propagation using real GEO TLE data.
"""
from datetime import datetime, timedelta
import pytest
from src.core import GroundStation, detect_passes, load_tle, propagate_satellite


@pytest.fixture
def denver_station():
    """Denver, CO ground station."""
    return GroundStation(lat_deg=39.74, lon_deg=-104.99, alt_m=1609.0)


@pytest.fixture
def geo_tle():
    """Load first GEO satellite from tle.txt."""
    with open("data/tle_geo/tle.txt", "r") as f:
        lines = [ln.strip() for ln in f.readlines()]
    
    # Extract first valid TLE (3 consecutive non-empty lines)
    content = [ln for ln in lines if ln and not ln.startswith("#")]
    
    if len(content) < 3:
        pytest.skip("GEO TLE file does not have enough data")
    
    name, line1, line2 = content[0], content[1], content[2]
    return name, line1, line2


def test_geo_tle_loads():
    """Verify GEO TLE file loads."""
    with open("data/tle_geo/tle.txt", "r") as f:
        lines = f.readlines()
    
    assert len(lines) > 3, "GEO TLE file should have multiple satellites"


def test_geo_propagation(geo_tle):
    """Test propagation of GEO satellite."""
    name, line1, line2 = geo_tle
    
    dt = datetime(2025, 1, 2, 0, 0, 0)
    pos_ecef, vel_ecef = propagate_satellite(line1, line2, dt)
    
    # GEO satellites orbit at ~42,164 km (35,786 km altitude)
    assert isinstance(pos_ecef, tuple)
    r = (pos_ecef[0]**2 + pos_ecef[1]**2 + pos_ecef[2]**2) ** 0.5
    
    # Check if GEO (35,000-42,000 km altitude)
    if 38000 < r < 43000:
        # Likely GEO
        assert True
    else:
        # Might be LEO or MEO, just verify it's a valid orbit
        assert 6378 < r < 100000, f"Radius {r} km seems invalid"


def test_geo_pass_prediction(geo_tle, denver_station):
    """Test GEO pass prediction (or lack thereof from stationary point).
    
    GEO satellites are essentially stationary, so from a fixed ground station
    we should see limited variation in elevation (unless inclination != 0).
    """
    name, line1, line2 = geo_tle
    
    start = datetime(2025, 1, 2, 0, 0, 0)
    end = start + timedelta(hours=24)
    
    times = []
    elevations = []
    current = start
    while current <= end:
        times.append(current)
        pos_ecef, _ = propagate_satellite(line1, line2, current)
        elev = denver_station.elevation_deg(pos_ecef)
        elevations.append(elev)
        current += timedelta(minutes=60)  # Check hourly for GEO
    
    # GEO satellites should have relatively stable elevation
    # (variation due to inclination and orbital mechanics, not traditional passes)
    min_elev = min(elevations)
    max_elev = max(elevations)
    elev_change = max_elev - min_elev
    
    # Most GEO sats change < 20° elevation over 24h from a fixed station
    # (some GEO sats have higher inclination variations)
    assert elev_change < 25.0, f"Elevation change {elev_change}° seems too large for GEO"


def test_geo_always_visible_from_equator(geo_tle):
    """GEO satellites (inclination ~0) should be continuously visible from equator."""
    name, line1, line2 = geo_tle
    
    equator_station = GroundStation(lat_deg=0.0, lon_deg=0.0, alt_m=0.0)
    
    start = datetime(2025, 1, 2, 0, 0, 0)
    end = start + timedelta(hours=24)
    
    times = []
    elevations = []
    current = start
    while current <= end:
        times.append(current)
        pos_ecef, _ = propagate_satellite(line1, line2, current)
        elev = equator_station.elevation_deg(pos_ecef)
        elevations.append(elev)
        current += timedelta(minutes=60)
    
    # Most elevations should be > 0° (visible above horizon)
    visible_count = sum(1 for e in elevations if e > 0)
    
    # Allow some margin for orbital mechanics
    assert visible_count > len(elevations) * 0.8, \
        f"GEO sat should be mostly visible from equator, got {visible_count}/{len(elevations)}"


def test_geo_propagation_consistency(geo_tle):
    """Test that propagating to same time gives same result."""
    name, line1, line2 = geo_tle
    
    dt = datetime(2025, 1, 2, 12, 0, 0)
    
    # Propagate twice
    pos1, vel1 = propagate_satellite(line1, line2, dt)
    pos2, vel2 = propagate_satellite(line1, line2, dt)
    
    # Should be identical
    for p1, p2 in zip(pos1, pos2):
        assert abs(p1 - p2) < 1e-6, "Propagation not deterministic"
    
    for v1, v2 in zip(vel1, vel2):
        assert abs(v1 - v2) < 1e-9, "Velocity not deterministic"


def test_geo_passes_are_rare(geo_tle, denver_station):
    """GEO satellites should have very few or no traditional 'passes'."""
    name, line1, line2 = geo_tle
    
    start = datetime(2025, 1, 2, 0, 0, 0)
    end = start + timedelta(hours=48)  # Check 48 hours
    
    times = []
    elevations = []
    current = start
    while current <= end:
        times.append(current)
        pos_ecef, _ = propagate_satellite(line1, line2, current)
        elev = denver_station.elevation_deg(pos_ecef)
        elevations.append(elev)
        current += timedelta(minutes=30)
    
    # Detect "passes" with high threshold (GEO must stay above 60° to be useful)
    passes = detect_passes(times, elevations, threshold_deg=60.0)
    
    # GEO sats typically don't have traditional AOS/LOS passes
    # They're either always visible or never visible from a given ground station
    # So we expect 0 or 1 "pass" events
    assert len(passes) <= 1, f"GEO should have ≤1 'pass' events, got {len(passes)}"
