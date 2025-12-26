# v1.2 — Synthetic Deviation & Error Modeling

## Overview
Extends the v1.0 SGP4 predictor with a **synthetic orbital error model** that generates ML training data. Creates two parallel pass predictions:
1. **SGP4 nominal** — Standard Two-Line Element propagation
2. **Synthetic truth** — SGP4 with synthetic perturbations applied

Computes residuals (differences) for training predictive error models.

## Motivation
Real satellite TLE elements age, becoming outdated. This system simulates how orbital predictions diverge from actual observations by:
- Adding along-track drift proportional to time since TLE epoch
- Injecting random cross-track noise
- Perturbing pass timing (AOS/LOS)

The residuals are suitable for training ML models to predict/correct TLE prediction errors.

## Architecture

### Modules
- **`deviation_model.py`** — Core perturbation functions:
  - `perturb_position()` — Apply along-track drift + cross-track noise to ECEF
  - `perturb_pass_times()` — Random timing shifts for AOS/LOS
  - `compute_position_error()` — Euclidean distance between predictions
  - `compute_timing_error()` — Seconds difference between times

- **`residuals.py`** — Statistics & output:
  - `ResidualStats` — Accumulate error metrics
  - `write_residuals_json()` — Save per-pass and aggregate residuals
  - `write_passes_json()` — Export pass predictions

- **`main.py`** — Orchestration:
  - Load TLE
  - Propagate twice (nominal + perturbed)
  - Detect passes for both
  - Match passes and compute residuals
  - Write three JSON outputs

## Usage

```bash
# Basic run (default Boulder, CO; 24-hour window)
python -m v1_2_synthetic_deviation.src.main \
  --tle v1_0_basic_pass_predictor/data/tle.txt

# Custom location, 72-hour window
python -m v1_2_synthetic_deviation.src.main \
  --tle v1_0_basic_pass_predictor/data/tle.txt \
  --hours 72 \
  --station-lat 51.5 \
  --station-lon -0.1 \
  --station-alt 0.01

# Coarser time step (faster, less detail)
python -m v1_2_synthetic_deviation.src.main \
  --tle v1_0_basic_pass_predictor/data/tle.txt \
  --step 120

# Custom elevation threshold
python -m v1_2_synthetic_deviation.src.main \
  --tle v1_0_basic_pass_predictor/data/tle.txt \
  --threshold 20.0
```

## Output Files

### `passes_sgp4.json`
Standard pass predictions from unperturbed SGP4:
```json
{
  "metadata": { ... },
  "passes": [
    {
      "start_utc": "2025-12-23T12:34:56Z",
      "end_utc": "2025-12-23T12:42:10Z",
      "max_elevation_deg": 45.23,
      "duration_sec": 434
    }
  ]
}
```

### `passes_synthetic_truth.json`
Same structure, but computed from perturbed orbits (the "ground truth").

### `residuals.json`
Detailed comparison showing SGP4 vs. truth for each matched pass:
```json
{
  "metadata": { ... },
  "overall_statistics": {
    "pass_count": 12,
    "position_error_km": {
      "mean": 0.15,
      "std": 0.08,
      "min": 0.02,
      "max": 0.31,
      "median": 0.14
    },
    "aos_error_sec": { ... },  // AOS timing error
    "los_error_sec": { ... },  // LOS timing error
    "max_elevation_error_deg": { ... }
  },
  "residuals_by_pass": [
    {
      "pass_index": 0,
      "sgp4_aos_utc": "2025-12-23T12:34:56Z",
      "truth_aos_utc": "2025-12-23T12:35:02Z",
      "aos_error_sec": 6.2,
      "sgp4_los_utc": "2025-12-23T12:42:10Z",
      "truth_los_utc": "2025-12-23T12:41:58Z",
      "los_error_sec": -12.1,
      "sgp4_max_el_deg": 45.23,
      "truth_max_el_deg": 44.85,
      "max_el_error_deg": -0.38,
      "position_error_km": 0.18
    }
  ]
}
```

## Error Model

### Along-Track Drift
```
drift = rate × hours_since_epoch
rate = 0.05 km/hour (configurable)
```
Simulates TLE aging — older TLEs increasingly miss along-track position.

### Cross-Track Noise
```
noise ~ N(0, σ²)
σ = 0.02 km (configurable)
```
Random walk perpendicular to velocity direction. Simulates modeling uncertainty.

### Timing Perturbation
```
error ~ U(±max_error)
max_error = 2.0 minutes (configurable)
```
Random uniform shift applied independently to AOS and LOS.

## Statistics Computed

For each pass and aggregated across all passes:
- **Position error**: 3D Euclidean distance (km)
- **AOS error**: Seconds between SGP4 and truth start times
- **LOS error**: Seconds between SGP4 and truth end times
- **Max elevation error**: Degrees difference

Statistics include: mean, std dev, min, max, median.

## ML Training Workflow

Typical usage for error correction models:
1. Generate synthetic residuals (this tool)
2. Train regressor: `passes_sgp4.json` → `residuals.json`
3. Model learns: "Given SGP4 prediction, predict actual error"
4. Deploy: Correct live TLE passes by adding learned residuals

## Notes

- Residuals are **time-dependent** (drift grows over hours)
- Perturbations use a **seeded PRNG** (reproducible with `--seed`)
- Pass matching is **greedy** (nearest AOS in truth to each SGP4 pass)
- Position error is sampled at pass midpoint (max elevation time)

## Dependencies
- `sgp4` (≥2.22): Orbital propagation
- `numpy` (≥1.23): Numerical operations

## See Also
- v1.0: Core SGP4 pass prediction
- v1.1: Visualization of passes
