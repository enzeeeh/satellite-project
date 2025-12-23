"""Tests for coordinate transforms."""
import pytest
import math
from datetime import datetime, timezone
from satcore.propagator import gmst_angle, teme_to_ecef


def test_gmst_angle_j2000():
    """Test GMST at J2000 epoch."""
    # J2000.0 = 2000-01-01 12:00:00 UTC
    j2000 = datetime(2000, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    gmst_rad = gmst_angle(j2000)
    
    # At J2000.0, GMST ≈ 280.46° ≈ 4.894 radians
    expected_rad = math.radians(280.46)
    assert abs(gmst_rad - expected_rad) < 0.05  # Within ~3°


def test_gmst_angle_increases_with_time():
    """Test that GMST increases over time."""
    t1 = datetime(2025, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
    t2 = datetime(2025, 1, 1, 6, 0, 0, tzinfo=timezone.utc)
    
    gmst1 = gmst_angle(t1)
    gmst2 = gmst_angle(t2)
    
    # GMST should increase (Earth rotates ~15°/hour)
    assert gmst2 > gmst1


def test_gmst_angle_wraps():
    """Test that GMST wraps to [0, 2π)."""
    t = datetime(2025, 6, 15, 18, 30, 0, tzinfo=timezone.utc)
    gmst_rad = gmst_angle(t)
    
    assert 0 <= gmst_rad < 2 * math.pi


def test_teme_to_ecef_identity_at_zero_gmst():
    """Test TEME→ECEF rotation with zero GMST."""
    r_teme = (7000.0, 0.0, 0.0)
    gmst_rad = 0.0
    
    r_ecef = teme_to_ecef(r_teme, gmst_rad)
    
    # No rotation: ECEF should match TEME
    assert abs(r_ecef[0] - 7000.0) < 1e-10
    assert abs(r_ecef[1]) < 1e-10
    assert abs(r_ecef[2]) < 1e-10


def test_teme_to_ecef_90_degree_rotation():
    """Test TEME→ECEF with 90° GMST rotation."""
    r_teme = (7000.0, 0.0, 0.0)
    gmst_rad = math.pi / 2  # 90°
    
    r_ecef = teme_to_ecef(r_teme, gmst_rad)
    
    # 90° Z-rotation: (x, y, z) → (x*cos(90) + y*sin(90), -x*sin(90) + y*cos(90), z)
    # (7000, 0, 0) → (0, -7000, 0)
    assert abs(r_ecef[0]) < 1e-10
    assert abs(r_ecef[1] - (-7000.0)) < 1e-10
    assert abs(r_ecef[2]) < 1e-10


def test_teme_to_ecef_180_degree_rotation():
    """Test TEME→ECEF with 180° GMST rotation."""
    r_teme = (7000.0, 0.0, 0.0)
    gmst_rad = math.pi  # 180°
    
    r_ecef = teme_to_ecef(r_teme, gmst_rad)
    
    # 180° rotation: x → -x, y → y
    assert abs(r_ecef[0] - (-7000.0)) < 1e-10
    assert abs(r_ecef[1]) < 1e-10
    assert abs(r_ecef[2]) < 1e-10


def test_teme_to_ecef_z_unchanged():
    """Test that Z-coordinate is unchanged by rotation."""
    r_teme = (7000.0, 1000.0, 3000.0)
    gmst_rad = math.radians(45.0)
    
    r_ecef = teme_to_ecef(r_teme, gmst_rad)
    
    # Z should be unchanged
    assert abs(r_ecef[2] - 3000.0) < 1e-10


def test_teme_to_ecef_magnitude_preserved():
    """Test that magnitude is preserved by rotation."""
    r_teme = (7000.0, 1000.0, 3000.0)
    gmst_rad = math.radians(123.4)
    
    r_ecef = teme_to_ecef(r_teme, gmst_rad)
    
    mag_teme = math.sqrt(sum(x**2 for x in r_teme))
    mag_ecef = math.sqrt(sum(x**2 for x in r_ecef))
    
    assert abs(mag_teme - mag_ecef) < 1e-10
