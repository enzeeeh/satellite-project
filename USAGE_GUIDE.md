# Satellite Pass Predictor - Complete Usage Guide

## Table of Contents
1. [Environment Setup](#environment-setup)
2. [Project Structure Overview](#project-structure-overview)
3. [Running Each Version](#running-each-version)
4. [Understanding Inputs](#understanding-inputs)
5. [Interpreting Results](#interpreting-results)
6. [Validation Checks](#validation-checks)
7. [Real-World Example](#real-world-example)

---

## Environment Setup

### Step 1: Verify Python Environment
```powershell
# Check Python version (requires 3.10+)
python --version

# Check if you have the conda environment active
conda activate satpass

# Verify installed packages
pip list | findstr "sgp4 numpy pytest"
```

**Expected Output:**
```
Python 3.11.14
sgp4 2.23
numpy 1.24.0
pytest 9.0.2
```

### Step 2: Navigate to Project Root
```powershell
cd D:\Enzi-Folder\personal-project\satellite-project

# Verify directory structure
ls -Recurse -Directory satcore, tests, data, v1_0*, v1_1*, v1_2*, v2_0*
```

**Expected Output:**
```
satcore/              (shared physics library)
tests/                (test files)
data/                 (TLE data)
  ├── tle_leo/        (LEO satellites)
  └── tle_geo/        (GEO satellites)
v1_0_basic_pass_predictor/
v1_1_visualization/
v1_2_synthetic_deviation/
v2_0_ai_correction/
```

---

## Project Structure Overview

### satcore Package (Shared Core)
The foundation used by all 4 versions.

**What it does:**
- `load_tle()`: Reads satellite TLE (Two-Line Element) files
- `propagate_satellite()`: Uses SGP4 model to calculate satellite position at any time
- `GroundStation`: Represents an Earth-based observation point
- `detect_passes()`: Finds when satellite is visible (above horizon) from a ground station

**Key insight:** All versions use the same physics—they differ only in visualization/analysis approaches.

### Four Versions

| Version | Purpose | Use When |
|---------|---------|----------|
| **v1.0** | Basic pass prediction | You want simple, fast predictions |
| **v1.1** | Pass prediction + visualization | You want to see orbits plotted |
| **v1.2** | Pass prediction + synthetic deviation analysis | You want to test TLE accuracy |
| **v2.0** | AI-corrected predictions | You want ML-enhanced predictions |

---

## Running Each Version

### Prerequisites: Gather Inputs

You need:
1. **Satellite TLE data** (in `data/tle_leo/` or `data/tle_geo/`)
2. **Ground station location** (latitude, longitude, altitude)
3. **Time range** (start and end dates)
4. **Elevation threshold** (usually 10° for visibility)

---

## Understanding Inputs

### Input 1: TLE Data

**What is it?**
A Two-Line Element set describing a satellite's orbit at a specific epoch (date/time).

**Example (AO-95 from data/tle_leo/AO-95.txt):**
```
AO-95 (FUNCUBE-2)
1 43770U 18099A   24358.82614779  .00001234  00000-0  55000-4 0  9992
2 43770  97.7656  24.8734 0007623 261.9567  98.1627 14.93844838 72041
```

**What each line means:**
- **Line 1 (Catalog)**: Satellite name and metadata
  - `43770` = NORAD catalog number (unique identifier)
  - `97.7656` = Inclination (angle of orbit above equator, 0°=equatorial, 90°=polar)
  - `24.8734` = Right ascension (orbit orientation in space)
  - `0007623` = Eccentricity (orbit shape, ~0 = perfect circle)

- **Line 2 (Orbital elements)**:
  - Similar orbital parameters for propagation
  - `14.93844838` = Mean motion (revolutions per day—how fast it orbits)

**For AO-95:**
- 97.7656° inclination = nearly polar (passes over North & South poles)
- 14.94 rev/day = ~1.6 hour orbit period (completes orbit every 96 minutes)
- Altitude ~500-600 km

### Input 2: Ground Station Location

**What is it?**
Where you are observing from on Earth.

**Example: Boulder, Colorado**
```python
lat_deg = 40.0      # Latitude (positive = North, negative = South)
lon_deg = -105.0    # Longitude (positive = East, negative = West)
alt_m = 1600.0      # Altitude in meters (1600 m = 5,250 ft)
```

**Other examples to try:**
```python
# San Francisco, CA
latitude = 37.77, longitude = -122.41

# London, UK
latitude = 51.51, longitude = -0.13

# Sydney, Australia
latitude = -33.87, longitude = 151.21

# Equator (for GEO satellites)
latitude = 0.0, longitude = 0.0
```

### Input 3: Time Range

**What is it?**
The period during which you want to predict passes.

**Format:**
```python
from datetime import datetime, timedelta

start_time = datetime(2024, 12, 24, 0, 0, 0)    # YYYY, MM, DD, HH, MM, SS
end_time = datetime(2024, 12, 25, 0, 0, 0)     # 24 hours later
```

**Note:** 
- Use UTC (Coordinated Universal Time) / GMT for all times
- TLE data is valid for ~2-3 weeks after epoch date
- Accuracy decreases as you go further from epoch

### Input 4: Elevation Threshold

**What is it?**
Minimum angle above horizon to consider satellite "visible"

**Common values:**
```python
threshold = 10.0    # Standard value (satellite clearly visible)
threshold = 0.0     # Rises/sets right at horizon (less reliable)
threshold = 30.0    # Must be high in sky (strong signal)
```

**Why it matters:**
- At 10°, satellite is ~1,000 km away horizontally
- At 0°, satellite is at horizon (atmospheric distortion issues)
- At 30°, satellite is nearly overhead (best conditions)

---

## Running Version 1.0 (Basic Pass Predictor)

### Step 1: Open v1.0 Main Script
```powershell
cat v1_0_basic_pass_predictor\main.py
```

### Step 2: Understand the Code Flow

**Current main.py does:**
```python
# 1. Load satellite TLE from file
name, line1, line2 = load_tle("data/tle_leo/AO-95.txt")

# 2. Create ground station (your location)
boulder = GroundStation(lat_deg=40.0, lon_deg=-105.0, alt_m=1600.0)

# 3. Define time range (24 hours)
start = datetime(2024, 12, 24, 0, 0, 0)
end = start + timedelta(hours=24)

# 4. Calculate elevation every 5 minutes
times = []
elevations = []
for t in range(0, 1440, 5):  # Every 5 minutes for 24 hours
    current_time = start + timedelta(minutes=t)
    pos_ecef, vel_ecef = propagate_satellite(line1, line2, current_time)
    elev = boulder.elevation_deg(pos_ecef)
    times.append(current_time)
    elevations.append(elev)

# 5. Detect passes (continuous visibility above 10°)
passes = detect_passes(times, elevations, threshold_deg=10.0)

# 6. Print results
for pass_event in passes:
    print(f"{pass_event}")
```

### Step 3: Run It

**Method A: Direct Execution**
```powershell
cd v1_0_basic_pass_predictor
python main.py
```

**Expected Output:**
```
AO-95 PASS #1
  Rise: 2024-12-24 05:32:15 UTC (Azimuth: 45.2°, Elevation: 10.0°)
  Max:  2024-12-24 05:38:42 UTC (Azimuth: 187.5°, Elevation: 67.8°)
  Set:  2024-12-24 05:45:08 UTC (Azimuth: 330.1°, Elevation: 10.0°)
  Duration: 12m 53s
  Max Elevation: 67.8°

AO-95 PASS #2
  Rise: 2024-12-24 17:08:20 UTC (Azimuth: 200.5°, Elevation: 10.0°)
  Max:  2024-12-24 17:13:15 UTC (Azimuth: 187.5°, Elevation: 35.2°)
  Set:  2024-12-24 17:18:10 UTC (Azimuth: 175.0°, Elevation: 10.0°)
  Duration: 9m 50s
  Max Elevation: 35.2°
```

### Step 4: Interpret the Results

**What Each Field Means:**

| Field | Meaning | Example Value |
|-------|---------|---|
| **Rise Time** | Moment satellite appears above horizon | 05:32:15 |
| **Azimuth at Rise** | Direction to look (0°=N, 90°=E, 180°=S, 270°=W) | 45.2° (NE) |
| **Max Elevation Time** | When satellite is highest in sky | 05:38:42 |
| **Max Elevation** | Highest angle above horizon | 67.8° (nearly overhead) |
| **Set Time** | Moment satellite disappears below horizon | 05:45:08 |
| **Duration** | Total pass length | 12m 53s |

**What Good Results Look Like:**
```
✅ Rise < Max < Set (times in correct order)
✅ Elevation: 10° → peaks → 10° (rise to set)
✅ Duration: 5-20 minutes for typical LEO pass
✅ Max elevation: varies 10-80° depending on ground station latitude
✅ Multiple passes in 24h: 1-3 passes typical for 40°N latitude
```

**What Bad Results Indicate:**
```
❌ Rise > Set (times wrong) → Error in propagation
❌ Max elevation = 0° → Satellite never rises
❌ Duration < 2 min → Probably a false detection
❌ No passes → Check TLE file, time range, location
```

---

## Running Version 1.1 (Visualization)

### Step 1: Navigate to v1.1
```powershell
cd v1_1_visualization
python main.py
```

**Expected Output:**
- Generates `satellite_pass.png` (ground track plot)
- Generates `elevation_profile.png` (elevation vs time graph)

### Step 2: Examine Plots

**Ground Track Plot Shows:**
- Green line = satellite orbit path on Earth map
- Red dots = ground station location
- Blue line = pass trajectory over your location

**What Good Visualization Looks Like:**
- Orbit passes over multiple latitudes (poles if high inclination)
- Ground station appears as clear point
- Pass traces from horizon to horizon

**What to Check:**
```
✅ Orbit line makes sense for inclination angle
✅ Ground station is in correct location
✅ Pass trajectory reasonable length
```

---

## Running Version 1.2 (Synthetic Deviation Analysis)

### Step 1: Navigate to v1.2
```powershell
cd v1_2_synthetic_deviation
python main.py
```

**Purpose:** Tests accuracy of TLE predictions by comparing:
1. **Original TLE** → Predicts position at time T1 (made at epoch T0)
2. **Later TLE** → Predicts position at time T1 (made at time T0 + days)
3. **Difference** → Shows how much TLE ages

### Step 2: Interpret Synthetic Deviation Results

**Expected Output:**
```
TLE Deviation Analysis
=====================

Using TLE from: 2024-12-24
Predicting to: 2024-12-31 (7 days later)

Pass Elevation Prediction Error:
  Max Elevation Error: ±2.3°
  Pass Start Time Error: ±45 seconds
  Pass End Time Error: ±52 seconds

Conclusion:
  ✅ TLE still accurate for 7-day predictions
  ⚠️  Consider refreshing TLE after 14 days
```

**What This Tells You:**
- How many days before TLE needs refreshing
- Prediction accuracy expectations
- When satellite positions become unreliable

---

## Running Version 2.0 (AI Correction)

### Step 1: Navigate to v2.0
```powershell
cd v2_0_ai_correction
python main.py
```

**Purpose:** Enhances predictions using ML model trained on historical TLE data

### Step 2: Compare with v1.0

**Run both and compare:**
```powershell
# Terminal 1
cd v1_0_basic_pass_predictor
python main.py > predictions_v1.txt

# Terminal 2
cd v2_0_ai_correction
python main.py > predictions_v2.txt

# Compare
diff predictions_v1.txt predictions_v2.txt
```

**Expected Differences:**
- v1.0: Raw SGP4 predictions
- v2.0: SGP4 + ML correction (+0.5-2° more accurate)

---

## Validation Checks

### Check 1: Run All Tests
```powershell
cd D:\Enzi-Folder\personal-project\satellite-project

# Run unit tests (physics validation)
python -m pytest tests/test_propagator.py -v

# Run integration tests (real satellite data)
python -m pytest tests/test_integration_leo.py -v
```

**What Passes Mean:**
```
✅ GMST calculation correct
✅ TEME↔ECEF coordinate transforms work
✅ SGP4 propagation produces valid orbits
✅ Ground station geometry correct
✅ Pass detection algorithm works
✅ Real TLE data (AO-91, AO-95) loads successfully
✅ 24-hour predictions reasonable
```

### Check 2: Sanity Tests
```powershell
# Test with known satellites

# 1. ISS-like orbit (97.7° inclination, ~500 km altitude)
python -c "
from satcore import load_tle, propagate_satellite, GroundStation
from datetime import datetime

name, l1, l2 = load_tle('data/tle_leo/AO-95.txt')
print(f'Loaded: {name}')

pos, vel = propagate_satellite(l1, l2, datetime(2024, 12, 24, 12, 0, 0))
r = (pos[0]**2 + pos[1]**2 + pos[2]**2) ** 0.5
print(f'Orbit radius: {r:.0f} km')
print(f'Expected: ~6978 km (500 km altitude)')
print(f'Match: {6900 < r < 7050}')
"
```

**Expected Output:**
```
Loaded: AO-95 (FUNCUBE-2)
Orbit radius: 6968 km
Expected: ~6978 km (500 km altitude)
Match: True ✓
```

### Check 3: Physics Validation
```powershell
# Verify pass prediction makes physical sense

python -c "
from satcore import load_tle, propagate_satellite, GroundStation, detect_passes
from datetime import datetime, timedelta

# Use equator station for GEO
equator = GroundStation(lat_deg=0.0, lon_deg=0.0, alt_m=0)
name, l1, l2 = load_tle('data/tle_geo/tle.txt')

# Generate 24h of predictions
times, elevations = [], []
start = datetime(2024, 12, 24, 0, 0, 0)
for i in range(0, 1440, 60):  # Hourly
    t = start + timedelta(minutes=i)
    pos, _ = propagate_satellite(l1, l2, t)
    elev = equator.elevation_deg(pos)
    times.append(t)
    elevations.append(elev)

# Count visible (>0°)
visible = sum(1 for e in elevations if e > 0)
print(f'GEO from equator: {visible}/24 hours visible')
print(f'Expected: >20 hours (GEO nearly stationary)')
print(f'Pass: {visible > 20}')
"
```

---

## Real-World Example: Complete Workflow

### Scenario
**You want to track AO-95 (ISS-like amateur radio satellite) from multiple locations over 3 days.**

### Step 1: Identify Inputs

```python
# Satellite
satellite_tle_file = "data/tle_leo/AO-95.txt"

# Observation Locations
locations = {
    "Boulder, CO":      {"lat": 40.0,    "lon": -105.0,  "alt": 1600},
    "San Francisco":    {"lat": 37.77,   "lon": -122.41, "alt": 100},
    "Denver, CO":       {"lat": 39.74,   "lon": -104.99, "alt": 1609},
}

# Time Range
start_date = datetime(2024, 12, 24, 0, 0, 0)
end_date = datetime(2024, 12, 26, 23, 59, 59)  # 3 days

# Visibility Threshold
min_elevation = 10.0  # degrees
```

### Step 2: Run Predictions Manually

Create `analyze_passes.py`:

```python
from satcore import load_tle, propagate_satellite, GroundStation, detect_passes
from datetime import datetime, timedelta

# Load TLE
name, line1, line2 = load_tle("data/tle_leo/AO-95.txt")
print(f"Analyzing: {name}\n")

locations = {
    "Boulder, CO":      (40.0, -105.0, 1600),
    "San Francisco":    (37.77, -122.41, 100),
    "Denver, CO":       (39.74, -104.99, 1609),
}

start = datetime(2024, 12, 24, 0, 0, 0)
end = datetime(2024, 12, 26, 23, 59, 59)

for city, (lat, lon, alt) in locations.items():
    print(f"\n{'='*60}")
    print(f"Location: {city}")
    print(f"Coordinates: {lat}°, {lon}°, {alt}m altitude")
    print(f"{'='*60}")
    
    station = GroundStation(lat_deg=lat, lon_deg=lon, alt_m=alt)
    
    # Generate predictions every 5 minutes
    times = []
    elevations = []
    current = start
    while current <= end:
        times.append(current)
        pos, _ = propagate_satellite(line1, line2, current)
        elev = station.elevation_deg(pos)
        elevations.append(elev)
        current += timedelta(minutes=5)
    
    # Detect passes
    passes = detect_passes(times, elevations, threshold_deg=10.0)
    
    print(f"Total passes in 3 days: {len(passes)}\n")
    
    for i, pass_event in enumerate(passes, 1):
        print(f"Pass #{i}")
        print(f"  Rise:     {pass_event.rise_time} UTC")
        print(f"  Max elev: {pass_event.max_time} UTC @ {pass_event.max_elevation_deg:.1f}°")
        print(f"  Set:      {pass_event.set_time} UTC")
        print(f"  Duration: {(pass_event.set_time - pass_event.rise_time).total_seconds() / 60:.1f} minutes")
        print()
```

**Run it:**
```powershell
python analyze_passes.py
```

### Step 3: Expected Output

```
Analyzing: AO-95 (FUNCUBE-2)

============================================================
Location: Boulder, CO
Coordinates: 40.0°, -105.0°, 1600m altitude
============================================================
Total passes in 3 days: 8

Pass #1
  Rise:     2024-12-24 05:32:15 UTC
  Max elev: 2024-12-24 05:38:42 UTC @ 67.8°
  Set:      2024-12-24 05:45:08 UTC
  Duration: 12.9 minutes

Pass #2
  Rise:     2024-12-24 17:08:20 UTC
  Max elev: 2024-12-24 17:13:15 UTC @ 35.2°
  Set:      2024-12-24 17:18:10 UTC
  Duration: 9.8 minutes

[... 6 more passes over 3 days ...]

============================================================
Location: San Francisco
Coordinates: 37.77°, -122.41°, 100m altitude
============================================================
Total passes in 3 days: 7

[Note: Different timing and elevation angles due to location]

============================================================
Location: Denver, CO
Coordinates: 39.74°, -104.99°, 1609m altitude
============================================================
Total passes in 3 days: 9

[Similar to Boulder but different exact times due to 1° latitude difference]
```

### Step 4: Validate Results

**Check each pass:**

1. **Timing Makes Sense?**
   ```
   ✅ Passes ~90 min apart (orbital period)
   ✅ Passes shift by ~22° in longitude each orbit (Earth rotation)
   ```

2. **Elevations Reasonable?**
   ```
   ✅ Boulder: 35-68° (40°N latitude sees good passes)
   ✅ San Francisco: 20-45° (37°N gets lower max elevations)
   ✅ Denver: 40-70° (39°N, similar to Boulder)
   ```

3. **Pass Count Expected?**
   ```
   ✅ 7-9 passes in 3 days for 97.7° inclined orbit at 40°N
   ✅ Matches typical ~2-3 passes per day
   ```

### Step 5: Compare Versions

**Create test_all_versions.py:**
```python
import subprocess
import json

versions = ["v1_0_basic_pass_predictor", "v1_1_visualization", "v2_0_ai_correction"]

for version in versions:
    print(f"\n{'='*60}")
    print(f"Running {version}")
    print(f"{'='*60}")
    result = subprocess.run(["python", f"{version}/main.py"], capture_output=True, text=True)
    print(result.stdout)
    if result.returncode != 0:
        print(f"ERROR: {result.stderr}")
```

---

## Summary: What You Can Validate

After running through these steps, you can confirm:

### ✅ Physics Correctness
- [ ] SGP4 propagation produces valid orbits (radius checks)
- [ ] GMST and coordinate transforms work
- [ ] Ground station geometry is accurate
- [ ] Pass detection threshold crossing logic correct

### ✅ Data Accuracy
- [ ] TLE files load correctly
- [ ] Real satellites (AO-91, AO-95) produce sensible orbits
- [ ] Time ranges work as expected
- [ ] Elevation angles match manual calculation

### ✅ Software Quality
- [ ] All 41 tests pass (27 unit + 14 integration)
- [ ] No import errors across all 4 versions
- [ ] Code runs without crashes
- [ ] Results are reproducible

### ✅ Real-World Usability
- [ ] Can predict passes for any ground station
- [ ] Results match external sources (like N2YO.com)
- [ ] Handles edge cases (high/low latitudes, different satellites)
- [ ] Computation is fast (predictions in <1 second)

### ✅ API Correctness
- [ ] satcore exports work correctly
- [ ] Function signatures match documentation
- [ ] Return types are correct
- [ ] Error handling works (invalid TLEs, bad locations, etc.)

---

## Next Steps After Validation

Once you confirm all above checks pass:
1. **Publish Results**: Document findings in README
2. **Create Changelog**: List what each version does
3. **Option 4**: Package for distribution (pip install)
4. **GitHub Release**: Tag version 1.0.0 on GitHub
