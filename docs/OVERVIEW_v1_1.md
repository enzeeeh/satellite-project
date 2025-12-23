# Satellite Project v1.1 — Visualization Overview

This document explains what v1.1 adds, what the outputs mean, how to run it, and how CI/versioning are handled.

## What Changed in v1.1
- Physics unchanged from v1.0: SGP4 propagation in TEME, simple GMST rotation to ECEF, topocentric ENU and elevation.
- Optional visualization layer:
  - Ground track (sub-satellite latitude/longitude) using Matplotlib and Plotly.
  - Elevation vs time with detected pass windows highlighted and max elevation markers.
  - Images saved under `v1_1_visualization/outputs/plots` with a UTC timestamp suffix.

## Key Files
- Predictor entrypoint: [v1_1_visualization/src/main.py](../v1_1_visualization/src/main.py)
- Visualization modules:
  - Ground track: [v1_1_visualization/src/visualization/ground_track.py](../v1_1_visualization/src/visualization/ground_track.py)
  - Elevation plot: [v1_1_visualization/src/visualization/elevation_plot.py](../v1_1_visualization/src/visualization/elevation_plot.py)
- Physics (copied from v1.0 to keep behavior identical):
  - [v1_1_visualization/src/propagator.py](../v1_1_visualization/src/propagator.py)
  - [v1_1_visualization/src/ground_station.py](../v1_1_visualization/src/ground_station.py)
  - [v1_1_visualization/src/pass_detector.py](../v1_1_visualization/src/pass_detector.py)
  - [v1_1_visualization/src/tle_loader.py](../v1_1_visualization/src/tle_loader.py)

## Running v1.1
Conda setup:
```powershell
conda activate satpass
pip install -r v1_1_visualization/requirements.txt
```
Run prediction + plots (example, 1 hour, 60s step):
```powershell
python -m v1_1_visualization.src.main --tle v1_0_basic_pass_predictor/data/tle.txt `
  --hours 1 --step 60 --plots both --outdir v1_1_visualization/outputs/plots
```

### CLI Options
- `--tle`: TLE file path (3 lines: name, line1, line2).
- `--lat`, `--lon`, `--alt`: Ground station geodetic coordinates (deg, deg, meters).
- `--threshold`: Elevation threshold for detecting passes (deg).
- `--hours`: Prediction horizon in hours.
- `--step`: Propagation time step in seconds.
- `--start-utc`: Optional ISO UTC start time (e.g., `2025-12-19T00:00:00Z`), default is now (UTC).
- `--plots`: `none` (default), `matplotlib`, `plotly`, or `both`.
- `--outdir`: Directory to save plots; defaults to `v1_1_visualization/outputs/plots`.

## Outputs Explained
### Console JSON
After detection, the program prints a JSON array of passes, e.g.:
```json
[
  {
    "startTime": "2025-12-19T04:27:51.392348Z",
    "maxTime": "2025-12-19T04:30:34.468757Z",
    "endTime": "2025-12-19T04:32:41.721574Z",
    "maxElevationDeg": 15.31
  }
]
```
- `startTime`: AOS (acquisition of signal) — the moment elevation first crosses the threshold upward.
- `maxTime`: Time of maximum elevation during the pass.
- `endTime`: LOS (loss of signal) — the moment elevation crosses the threshold downward.
- `maxElevationDeg`: Peak elevation angle in degrees during the pass.

### Plot Images
Saved under `v1_1_visualization/outputs/plots` with names like:
- `ground_track_matplotlib_YYYYMMDDTHHMMSSZ.png`
- `ground_track_plotly_YYYYMMDDTHHMMSSZ.png` (or `.html` fallback)
- `elevation_matplotlib_YYYYMMDDTHHMMSSZ.png`
- `elevation_plotly_YYYYMMDDTHHMMSSZ.png` (or `.html` fallback)

#### Ground Track
- Shows the sub-satellite point (latitude/longitude) over time.
- Computed by converting the satellite ECEF position to WGS84 geodetic lat/lon.
- Longitude is wrapped to `[-180°, 180°]`. Expect line breaks near the International Date Line.
- **Annotations** (with colored markers and labels):
  - **START** (green circle): Opening position with UTC timestamp.
  - **END** (red circle): Closing position with UTC timestamp.
  - **MAX_LAT** (yellow star): Northernmost latitude reached.
  - **STATION** (red triangle): Ground observer location with coordinates (lat, lon).

#### Elevation vs Time
- Elevation curve for the entire prediction window.
- Green shaded bands mark detected pass intervals (above threshold).
- Orange dashed line indicates the threshold elevation (default 10°).
- Black line at 0° is the geometric horizon.
- **Annotations** (with colored markers and labels):
  - **AOS** (green circle): Acquisition of signal—where elevation crosses the threshold upward.
  - **LOS** (red circle): Loss of signal—where elevation crosses the threshold downward.
  - **MAX** (purple star): Peak elevation angle with value (degrees) and pass duration.
  - **Threshold line** (orange dashed): Minimum elevation for a usable pass.
  - **Pass duration labels**: Minutes shown above each pass window for quick reference.
- Use this to see pass durations, peaks, visibility windows, and observation timing.

## Physics Notes (unchanged from v1.0)
- Orbits propagated in TEME using SGP4 (`Satrec.sgp4`).
- TEME → ECEF via a simple Z-rotation using GMST (IAU 1982 approximation).
- Topocentric ENU and elevation computed with WGS84 geodetic station coordinates.
- For high-precision work, consider full IAU 2000/2006 transforms with UT1-UTC, EQE, and polar motion.

## CI/CD
- v1.0 workflow: [\.github/workflows/ci.yml](../.github/workflows/ci.yml)
  - Installs deps, byte-compiles `src`, runs a sample.
- v1.1 workflow: [\.github/workflows/ci_v1_1.yml](../.github/workflows/ci_v1_1.yml)
  - Installs visualization deps.
  - Runs the v1.1 entrypoint to generate plots.
  - Uploads plot artifacts for inspection on each push/PR.

## Versioning Strategy
- Source layout: We kept separate folders per version (`v1_0_basic_pass_predictor`, `v1_1_visualization`) to preserve backwards-compatible behavior and make it explicit which code produces which outputs.
- Git strategy:
  - Use Git tags/releases (e.g., `v1.0.0`, `v1.1.0`) for versioning the repository.
  - CI can run multiple versions via separate workflows or a matrix.
  - If desired, we can refactor a shared core (physics) module and import it from both versions to reduce duplication while maintaining versioned entrypoints.
- GitHub Actions versioning: Actions themselves don’t version your code — they execute workflows for whatever commit/branch is pushed. Tags/releases are the canonical way to version software in GitHub.

## Quick Troubleshooting
- Plotly static export requires Kaleido. If unavailable in the environment, the code falls back to HTML output.
- If no passes appear, try a longer `--hours`, finer `--step`, or a different `--threshold`.
- Ensure the TLE file has exactly three non-empty lines: name, line 1 (starts with `1 `), line 2 (starts with `2 `).
