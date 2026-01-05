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

**Command**:
```bash
python main.py --tle data/tle_leo/AO-91.txt --plot matplotlib
```

**Console Output**:
```
PASS #1 over Boulder, CO
Rise (AOS):     2025-12-26 12:30:15 UTC @ 10° elevation
Peak (TCA):     2025-12-26 12:35:22 UTC @ 45° elevation
Set (LOS):      2025-12-26 12:40:18 UTC @ 5° elevation
Duration:       10 minutes
Quality:        ⭐⭐ Good
```

**Generated Files**:
- 📄 `outputs/passes_TIMESTAMP.json` - Structured data
- 📊 `outputs/elevation_plot.png` - Elevation vs time graph
- 🌍 `outputs/ground_track.png` - Satellite path on map

## Documentation

### Getting Started
- **[Quick Start Guide](docs/QUICK_START.md)** - Installation, first run, basic usage (5 min read)
- **[Usage Guide](docs/USAGE_GUIDE.md)** - Complete reference for all CLI options and workflows

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
