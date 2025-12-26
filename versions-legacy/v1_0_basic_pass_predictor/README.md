# Minimal Satellite Pass Predictor (SGP4)

This is a minimal, clean Python implementation that predicts satellite passes for the next 48 hours using SGP4 propagation and simple topocentric geometry.

- Language: Python
- Propagator: [`sgp4`](https://pypi.org/project/sgp4/)
- Input: TLE text file (3 lines: name, line1, line2)
- Output: JSON list of passes with start, max elevation time, end, and max elevation degrees

## Ground Station (default)
- Latitude: 40.0°
- Longitude: -105.0°
- Altitude: 1600 m
- Elevation threshold: 10°

## Install (Conda)
```powershell
# Open Anaconda Prompt (recommended) or a Conda-enabled PowerShell
conda create -n satpass python=3.11 -y
conda activate satpass
conda install -y -c conda-forge sgp4 numpy
```

Alternative (pip/venv):
```powershell
python -m venv .venv
. .venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Usage
```powershell
# From the project root (after activating Conda env or venv)
python -m src.main --tle data/tle.txt --hours 48 --step 30 --threshold 10 `
  --lat 40.0 --lon -105.0 --alt 1600
```

- `--tle`: Path to your TLE file. Replace `data/tle.txt` with your target satellite.
- `--start-utc`: Optional ISO time (e.g., `2025-12-19T00:00:00Z`). Default is now (UTC).
- `--hours`: Prediction horizon (default 48).
- `--step`: Time step seconds (default 30).
- `--threshold`: Elevation threshold degrees (default 10).

The program prints JSON, e.g.:
```json
[
  {
    "startTime": "2025-12-19T01:23:45Z",
    "maxTime": "2025-12-19T01:30:18Z",
    "endTime": "2025-12-19T01:36:12Z",
    "maxElevationDeg": 54.321
  }
]
```

## TLE File Format
`data/tle.txt` should contain exactly three non-empty lines (comments starting with `#` are ignored):
```
SAT NAME
1 xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
2 xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```
A sample ISS TLE is provided for convenience.

## Notes on Accuracy
- Coordinates are propagated in TEME and converted to ECEF using a simple GMST rotation via `sgp4.ext.gstime`. This is a practical approximation for pass prediction.
- For high-precision work, include equation of the equinoxes, polar motion, UT1-UTC, and IAU 2006/2000A models (e.g., via Astropy).

## Project Structure
```
v1_0_basic_pass_predictor/
├── data/
│   └── tle.txt
├── src/
│   ├── tle_loader.py
│   ├── propagator.py
│   ├── ground_station.py
│   ├── pass_detector.py
│   └── main.py
├── requirements.txt
└── README.md
```
