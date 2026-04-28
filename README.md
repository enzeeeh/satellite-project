# Satellite Pass Predictor

**Predict when satellites are visible from your location** - simple, accurate, and flexible.

## What This Project Does

Given a satellite's orbital data (TLE), your ground station coordinates, and a time window, this tool predicts:
- ⏰ **When** the satellite rises above the horizon (AOS - Acquisition of Signal)
- 📈 **When** it reaches maximum elevation (TCA - Time of Closest Approach)
- 📉 **When** it sets below the horizon (LOS - Loss of Signal)
- 📊 **How high** it gets in the sky (elevation angle)

Perfect for amateur radio operators, astronomers, educators, and space mission planners.

## Quick Start

```bash
# Basic prediction (Boulder, CO by default)
python main.py --tle data/tle_leo/AO-91.txt

# With visualization
python main.py --tle data/tle_leo/AO-91.txt --plot matplotlib

# Custom location (London)
python main.py --tle data/tle_leo/AO-91.txt --lat 51.5 --lon -0.1 --plot matplotlib

# Find only high-quality passes (> 45°)
python main.py --tle data/tle_leo/AO-91.txt --threshold 45 --hours 168
```

**Output**: Pass times, elevation angles, optional plots (PNG/HTML), and JSON data.

## Key Features

### Core Capabilities
- ✅ **Accurate Predictions** - Uses SGP4 model (industry standard for LEO/GEO satellites)
- ✅ **Multiple Satellites** - Process any TLE data from CelesTrak or Space-Track
- ✅ **Any Location** - WGS84 geodetic coordinates with altitude support
- ✅ **Flexible Time Windows** - From minutes to weeks
- ✅ **JSON Output** - Structured data for automation and integration

### Visualization
- ✅ **Ground Tracks** - See satellite path on a map (static or interactive)
- ✅ **Elevation Plots** - Visualize pass quality and timing
- ✅ **Dual Modes** - Matplotlib (PNG) or Plotly (HTML)

### Advanced
- ✅ **ML Enhancements** - Optional neural network for residual corrections
- ✅ **Analysis Tools** - Compare TLE accuracy across epochs
- ✅ **Flexible CLI** - Mix and match features with command-line flags

## Installation

### Prerequisites
- Python 3.10 or higher

### Install Dependencies
```bash
# Core (required)
pip install sgp4 numpy

# Visualization (optional)
pip install matplotlib plotly

# ML features (optional)
pip install torch

# Or install all at once
pip install -r requirements.txt
```

## Example Output

**Interactive wizard** (no flags needed):
```bash
python main.py
```

**Or direct CLI**:
```bash
python main.py --tle data/tle_leo/AO-91.txt --lat 40 --lon -105 --alt 1600 --hours 24 --plot matplotlib
```

**Console output** (AO-91 over Boulder, CO — 24 h window):
```
======================================================================
UNIFIED SATELLITE PASS PREDICTOR
======================================================================

[1/5] Loading TLE from data/tle_leo/AO-91.txt...
  ✓ Loaded: AO-91

[2/5] Setting up ground station...
  ✓ Location: 40.0°N, -105.0°E, 1600m
  ✓ Time samples: 2881 (30.0s step)

[3/5] Propagating satellite...
  ✓ Computed 2881 elevation samples

[4/5] Detecting passes...
  ✓ Found 4 passes above 10.0° threshold
    Pass 1: 2026-04-27 07:14:14 @ 38.3° (7.5 min)
    Pass 2: 2026-04-27 08:46:14 @ 16.3° (5.1 min)
    Pass 3: 2026-04-27 17:43:44 @ 12.6° (3.2 min)
    Pass 4: 2026-04-27 19:16:14 @ 38.9° (6.7 min)

[5/5] Generating visualizations (matplotlib)...
  ✓ Saved: outputs/ground_track_mpl_....png
  ✓ Saved: outputs/elevation_mpl_....png

  ✓ JSON output: outputs/passes_....json
```

**JSON pass record**:
```json
{
  "pass_number": 1,
  "aos_time": "2026-04-27T07:10:20+00:00",
  "tca_time": "2026-04-27T07:14:14+00:00",
  "los_time": "2026-04-27T07:17:48+00:00",
  "max_elevation_deg": 38.3,
  "duration_minutes": 7.5,
  "prediction_type": "basic"
}
```

**Generated files** (saved to `outputs/`, git-ignored):
- 📄 `passes_<timestamp>.json` — Structured pass data
- 📊 `elevation_mpl_<timestamp>.png` — Elevation vs time curve
- 🌍 `ground_track_mpl_<timestamp>.png` — Satellite path on world map

