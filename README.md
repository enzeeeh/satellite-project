# Satellite Pass Predictor

Predict when satellites are visible from your location.

## Quick Start

```bash
# Basic prediction
python main.py --tle data/tle_leo/AO-91.txt

# With visualization
python main.py --tle data/tle_leo/AO-91.txt --plot matplotlib

# Custom location (London)
python main.py --tle data/tle_leo/AO-91.txt --lat 51.5 --lon -0.1 --plot matplotlib
```

**Output**: Pass times, elevation angles, and optional plots

## Learn More

- **[What is this project?](docs/ABOUT.md)** - Overview and features
- **[First Time?](docs/QUICK_START.md)** - Installation and basic usage
- **[Full Documentation](docs/)** - Detailed guides and references

## Features

- ✅ SGP4 orbital propagation (accurate satellite positions)
- ✅ Pass prediction (when satellites are visible)
- ✅ Visualization (matplotlib/plotly plots)
- ✅ ML corrections (optional neural network enhancement)
- ✅ Multiple satellites and locations
- ✅ JSON output for automation

## Requirements

- Python 3.10+
- `sgp4` (orbital mechanics)
- `numpy` (numerical computing)
- `matplotlib` or `plotly` (optional, for visualization)
- `torch` (optional, for ML features)

## Installation

```bash
pip install sgp4 numpy matplotlib plotly torch
```

## Quick Help

```bash
python main.py --help
```

---
## Releasing

Keep releases simple:
- See the change history in [CHANGELOG.md](CHANGELOG.md)
- Follow the minimal steps in [RELEASE.md](RELEASE.md)

---

**For detailed documentation, see [docs/](docs/)**
