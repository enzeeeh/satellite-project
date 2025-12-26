# Usage Guide - Complete Reference

## Command-Line Options

### Required
- `--tle PATH` - Path to TLE file (required)

### Ground Station (optional)
- `--lat DEGREES` - Latitude (default: 40.0)
- `--lon DEGREES` - Longitude (default: -105.0)
- `--alt METERS` - Altitude (default: 1600)

### Time Parameters (optional)
- `--hours HOURS` - Prediction window (default: 48)
- `--step SECONDS` - Propagation step (default: 30)
- `--start-utc ISO_TIME` - Start time (default: now)

### Thresholds (optional)
- `--threshold DEGREES` - Min elevation (default: 10)

### Features (optional)
- `--plot {none|matplotlib|plotly|both}` - Visualizations
- `--ai-correct` - Enable ML corrections
- `--model PATH` - ML model path
- `--analyze-deviation` - Analyze TLE accuracy

### Output (optional)
- `--outdir PATH` - Output directory (default: outputs)
- `--json-output` - Save passes as JSON

## Examples

### Basic Prediction
```bash
python main.py --tle data/tle_leo/AO-91.txt
```

### With Visualization
```bash
# Matplotlib (static PNG)
python main.py --tle data/tle_leo/AO-91.txt --plot matplotlib

# Plotly (interactive HTML)
python main.py --tle data/tle_leo/AO-91.txt --plot plotly

# Both
python main.py --tle data/tle_leo/AO-91.txt --plot both
```

### Different Location
```bash
# London, UK (51.5°N, 0.1°W)
python main.py --tle data/tle_leo/AO-91.txt --lat 51.5 --lon -0.1 --alt 10

# Tokyo, Japan
python main.py --tle data/tle_leo/AO-91.txt --lat 35.7 --lon 139.7 --alt 50

# JPL, Pasadena
python main.py --tle data/tle_leo/AO-91.txt --lat 34.2 --lon -118.2 --alt 230
```

### Extended Time Window
```bash
# 7 days
python main.py --tle data/tle_leo/AO-91.txt --hours 168

# 14 days with plots
python main.py --tle data/tle_leo/AO-91.txt --hours 336 --plot matplotlib
```

### Pass Filtering
```bash
# Only high elevation passes (>45°)
python main.py --tle data/tle_leo/AO-91.txt --threshold 45

# Low elevation passes (>5°)
python main.py --tle data/tle_leo/AO-91.txt --threshold 5
```

### ML Corrections
```bash
# Using trained model
python main.py --tle data/tle_leo/AO-91.txt --ai-correct --model models/residual_model.pt

# With visualization
python main.py --tle data/tle_leo/AO-91.txt --ai-correct --model models/residual_model.pt --plot plotly
```

### Combined
```bash
python main.py --tle data/tle_leo/AO-91.txt \
  --lat 40 --lon -105 --alt 1600 \
  --hours 168 --threshold 10 \
  --plot both \
  --ai-correct --model models/residual_model.pt \
  --outdir my_results
```

## Output Formats

### Console Output
Pass summary with times and elevations (always printed)

### PNG Plots
With `--plot matplotlib` or `--plot both`:
- `ground_track_mpl_*.png` - Satellite path on map
- `elevation_mpl_*.png` - Elevation vs time graph

### HTML Plots
With `--plot plotly` or `--plot both`:
- `ground_track_plotly_*.html` - Interactive map
- `elevation_plotly_*.html` - Interactive graph

### JSON Output
With `--json-output` or default:
- `passes_*.json` - Structured pass data

## JSON Output Structure

```json
{
  "metadata": {
    "generated_at": "2025-12-26T10:30:00Z",
    "satellite": "AMSAT-OSCAR 91",
    "ground_station": {
      "latitude_deg": 40.0,
      "longitude_deg": -105.0,
      "altitude_m": 1600
    },
    "prediction": {
      "start_time": "2025-12-26T00:00:00Z",
      "end_time": "2025-12-28T00:00:00Z",
      "horizon_threshold_deg": 10
    },
    "num_passes": 4
  },
  "passes": [
    {
      "pass_number": 1,
      "aos_time": "2025-12-26T12:30:15Z",
      "tca_time": "2025-12-26T12:35:22Z",
      "los_time": "2025-12-26T12:40:18Z",
      "max_elevation_deg": 45.2,
      "duration_minutes": 10.0
    }
  ]
}
```

## Tips & Tricks

### Batch Processing Multiple Satellites
```bash
for tle in data/tle_leo/*.txt; do
  python main.py --tle "$tle" --hours 48
done
```

### Compare Multiple Locations
```bash
python main.py --tle data/tle_leo/AO-91.txt --outdir outputs/boulder
python main.py --tle data/tle_leo/AO-91.txt --lat 51.5 --lon -0.1 --outdir outputs/london
python main.py --tle data/tle_leo/AO-91.txt --lat 35.7 --lon 139.7 --outdir outputs/tokyo
```

### Find Passes on Specific Date
```bash
python main.py --tle data/tle_leo/AO-91.txt \
  --start-utc 2025-12-28T00:00:00Z \
  --hours 24
```

### High-Precision Predictions
```bash
# Use smaller step (10 seconds instead of default 30)
python main.py --tle data/tle_leo/AO-91.txt --step 10
```

### Extended Predictions
```bash
# 2 weeks with high precision
python main.py --tle data/tle_leo/AO-91.txt --hours 336 --step 10
```

## Performance Notes

- **Typical**: < 1 second for 48-hour prediction
- **Large window**: 7 days ≈ 10 seconds
- **With plots**: + 5-10 seconds
- **With ML**: + 2 seconds per batch

## Help & Support

### Show all options
```bash
python main.py --help
```

### Check Python version
```bash
python --version
```

### Verify packages installed
```bash
python -c "import sgp4; import numpy; print('OK')"
```

---

**For more info**: Check [Architecture](ARCHITECTURE.md) or [About](ABOUT.md)