## Documentation

### Getting Started
- **[Quick Start Guide](docs/QUICK_START.md)** - Installation, first run, basic usage (5 min read)
- **[Usage Guide](docs/USAGE_GUIDE.md)** - Complete reference for all CLI options and workflows
- **[FAQ](docs/FAQ.md)** - Common questions on physics, data, ML, and testing

### Technical Details
- **[Architecture](docs/ARCHITECTURE.md)** - How the system works (modules, data flow)
- **[Prediction Pipeline](docs/deep_dive/prediction_pipeline.md)** - Mathematical deep dive (SGP4, coordinate transforms, ML corrections)
- **[Visualization Guide](docs/VISUALIZATION_GUIDE.md)** - Plotting options and customization

### Development
- **[Development Guide](docs/DEVELOPMENT.md)** - Setup for contributors, testing, code style
- **[Roadmap](docs/ROADMAP.md)** - Future features and planned improvements

### Additional Resources
- **[Migration Archive](docs/archive/MIGRATION.md)** - Legacy version upgrade notes

## Use Cases

### 📡 Amateur Radio Operators
Track satellites like AO-91 and AO-95 to plan communication windows.
```bash
python main.py --tle data/tle_leo/AO-91.txt --hours 168 --threshold 45
```

### 🔭 Astronomers
Plan ISS or Hubble observation sessions with precise timing.
```bash
python main.py --tle data/tle_leo/ISS.txt --hours 168 --plot plotly
```

### 🛰️ Mission Planners
Predict coverage for multiple ground stations (JPL, Goddard, Stanford).
```bash
python main.py --tle data/tle.txt --lat 34.2 --lon -118.2  # JPL
python main.py --tle data/tle.txt --lat 38.8 --lon -77.0   # Goddard
```

### 🎓 Students & Educators
Learn orbital mechanics, coordinate transformations, and SGP4 with real data.

## Technology Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Orbital mechanics** | SGP4 (pysgp4) | Predict satellite positions from TLE |
| **Math/Science** | NumPy | Vector operations, coordinate transforms |
| **Plotting** | Matplotlib + Plotly | Static and interactive visualizations |
| **ML** | PyTorch | Optional neural network corrections |
| **Testing** | Pytest | Automated validation and CI/CD |

## Project Structure

```
satellite-project/
├── main.py                     Unified CLI entry point
├── src/
│   ├── core/                   Physical models (SGP4, coordinates)
│   ├── visualization/          Plotting utilities
│   └── ml/                     Machine learning enhancements
├── data/
│   ├── tle_leo/                LEO satellite TLEs (AO-91, AO-95, etc.)
│   └── tle_geo/                GEO satellite TLEs
├── models/                     Pre-trained ML models
├── outputs/                    Generated results (JSON, plots)
├── docs/                       Documentation (guides, references)
└── tests/                      Automated test suite
```

## Accuracy & Limitations

### ✅ Accurate For:
- Recent TLEs (< 14 days old)
- LEO and GEO satellites
- Predictions within a few weeks
- Elevation angles > 5° above horizon

### ⚠️ Not Suitable For:
- Very old TLEs (accuracy degrades rapidly after 30 days)
- Highly elliptical or specialized orbits
- High-precision requirements (~km-level accuracy)
- Real-time tracking without TLE updates

### Simplifications:
- Uses GMST for coordinate rotation (ignores polar motion, UT1-UTC)
- Simplified atmospheric refraction model
- No terrain elevation or obstruction modeling

For high-precision missions, integrate with Astropy or NASA SPICE toolkit.

## Data Sources

- **TLE Data**: [CelesTrak](https://celestrak.org/), [Space-Track](https://www.space-track.org/)
- **Satellite Info**: [N2YO](https://www.n2yo.com/), [Wikipedia](https://en.wikipedia.org/wiki/List_of_active_satellites)

## Contributing & Development

See [DEVELOPMENT.md](docs/DEVELOPMENT.md) for:
- Setting up development environment
- Running tests (`pytest`)
- Code style guidelines
- Submitting pull requests

## Release Notes

- **[CHANGELOG.md](CHANGELOG.md)** - Version history and changes
- **[RELEASE.md](RELEASE.md)** - Release process documentation

## Support

For issues, questions, or suggestions:
1. Check the documentation in `docs/`
2. Review [QUICK_START.md](docs/QUICK_START.md) troubleshooting section
3. Open an issue on GitHub with detailed error messages and context

---

**Ready to predict satellite passes?** → Start with the [Quick Start Guide](docs/QUICK_START.md)
