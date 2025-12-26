# About This Project

## What Is It?

**Satellite Pass Predictor** is a Python tool that tells you **when satellites are visible from your location**. 

Given:
- A satellite's orbital data (TLE - Two-Line Element)
- Your ground station location (latitude, longitude, altitude)
- A time window (e.g., "next 48 hours")

It answers:
- **When** does the satellite rise above the horizon?
- **When** is it at maximum elevation (best viewing)?
- **When** does it set below the horizon?
- **How high** does it get in the sky?

## Why Use It?

### For Amateur Radio (Satellite Communication)
- Know when to point your antenna at satellites like AO-91, AO-95
- Schedule communication windows with other operators
- Track multiple satellites simultaneously

### For Astronomy (Observation)
- Plan observation sessions for ISS, Hubble, etc.
- Know the best elevation angle for photography
- Plan outdoor activities around satellite passes

### For Space Missions (Mission Planning)
- Predict pass times for specific ground stations
- Analyze satellite constellation coverage
- Test orbital mechanics algorithms

### For Education
- Learn about orbital mechanics (SGP4 model)
- Understand coordinate transformations (ECEF, ENU, WGS84)
- Practice with real satellite data

## Key Capabilities

### Core Features
✅ **Accurate Predictions** - Uses SGP4 model (industry standard for LEO/GEO)  
✅ **Multiple Satellites** - Process any TLE data  
✅ **Any Location** - WGS84 geodetic coordinates  
✅ **Flexible Time Windows** - From minutes to days  
✅ **JSON Output** - Easy to automate and integrate  

### Visualization
✅ **Ground Tracks** - See satellite path on a map  
✅ **Elevation Plots** - Visualize pass quality  
✅ **Static (PNG)** or **Interactive (HTML)** plots  

### Advanced
✅ **ML Enhancements** - Optional neural network for residual corrections  
✅ **Analysis Tools** - Compare TLE accuracy  
✅ **Flexible CLI** - Mix and match features with flags  

## Example: What You Get

**Input**:
```bash
python main.py --tle data/tle_leo/AO-91.txt --plot matplotlib
```

**Output**:
```
PASS #1 over Boulder, CO
Rise (AOS):     2025-12-26 12:30:15 UTC @ 10° elevation
Peak (TCA):     2025-12-26 12:35:22 UTC @ 45° elevation
Set (LOS):      2025-12-26 12:40:18 UTC @ 5° elevation
Duration:       10 minutes
Quality:        ⭐⭐ Good
```

Plus:
- 📊 Elevation vs time plot (PNG)
- 🌍 Ground track map (PNG)
- 📄 JSON file with structured data

## Project Structure

```
src/
├── core/              Physical models (SGP4, coordinate transforms)
├── visualization/     Plotting utilities (matplotlib, plotly)
└── ml/               Machine learning enhancements (optional)

main.py              Unified command-line interface

docs/               Documentation (you are here)
data/               TLE files for various satellites
models/             Pre-trained ML models
outputs/            Results and plots
```

## Technology Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Orbital mechanics** | SGP4 (pysgp4) | Predict satellite positions |
| **Math/Science** | NumPy | Numerical computations |
| **Plotting** | Matplotlib + Plotly | Static and interactive plots |
| **ML** | PyTorch | Optional neural network corrections |
| **Testing** | Pytest | Automated validation |

## History & Evolution

This project has evolved through multiple iterations:

- **v1.0**: Basic pass prediction (command-line tool)
- **v1.1**: Added visualization (plots and graphs)
- **v1.2**: Added TLE accuracy analysis (synthetic deviation testing)
- **v2.0**: Added ML enhancements (neural network corrections)
- **Unified**: Combined all into one flexible system (current)

The unified system eliminates duplication and lets you mix features freely.

## Use Cases

### Scenario 1: Amateur Radio Operator
```bash
# Find good passes in next week for AO-91 and AO-95
python main.py --tle data/tle_leo/AO-91.txt --hours 168 --threshold 45
python main.py --tle data/tle_leo/AO-95.txt --hours 168 --threshold 45
```

### Scenario 2: ISS Photographer
```bash
# Get daytime passes with precise timing
python main.py --tle data/tle_leo/ISS.txt --hours 168 --plot matplotlib
# Plan outdoor photography session based on elevation and timing
```

### Scenario 3: Mission Control
```bash
# Predict coverage for multiple ground stations
python main.py --tle data/tle.txt --lat 34.2 --lon -118.2  # JPL
python main.py --tle data/tle.txt --lat 38.8 --lon -77.0   # Goddard
python main.py --tle data/tle.txt --lat 37.4 --lon -122.1  # Stanford
```

## Key Assumptions & Limitations

### Accurate For:
- Satellites with recent TLEs (< 14 days old)
- LEO (Low Earth Orbit) and GEO (Geostationary) satellites
- Predictions within a few weeks
- Elevation angles > 5° (horizon effects ignored below)

### Not Suitable For:
- Very old TLEs (accuracy degrades rapidly)
- Highly elliptical or special orbits
- High precision (~km-level) requirements
- Real-time tracking (use TLE Age > 30 days with caution)

### Simplifications:
- GMST for coordinate rotation (ignores polar motion, UT1-UTC)
- Simplified atmospheric refraction
- No ground elevation or blockage

For high-precision work, integrate with Astropy or NASA SPICE toolkit.

## Data Sources

### TLE Files
- **CelesTrak**: https://celestrak.org/ (primary source)
- **NORAD**: https://www.space-track.org/ (raw data)

### Satellite Information
- **NORAD**: https://www.space-track.org/
- **Wikipedia**: https://en.wikipedia.org/wiki/List_of_active_satellites
- **N2YO**: https://www.n2yo.com/

## Getting Started

**New to this project?**
- Read [Quick Start](QUICK_START.md) (5 minutes)
- Run the examples
- Check out the docs/

**Already familiar?**
- See [Usage Guide](USAGE_GUIDE.md) for detailed reference
- Check [Quick Reference](QUICK_REFERENCE.md) for command cheat sheet

**Want to improve?**
- See [Improvements](IMPROVEMENTS.md) for feature ideas
- Read [Architecture](ARCHITECTURE.md) for technical details

## Support

For issues, questions, or suggestions:
1. Check the documentation in `docs/`
2. Review examples in the README
3. Check troubleshooting section in QUICK_START.md

---

**Next**: Ready to use it? → [Quick Start Guide](QUICK_START.md)
