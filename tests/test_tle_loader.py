"""Tests for TLE loading."""
import pytest
from pathlib import Path
from satcore.tle_loader import load_tle


def test_load_valid_tle(tmp_path):
    """Test loading a valid TLE file."""
    tle_path = tmp_path / "test.tle"
    tle_path.write_text(
        "ISS (ZARYA)\n"
        "1 25544U 98067A   08264.51782528 -.00002182  00000-0 -11606-4 0  2927\n"
        "2 25544  51.6416 247.4627 0006703 130.5360 325.0288 15.72125391563537\n"
    )
    
    name, line1, line2 = load_tle(str(tle_path))
    
    assert name == "ISS (ZARYA)"
    assert line1.startswith("1 25544")
    assert line2.startswith("2 25544")


def test_load_tle_with_comments(tmp_path):
    """Test loading TLE with comment lines."""
    tle_path = tmp_path / "test.tle"
    tle_path.write_text(
        "# This is a comment\n"
        "ISS (ZARYA)\n"
        "# Another comment\n"
        "1 25544U 98067A   08264.51782528 -.00002182  00000-0 -11606-4 0  2927\n"
        "2 25544  51.6416 247.4627 0006703 130.5360 325.0288 15.72125391563537\n"
    )
    
    name, line1, line2 = load_tle(str(tle_path))
    assert name == "ISS (ZARYA)"


def test_load_tle_with_blank_lines(tmp_path):
    """Test loading TLE with blank lines."""
    tle_path = tmp_path / "test.tle"
    tle_path.write_text(
        "\n"
        "ISS (ZARYA)\n"
        "\n"
        "1 25544U 98067A   08264.51782528 -.00002182  00000-0 -11606-4 0  2927\n"
        "\n"
        "2 25544  51.6416 247.4627 0006703 130.5360 325.0288 15.72125391563537\n"
    )
    
    name, line1, line2 = load_tle(str(tle_path))
    assert name == "ISS (ZARYA)"


def test_load_tle_insufficient_lines(tmp_path):
    """Test that error is raised with insufficient lines."""
    tle_path = tmp_path / "test.tle"
    tle_path.write_text("ISS (ZARYA)\n")
    
    with pytest.raises(ValueError, match="must contain at least 3"):
        load_tle(str(tle_path))


def test_load_tle_invalid_format(tmp_path):
    """Test that error is raised with invalid TLE format."""
    tle_path = tmp_path / "test.tle"
    tle_path.write_text(
        "ISS (ZARYA)\n"
        "Not a valid line 1\n"
        "Not a valid line 2\n"
    )
    
    with pytest.raises(ValueError, match="must start with"):
        load_tle(str(tle_path))
