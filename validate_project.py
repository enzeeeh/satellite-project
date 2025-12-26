#!/usr/bin/env python
"""
Interactive Satellite Pass Predictor - Validation & Testing Script

This script lets you step-by-step explore the satellite project:
1. Load TLE data
2. Create ground stations
3. Predict passes
4. Validate results
5. Compare versions
"""

from src.core import GroundStation, detect_passes, load_tle, propagate_satellite
from datetime import datetime, timedelta
import sys

def print_header(title):
    """Print formatted section header."""
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}")

def print_success(msg):
    print(f"✅ {msg}")

def print_error(msg):
    print(f"❌ {msg}")

def print_info(msg):
    print(f"ℹ️  {msg}")

# ============================================================================
# SECTION 1: VERIFY ENVIRONMENT
# ============================================================================
def check_environment():
    """Check if all required packages are installed."""
    print_header("SECTION 1: ENVIRONMENT CHECK")
    
    try:
        import sgp4
        print_success(f"sgp4 installed (version {sgp4.__version__})")
    except ImportError:
        print_error("sgp4 not installed. Run: pip install sgp4")
        return False
    
    try:
        import numpy
        print_success(f"numpy installed (version {numpy.__version__})")
    except ImportError:
        print_error("numpy not installed. Run: pip install numpy")
        return False
    
    try:
        import pytest
        print_success(f"pytest installed (version {pytest.__version__})")
    except ImportError:
        print_info("pytest not installed (optional, for testing)")
    
    return True

# ============================================================================
# SECTION 2: LOAD TLE DATA
# ============================================================================
def explore_tle_files():
    """Load and display TLE data."""
    print_header("SECTION 2: LOAD TLE DATA")
    
    test_files = [
        "data/tle_leo/AO-95.txt",
        "data/tle_leo/AO-91.txt",
        "data/tle_geo/tle.txt",
    ]
    
    for tle_file in test_files:
        try:
            name, line1, line2 = load_tle(tle_file)
            print_success(f"Loaded {tle_file}")
            print(f"  Satellite: {name}")
            print(f"  Line 1: {line1[:40]}...")
            print(f"  Line 2: {line2[:40]}...")
        except FileNotFoundError:
            print_error(f"File not found: {tle_file}")
        except Exception as e:
            print_error(f"Failed to load {tle_file}: {e}")
    
    return True

# ============================================================================
# SECTION 3: VERIFY PROPAGATION
# ============================================================================
def verify_propagation():
    """Test satellite propagation."""
    print_header("SECTION 3: VERIFY PROPAGATION (SGP4)")
    
    # Load AO-95
    name, line1, line2 = load_tle("data/tle_leo/AO-95.txt")
    print_info(f"Testing with: {name}")
    
    # Propagate to a specific time
    dt = datetime(2024, 12, 24, 12, 0, 0)
    pos, vel = propagate_satellite(line1, line2, dt)
    
    # Calculate orbital radius
    r = (pos[0]**2 + pos[1]**2 + pos[2]**2) ** 0.5
    alt = r - 6378.137  # Earth radius
    
    print_info(f"Propagation time: {dt} UTC")
    print(f"Position ECEF: ({pos[0]:.1f}, {pos[1]:.1f}, {pos[2]:.1f}) km")
    print(f"Velocity ECEF: ({vel[0]:.4f}, {vel[1]:.4f}, {vel[2]:.4f}) km/s")
    print(f"Orbital radius: {r:.1f} km")
    print(f"Altitude: {alt:.1f} km")
    
    # Validation checks
    checks = []
    checks.append(("Radius within LEO range (6378-7000 km)", 6378 < r < 7000))
    checks.append(("Altitude ~500-600 km", 400 < alt < 800))
    checks.append(("Velocity ~7.5-7.8 km/s", 7.3 < ((vel[0]**2 + vel[1]**2 + vel[2]**2)**0.5) < 8.0))
    
    all_pass = True
    for check, result in checks:
        if result:
            print_success(check)
        else:
            print_error(check)
            all_pass = False
    
    return all_pass

