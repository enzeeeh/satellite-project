# Frequently Asked Questions

Common questions about the Satellite Pass Predictor — covering usage, core physics, data, ML, and testing.

---

## General

**Q: What does this project do?**  
A: It predicts when a satellite will be visible from a ground station — giving you Acquisition of Signal (AOS), Time of Closest Approach (TCA), Loss of Signal (LOS), and max elevation for each pass. It supports LEO and GEO satellites, optional matplotlib/plotly plots, and an optional ML residual correction layer on top of SGP4.

**Q: How do I run it?**  
A: Two ways:

```bash
# Interactive wizard — no flags needed, step-by-step prompts
python main.py

# CLI — supply all options directly
python main.py --tle data/tle_leo/AO-91.txt --lat 40 --lon -105 --alt 1600 --hours 24 --plot matplotlib
```

**Q: What satellites can it track?**  
A: Any satellite with a valid TLE. The repo ships with AO-91 and AO-95 (amateur radio LEO), plus a few GEO satellites. You can drop any TLE file from [CelesTrak](https://celestrak.org/) or [Space-Track](https://www.space-track.org/) into `data/` and point `--tle` at it.

---

## Core Physics

**Q: What propagation model is used?**  
A: SGP4 via the `sgp4` Python library (v2.20+). It takes a Two-Line Element (TLE) set and propagates the satellite's position forward in time using the TEME (True Equator Mean Equinox) reference frame.

**Q: What is a TLE?**  
A: A Two-Line Element set is a standardised two-line text format for describing a satellite's orbit. It encodes the epoch, inclination, RAAN (Right Ascension of Ascending Node), eccentricity, argument of perigee, mean anomaly, and mean motion. The project reads them from plain `.txt` files.

**Q: How does TEME position become an elevation angle?**  
A: Three-step pipeline:

1. **TEME → ECEF** — Rotate by the Greenwich Mean Sidereal Time (GMST) angle around the Z-axis using the IAU 1982 formula
2. **ECEF → ENU** — Convert the satellite's ECEF position relative to the ground station into East-North-Up coordinates using WGS84 geodetic constants ($a = 6378.137$ km, $f = 1/298.257223563$)
3. **ENU → Elevation** — $\text{elevation} = \arctan\!\left(\dfrac{\text{Up}}{\sqrt{\text{East}^2 + \text{North}^2}}\right)$

**Q: How does pass detection work?**  
A: The code samples elevation at a fixed time step (default 30 s). When it finds an interval where elevation crosses the threshold (default 10°), it uses **linear interpolation** between those two samples to compute the precise AOS and LOS times. The sample with the highest elevation inside the pass is the TCA.

**Q: What are the known physical simplifications?**  
A:
- GMST computed with IAU 1982 formula — polar motion and UT1-UTC offset are ignored
- No atmospheric refraction correction
- No terrain masking or obstruction modelling
- For sub-kilometre accuracy, use Astropy or NASA SPICE instead

---

## Data & Files

**Q: Where are the TLE files?**  
A:
| Path | Satellites |
|------|-----------|
| `data/tle_leo/AO-91.txt` | AO-91 — amateur radio LEO (~400 km, ~82° inc.) |
| `data/tle_leo/AO-95.txt` | AO-95 — amateur radio LEO |
| `data/tle_geo/tle.txt` | TDRS 3, FLTSATCOM, SKYNET (GEO) |

**Q: Why does the TLE file have thousands of lines?**  
A: The files contain historical TLE records going back years. Currently only the **first valid TLE** in each file is used for prediction — historical entries are preserved for future analysis features.

**Q: Where do run outputs go?**  
A: All outputs land in `outputs/` and are git-ignored (not committed):

| File pattern | Contents |
|-------------|----------|
| `passes_<timestamp>.json` | Structured pass data (AOS, TCA, LOS, elevation, duration) |
| `elevation_mpl_<timestamp>.png` | Elevation vs time curve (matplotlib) |
| `ground_track_mpl_<timestamp>.png` | Global ground track map (matplotlib) |
| `elevation_plotly_<timestamp>.html` | Interactive elevation plot (plotly) |
| `ground_track_plotly_<timestamp>.html` | Interactive ground track map (plotly) |

---

## Output Format

**Q: What does the JSON output look like?**

```json
{
  "metadata": {
    "satellite": "AO-91",
    "ground_station": { "lat": 40.0, "lon": -105.0, "alt_m": 1600 },
    "prediction_window_hours": 24,
    "threshold_deg": 10.0
  },
  "passes": [
    {
      "pass_number": 1,
      "aos_time": "2026-04-27T07:10:20+00:00",
      "tca_time": "2026-04-27T07:14:14+00:00",
      "los_time": "2026-04-27T07:17:48+00:00",
      "max_elevation_deg": 38.3,
      "duration_minutes": 7.5,
      "prediction_type": "basic"
    }
  ]
}
```

**Q: What does `prediction_type` mean?**  
A: `"basic"` means raw SGP4 output was used. `"ai_corrected"` means the ML residual model was applied before elevation was computed.

---

## ML Correction

**Q: What is the AI correction feature?**  
A: A small PyTorch neural network (`ResidualPredictor`) that predicts an along-track position error in km. It shifts the satellite's ECEF position along its velocity unit vector before the elevation angle is computed. The result is a corrected prediction that attempts to account for TLE modelling residuals.

**Q: What are the network inputs and output?**  

| Feature | Description |
|---------|-------------|
| `time_since_tle_epoch_hours` | How old the TLE is at prediction time |
| `mean_motion_rev_per_day` | Orbital rate from TLE line 2 |
| `eccentricity` | Orbital eccentricity from TLE line 2 |
| `inclination_deg` | Orbital inclination from TLE line 2 |

Output: along-track error in km (positive = satellite is ahead of predicted position).

**Q: Is the model pretrained?**  
A: Yes — `models/residual_model.pt` is included in the repo. Enable it with:
```bash
python main.py --tle data/tle_leo/AO-91.txt --ai-correct
# or answer "Yes" at Step 5 of the interactive wizard
```

**Q: Architecture of the neural network?**  
A: Fully-connected: `4 → 64 → 32 → 16 → 1` with ReLU activations and 0.1 dropout.

---

## Architecture

**Q: What is `src/core/` vs `satcore/`?**  
A: They currently contain identical code — a known duplication. `src/core/` is used by `main.py` at runtime; `satcore/` is used by the test suite. Consolidation to `src/core/` is a planned improvement.

**Q: What's in `src/visualization/`?**  
A: Two modules, each with both a matplotlib (PNG) and plotly (interactive HTML) variant:
- `elevation_plot.py` — elevation vs time curve with AOS/LOS/MAX markers and pass window shading
- `ground_track.py` — geodetic lat/lon ground track with ground station marker

---

## Testing

**Q: How many tests are there and how do I run them?**  
A: 41 tests, 100% passing across 6 test files:

```bash
pytest tests/ -v
```

| File | Count | Covers |
|------|-------|--------|
| `test_propagator.py` | 7 | GMST formula, TEME→ECEF rotation |
| `test_ground_station.py` | 6 | WGS84 constants, ENU transform, elevation |
| `test_pass_detector.py` | 8 | AOS/LOS detection, interpolation, edge cases |
| `test_tle_loader.py` | 5 | TLE parsing, comment filtering, error handling |
| `test_integration_leo.py` | 10 | Real AO-91/AO-95 TLE data end-to-end |
| `test_integration_geo.py` | 6 | Real GEO TLE data end-to-end |

**Q: Is there a CI pipeline?**  
A: Yes — `.github/workflows/tests.yml` runs the full test suite on every push via GitHub Actions.
