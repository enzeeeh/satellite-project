# Quick Reference - Command Cheat Sheet

Copy & paste ready examples.

## One-Liners

### Basics
```bash
# Simple prediction
python main.py --tle data/tle_leo/AO-91.txt

# Show help
python main.py --help
```

### Visualizations
```bash
# Static plots (PNG)
python main.py --tle data/tle_leo/AO-91.txt --plot matplotlib

# Interactive plots (HTML)
python main.py --tle data/tle_leo/AO-91.txt --plot plotly

# Both
python main.py --tle data/tle_leo/AO-91.txt --plot both
```

### Ground Stations
```bash
# Default (Boulder, CO)
python main.py --tle data/tle_leo/AO-91.txt

# London, UK
python main.py --tle data/tle_leo/AO-91.txt --lat 51.5 --lon -0.1 --alt 10

# Tokyo, Japan
python main.py --tle data/tle_leo/AO-91.txt --lat 35.7 --lon 139.7 --alt 50

# JPL, Pasadena
python main.py --tle data/tle_leo/AO-91.txt --lat 34.2 --lon -118.2 --alt 230
```

### Time Ranges
```bash
# 7 days
python main.py --tle data/tle_leo/AO-91.txt --hours 168

# 14 days
python main.py --tle data/tle_leo/AO-91.txt --hours 336

# Specific date
python main.py --tle data/tle_leo/AO-91.txt --start-utc 2025-12-28T00:00:00Z --hours 24
```

### Pass Filtering
```bash
# Only high passes (>45°)
python main.py --tle data/tle_leo/AO-91.txt --threshold 45

# Low passes (>5°)
python main.py --tle data/tle_leo/AO-91.txt --threshold 5
```

### ML Corrections
```bash
python main.py --tle data/tle_leo/AO-91.txt --ai-correct --model models/residual_model.pt
```

### Combined
```bash
python main.py --tle data/tle_leo/AO-91.txt \
  --lat 40 --lon -105 --alt 1600 \
  --hours 168 --threshold 10 \
  --plot both \
  --ai-correct --model models/residual_model.pt
```

## Flag Reference

| Flag | Default | Example | Purpose |
|------|---------|---------|---------|
| `--tle` | **required** | `data/tle_leo/AO-91.txt` | TLE file |
| `--lat` | 40.0 | `51.5` | Latitude |
| `--lon` | -105.0 | `-0.1` | Longitude |
| `--alt` | 1600 | `10` | Altitude (m) |
| `--threshold` | 10.0 | `45` | Min elevation (°) |
| `--hours` | 48.0 | `168` | Window (hours) |
| `--step` | 30.0 | `60` | Step (seconds) |
| `--start-utc` | now | `2025-12-28T00:00:00Z` | Start time |
| `--plot` | none | `matplotlib` | Plot type |
| `--ai-correct` | false | (flag) | Enable ML |
| `--model` | none | `models/residual_model.pt` | ML model |
| `--analyze-deviation` | false | (flag) | TLE analysis |
| `--outdir` | outputs | `results/` | Output dir |
| `--json-output` | false | (flag) | Force JSON |

## Common Workflows

### Workflow 1: Quick Check
```bash
python main.py --tle data/tle_leo/AO-91.txt
# < 1 second, console output only
```

### Workflow 2: Plan Session
```bash
python main.py --tle data/tle_leo/AO-91.txt --hours 24 --threshold 30 --plot matplotlib
# Find good passes in next 24 hours with plots
```

### Workflow 3: Multiple Satellites
```bash
for sat in data/tle_leo/*.txt; do
  python main.py --tle "$sat" --hours 48
done
```

### Workflow 4: Multiple Locations
```bash
python main.py --tle data/tle_leo/AO-91.txt --outdir outputs/boulder
python main.py --tle data/tle_leo/AO-91.txt --lat 51.5 --lon -0.1 --outdir outputs/london
python main.py --tle data/tle_leo/AO-91.txt --lat 35.7 --lon 139.7 --outdir outputs/tokyo
```

### Workflow 5: AI + Plots
```bash
python main.py \
  --tle data/tle_leo/AO-91.txt \
  --ai-correct --model models/residual_model.pt \
  --plot plotly \
  --hours 168
```

## File Locations

```
data/tle_leo/        ← LEO satellite TLEs
data/tle_geo/        ← GEO satellite TLEs
models/              ← ML models
outputs/             ← Results go here
```

## Troubleshooting

### Missing TLE file
```bash
ls data/tle_leo/  # See available files
```

### Missing package
```bash
pip install sgp4 numpy matplotlib plotly torch
```

### Module not found
```bash
pip install <package_name>
```

### No PNG output
```bash
pip install kaleido  # For Matplotlib PNG export
# Or use Plotly HTML instead
python main.py --tle data/tle_leo/AO-91.txt --plot plotly
```

---

See [Usage Guide](USAGE_GUIDE.md) for detailed reference.