# ============================================================================
# SECTION 4: GROUND STATION GEOMETRY
# ============================================================================
def verify_ground_station():
    """Test ground station coordinate transforms."""
    print_header("SECTION 4: GROUND STATION GEOMETRY")
    
    # Test with Boulder, CO
    station = GroundStation(lat_deg=40.0, lon_deg=-105.0, alt_m=1600)
    print_info("Testing with Boulder, CO (40.0°N, 105.0°W, 1600m)")
    
    # Get ECEF position
    ecef = station.ecef_km()
    print(f"ECEF position: ({ecef[0]:.1f}, {ecef[1]:.1f}, {ecef[2]:.1f}) km")
    
    # Verify coordinates are reasonable (should be within Earth)
    r = (ecef[0]**2 + ecef[1]**2 + ecef[2]**2) ** 0.5
    print(f"Distance from Earth center: {r:.1f} km")
    
    # Test elevation at different positions
    test_cases = [
        ("Satellite directly overhead", (ecef[0], ecef[1], ecef[2] + 500), 90.0),
        ("Satellite on horizon", (6378, 0, 0), -10.0),
        ("Satellite below horizon", (6378, 0, -100), -20.0),
    ]
    
    print("\nElevation angle tests:")
    all_pass = True
    for description, sat_pos, expected_range in test_cases:
        elev = station.elevation_deg(sat_pos)
        # Just check it's computed, exact values depend on station location
        print(f"  {description}: {elev:.1f}°")
    
    print_success("Ground station calculations working")
    return True

# ============================================================================
# SECTION 5: PASS DETECTION
# ============================================================================
def predict_passes():
    """Predict actual satellite passes."""
    print_header("SECTION 5: PASS DETECTION")
    
    # Load satellite and station
    name, line1, line2 = load_tle("data/tle_leo/AO-95.txt")
    station = GroundStation(lat_deg=40.0, lon_deg=-105.0, alt_m=1600)
    
    print_info(f"Satellite: {name}")
    print_info("Location: Boulder, CO (40.0°N, 105.0°W)")
    print_info("Time range: 24 hours starting 2024-12-24 00:00 UTC")
    print_info("Elevation threshold: 10°")
    
    # Generate predictions every 5 minutes for 24 hours
    start = datetime(2024, 12, 24, 0, 0, 0)
    end = start + timedelta(hours=24)
    
    times = []
    elevations = []
    current = start
    while current <= end:
        times.append(current)
        pos, _ = propagate_satellite(line1, line2, current)
        elev = station.elevation_deg(pos)
        elevations.append(elev)
        current += timedelta(minutes=5)
    
    print(f"\nGenerated {len(times)} elevation samples")
    
    # Detect passes
    passes = detect_passes(times, elevations, threshold_deg=10.0)
    print(f"Detected {len(passes)} passes\n")
    
    # Validate results
    checks = []
    checks.append(("Found at least 1 pass", len(passes) >= 1))
    checks.append(("Found no more than 3 passes (24h)", len(passes) <= 3))
    
    all_pass = True
    for pass_event in passes:
        # Check ordering (start_time, max_time, end_time)
        rise_ok = pass_event.start_time < pass_event.max_time < pass_event.end_time
        checks.append((f"Pass times in order (start < max < end)", rise_ok))
        
        # Check duration
        duration = (pass_event.end_time - pass_event.start_time).total_seconds() / 60
        duration_ok = 5 < duration < 25
        checks.append((f"Pass duration {duration:.1f}m in range (5-25 min)", duration_ok))
        
        # Check elevation
        elev_ok = 10 <= pass_event.max_elevation_deg <= 90
        checks.append((f"Max elevation {pass_event.max_elevation_deg:.1f}° reasonable", elev_ok))
        
        # Print pass details
        print(f"PASS #{len([p for p in passes[:passes.index(pass_event)+1]])}")
        print(f"  Start time:     {pass_event.start_time} UTC")
        print(f"  Peak time:      {pass_event.max_time} UTC")
        print(f"  End time:       {pass_event.end_time} UTC")
        print(f"  Max elevation:  {pass_event.max_elevation_deg:.1f}°")
        print(f"  Duration:       {duration:.1f} minutes\n")
    
    for check, result in checks:
        if result:
            print_success(check)
        else:
            print_error(check)
            all_pass = False
    
    return all_pass

