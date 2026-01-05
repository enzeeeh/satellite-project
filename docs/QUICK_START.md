# Quick Start Guide

Get up and running in 5 minutes.

## Installation

### 1. Check Python Version
```bash
python --version
# Need: 3.10 or higher
```

### 2. Install Required Packages
```bash
pip install sgp4 numpy
```

### 3. Optional: For Visualization
```bash
# For static plots (PNG)
pip install matplotlib

# For interactive plots (HTML)
pip install plotly kaleido

# For both
pip install matplotlib plotly kaleido
```

### 4. Optional: For ML Features
```bash
pip install torch
```

## Your First Prediction

### Example 1: Basic (< 1 second)
```bash
python main.py --tle data/tle_leo/AO-91.txt
```

**Output**:
```
UNIFIED SATELLITE PASS PREDICTOR
======================================================================

[1/5] Loading satellite TLE data...
  ✓ Loaded: AMSAT-OSCAR 91

[2/5] Setting up ground station...
  ✓ Location: 40.0°N, -105.0°E, 1600m

[3/5] Propagating satellite...
  ✓ Computed 5760 elevation samples

[4/5] Detecting passes...
  ✓ Found 4 passes above 10° threshold
  Pass 1: 2025-12-26 12:30:15 @ 45.2° (10.0 min)
  Pass 2: 2025-12-26 14:05:30 @ 32.1° (7.5 min)
  Pass 3: 2025-12-27 11:45:22 @ 55.8° (12.3 min)
  Pass 4: 2025-12-28 10:20:18 @ 28.4° (6.8 min)

✓ Prediction complete!
```

### Example 2: With Plots (5-10 seconds)
```bash
python main.py --tle data/tle_leo/AO-91.txt --plot matplotlib
```

**Creates**:
- `outputs/elevation_mpl_*.png` - Elevation angle vs time
- `outputs/ground_track_mpl_*.png` - Satellite path on Earth map
- Console output with pass summary

### Example 3: Different Location
```bash
python main.py --tle data/tle_leo/AO-91.txt --lat 51.5 --lon -0.1 --alt 10
```
(Predicts for London, UK)

### Example 4: Extended Horizon
```bash
python main.py --tle data/tle_leo/AO-91.txt --hours 168 --plot matplotlib
```
(Predicts for 7 days, creates plots)

## Common Tasks

### Find High Passes (> 45° elevation)
```bash
python main.py --tle data/tle_leo/AO-91.txt --threshold 45
```

### Track Multiple Satellites
```bash
python main.py --tle data/tle_leo/AO-91.txt --hours 48
python main.py --tle data/tle_leo/AO-95.txt --hours 48
```

### See Interactive Plots
```bash
python main.py --tle data/tle_leo/AO-91.txt --plot plotly
```

Creates HTML files you can open in browser and zoom/pan.

### Save Results as JSON
```bash
python main.py --tle data/tle_leo/AO-91.txt --json-output
```

Creates `passes_*.json` in `outputs/` folder.

## Understanding the Output

### Pass Information
```
Pass 1: 2025-12-26 12:30:15 @ 45.2° (10.0 min)
│       │                     │      │
│       └─ Start time (AOS)   │      └─ Duration
│                             └─ Max elevation
└─ Pass number
```

### Time Meanings
- **AOS** (Acquisition of Signal) - Satellite rises above horizon
- **TCA** (Time of Closest Approach) - Highest point in sky
- **LOS** (Loss of Signal) - Satellite sets below horizon

### Elevation Angle
- **10°**: Just above horizon (difficult to observe)
- **30°**: Good visibility
- **45°**: Very good for communication
- **90°**: Directly overhead (zenith)

## Troubleshooting

### "No such file or directory: data/tle_leo/AO-91.txt"

**Problem**: TLE file not found

**Solution**:
```bash
# Check what TLE files you have
ls data/tle_leo/
ls data/tle_geo/

# Use existing file
python main.py --tle data/tle_leo/AO-95.txt
```

### "ModuleNotFoundError: No module named 'sgp4'"

**Problem**: Missing required package

**Solution**:
```bash
pip install sgp4
```

### "ModuleNotFoundError: No module named 'matplotlib'"

**Problem**: Visualization library not installed

**Solution**:
```bash
pip install matplotlib
```

Or use Plotly instead:
```bash
pip install plotly
```

### Plots don't appear as PNG files

**Problem**: Kaleido not installed (needed for PNG export)

**Solution**:
```bash
pip install kaleido
```

Or use Plotly's HTML format:
```bash
python main.py --tle data/tle_leo/AO-91.txt --plot plotly
```

### "No such file or directory" for ML model

**Problem**: Model file doesn't exist

**Solution**:
```bash
# Only use --ai-correct if you have trained model
# Otherwise, omit this flag:
python main.py --tle data/tle_leo/AO-91.txt --plot matplotlib
```

## Next Steps

### Learn the CLI
Read [Usage Guide](USAGE_GUIDE.md) for all available options (includes Quick Reference cheat sheet).

### Understand the Project
Read root [README.md](../README.md) for project overview and capabilities.

### Get Help
```bash
python main.py --help
```

Shows all available flags and options.

---

**Ready to dive deeper?** → [Complete Usage Guide](USAGE_GUIDE.md)
