"""Tests for pass detection logic."""
import pytest
from datetime import datetime, timedelta
from satcore.pass_detector import detect_passes, PassEvent


def test_detect_simple_pass():
    """Test detection of a single simple pass."""
    # Create a simple elevation profile: rises above 10°, peaks, then falls
    start = datetime(2025, 1, 1, 0, 0, 0)
    times = [start + timedelta(minutes=i) for i in range(10)]
    elevations = [5.0, 8.0, 12.0, 18.0, 22.0, 18.0, 12.0, 8.0, 5.0, 2.0]
    
    passes = detect_passes(times, elevations, threshold_deg=10.0)
    
    assert len(passes) == 1
    assert passes[0].max_elevation_deg == 22.0


def test_detect_no_passes():
    """Test when no passes exceed threshold."""
    start = datetime(2025, 1, 1, 0, 0, 0)
    times = [start + timedelta(minutes=i) for i in range(10)]
    elevations = [2.0, 3.0, 5.0, 7.0, 8.0, 7.0, 5.0, 3.0, 2.0, 1.0]
    
    passes = detect_passes(times, elevations, threshold_deg=10.0)
    
    assert len(passes) == 0


def test_detect_multiple_passes():
    """Test detection of multiple passes."""
    start = datetime(2025, 1, 1, 0, 0, 0)
    # Create exactly 22 time points
    times = [start + timedelta(minutes=i) for i in range(22)]
    # Two passes: first peaks at 20°, second peaks at 15° (total 22 points)
    elevations = [
        5.0, 8.0, 12.0, 20.0, 12.0, 8.0, 5.0,  # First pass (7 points)
        2.0, 1.0, 2.0, 5.0, 8.0,  # Gap (5 points)
        12.0, 15.0, 12.0, 8.0, 5.0, 2.0, 1.0, 0.0, 0.0, 0.0  # Second pass + trailing (10 points)
    ]
    
    assert len(times) == len(elevations), f"Length mismatch: {len(times)} times vs {len(elevations)} elevations"
    
    passes = detect_passes(times, elevations, threshold_deg=10.0)
    
    assert len(passes) == 2
    assert passes[0].max_elevation_deg == 20.0
    assert passes[1].max_elevation_deg == 15.0


def test_pass_starts_above_threshold():
    """Test pass that starts above threshold."""
    start = datetime(2025, 1, 1, 0, 0, 0)
    times = [start + timedelta(minutes=i) for i in range(10)]
    elevations = [15.0, 20.0, 18.0, 12.0, 8.0, 5.0, 2.0, 1.0, 0.0, 0.0]
    
    passes = detect_passes(times, elevations, threshold_deg=10.0)
    
    assert len(passes) == 1
    assert passes[0].start_time == times[0]
    assert passes[0].max_elevation_deg == 20.0


def test_pass_ends_above_threshold():
    """Test pass that continues past final sample."""
    start = datetime(2025, 1, 1, 0, 0, 0)
    times = [start + timedelta(minutes=i) for i in range(10)]
    elevations = [5.0, 8.0, 12.0, 18.0, 22.0, 25.0, 28.0, 30.0, 32.0, 35.0]
    
    passes = detect_passes(times, elevations, threshold_deg=10.0)
    
    assert len(passes) == 1
    assert passes[0].end_time == times[-1]
    assert passes[0].max_elevation_deg == 35.0


def test_threshold_interpolation():
    """Test that AOS/LOS times are interpolated."""
    start = datetime(2025, 1, 1, 0, 0, 0)
    times = [start + timedelta(minutes=i) for i in range(5)]
    # Crosses threshold between index 0-1 and 3-4
    elevations = [8.0, 12.0, 15.0, 12.0, 8.0]
    
    passes = detect_passes(times, elevations, threshold_deg=10.0)
    
    assert len(passes) == 1
    # AOS should be between times[0] and times[1]
    assert times[0] < passes[0].start_time < times[1]
    # LOS should be between times[3] and times[4]
    assert times[3] < passes[0].end_time < times[4]


def test_empty_input():
    """Test with empty input."""
    passes = detect_passes([], [], threshold_deg=10.0)
    assert len(passes) == 0


def test_mismatched_lengths():
    """Test with mismatched input lengths."""
    start = datetime(2025, 1, 1, 0, 0, 0)
    times = [start + timedelta(minutes=i) for i in range(5)]
    elevations = [8.0, 12.0, 15.0]  # Only 3 values
    
    passes = detect_passes(times, elevations, threshold_deg=10.0)
    assert len(passes) == 0