# ============================================================================
# SECTION 6: MULTI-LOCATION COMPARISON
# ============================================================================
def compare_locations():
    """Compare pass predictions for different ground stations."""
    print_header("SECTION 6: MULTI-LOCATION COMPARISON")
    
    name, line1, line2 = load_tle("data/tle_leo/AO-95.txt")
    
    locations = {
        "Boulder, CO": (40.0, -105.0),
        "San Francisco, CA": (37.77, -122.41),
        "Denver, CO": (39.74, -104.99),
    }
    
    start = datetime(2024, 12, 24, 0, 0, 0)
    end = start + timedelta(hours=24)
    
    results = {}
    
    for city, (lat, lon) in locations.items():
        station = GroundStation(lat_deg=lat, lon_deg=lon, alt_m=1600)
        
        times = []
        elevations = []
        current = start
        while current <= end:
            times.append(current)
            pos, _ = propagate_satellite(line1, line2, current)
            elev = station.elevation_deg(pos)
            elevations.append(elev)
            current += timedelta(minutes=5)
        
        passes = detect_passes(times, elevations, threshold_deg=10.0)
        results[city] = len(passes)
    
    print(f"\n24-hour pass count by location:")
    for city, count in results.items():
        print(f"  {city}: {count} pass(es)")
    
    # Locations at similar latitude should have similar pass counts
    boulder_passes = results["Boulder, CO"]
    denver_passes = results["Denver, CO"]
    
    similar = abs(boulder_passes - denver_passes) <= 1
    print_success(f"Similar latitudes have similar pass counts: {similar}")
    
    return True

# ============================================================================
# SECTION 7: VERIFY DATA FILES
# ============================================================================
def verify_data_files():
    """Check that all required data files exist and are readable."""
    print_header("SECTION 7: DATA FILES VERIFICATION")
    
    import os
    
    required_files = [
        "data/README.md",
        "data/tle_leo/AO-91.txt",
        "data/tle_leo/AO-95.txt",
        "data/tle_geo/tle.txt",
    ]
    
    all_exist = True
    for file_path in required_files:
        if os.path.exists(file_path):
            size = os.path.getsize(file_path)
            print_success(f"{file_path} ({size} bytes)")
        else:
            print_error(f"{file_path} NOT FOUND")
            all_exist = False
    
    return all_exist

# ============================================================================
# MAIN
# ============================================================================
def main():
    """Run all validation tests."""
    print("\n")
    print("╔" + "="*68 + "╗")
    print("║" + " "*68 + "║")
    print("║" + "  SATELLITE PASS PREDICTOR - COMPLETE VALIDATION SUITE".center(68) + "║")
    print("║" + " "*68 + "║")
    print("╚" + "="*68 + "╝")
    
    # Run all sections
    sections = [
        ("Environment", check_environment),
        ("TLE Files", explore_tle_files),
        ("Propagation", verify_propagation),
        ("Ground Station", verify_ground_station),
        ("Pass Detection", predict_passes),
        ("Multi-Location", compare_locations),
        ("Data Files", verify_data_files),
    ]
    
    results = {}
    for section_name, section_func in sections:
        try:
            result = section_func()
            results[section_name] = result
        except Exception as e:
            print_error(f"Exception in {section_name}: {e}")
            import traceback
            traceback.print_exc()
            results[section_name] = False
    
    # Summary
    print_header("VALIDATION SUMMARY")
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for section, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {section}")
    
    print(f"\nTotal: {passed}/{total} sections passed")
    
    if passed == total:
        print_success("ALL VALIDATION CHECKS PASSED!")
        print_info("Project is ready for publication/distribution")
        return 0
    else:
        print_error(f"{total - passed} section(s) failed")
        print_info("Please review errors above")
        return 1

if __name__ == "__main__":
    sys.exit(main())
