# Satellite Pass Predictor with Visualization (v1.1)

Adds optional visualization to the minimal pass predictor:
- Ground track (sub-satellite lat/lon) using Matplotlib and Plotly
- Elevation vs time with pass windows highlighted
- Plots saved under `outputs/plots`

Physics is unchanged from v1.0 (SGP4 + GMST TEME→ECEF rotation).

## Install (Conda)
```powershell
conda create -n satpass python=3.11 -y
conda activate satpass
conda install -y -c conda-forge sgp4 numpy matplotlib plotly kaleido
```

## Usage
```powershell
# From repository root
python -m v1_1_visualization.src.main --tle v1_0_basic_pass_predictor/data/tle.txt \
  --hours 2 --step 60 --plots both --outdir v1_1_visualization/outputs/plots
```

Options:
- `--plots`: `none` (default), `matplotlib`, `plotly`, or `both`
- `--lat/--lon/--alt/--threshold/--hours/--step/--start-utc`: Same as v1.0
- `--outdir`: Directory to save plots (defaults to `outputs/plots`)

## Notes
- Plotly static image export uses Kaleido; HTML export is also supported.
- Ground track is the sub-satellite point (ECEF→geodetic WGS84).
