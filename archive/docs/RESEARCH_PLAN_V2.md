# Research Plan v2: A Well-Posed, CPU-Cheap SGP4 Error-Correction Study

*Successor to `RESEARCH_PLAN.md`. That study returned a negative result (deep sequence models do not beat SGP4). This plan fixes the four design flaws identified in its §7 and re-poses the problem so that a genuine improvement is at least **possible** — while staying inside a laptop/CPU compute budget.*

---

## 0. What changed and why

| Flaw in v1 (see `RESEARCH_PLAN.md` §7) | Fix in v2 |
|---|---|
| Target and baseline were both SGP4 → ceiling is "tie SGP4" | Target is **real** SGP4 error: divergence of a TLE from the *next independently-fitted TLE* at its epoch (Peng & Bai formulation) |
| Residual signal tiny/noisy at 3-day staleness | Train across the **full natural spread of TLE ages** (0 → ~5 days between consecutive TLEs); no artificial `STALE_DAYS` inflation |
| Residuals in geodetic degrees (ill-posed, wraps at poles/±180°) | Residuals in the **RIC frame** (radial / along-track / cross-track) in km — along-track is the dominant, well-behaved axis |
| Deep nets on a small, low-signal target → fit noise; needs GPU | **LightGBM** gradient-boosted trees — better on small tabular data, trains in seconds on **CPU**, no Colab GPU |
| No physical driver of drag error in the features | Add **space-weather** features (F10.7 solar flux, Ap/Kp geomagnetic index) — the actual cause of the drag error SGP4 misses |

**Falsifiable success criterion.** The corrected prediction must reduce **along-track MAE (km)** versus raw SGP4 on the held-out test set, evaluated per TLE-age cohort. If it does not beat SGP4, v2 also concludes as an (honest) negative result — but now the experiment is *capable* of a positive one, which v1 was not.

---

## 1. Ground truth — the core fix

We never observe the "true" orbit directly, but each newly published TLE is a fresh fit to real tracking observations at its epoch. So we treat the **next** TLE as ground truth for the **current** one:

```
For each consecutive TLE pair (TLE_k, TLE_{k+1}) of a satellite:
    t_eval = epoch(TLE_{k+1})                     # moment fresh tracking data arrived
    r_pred = SGP4(TLE_k).propagate(t_eval)        # what the old TLE predicted
    r_true = SGP4(TLE_{k+1}).propagate(t_eval)    # fresh fit ≈ real state at t_eval
    error_vec = r_true - r_pred                   # REAL SGP4 prediction error (ECEF/TEME km)
```

Also sample intermediate horizons `t_eval = epoch(TLE_k) + Δ` for `Δ ∈ {1, 3, 6, 12, 24, 48, 72} h`, propagating `TLE_k` (prediction) and interpolating truth from the bracketing fresh TLEs where available. This is a real, non-circular error signal — the quantity SGP4 actually gets wrong, not SGP4-vs-SGP4.

> This generalises what the *shipped* corrector (`notebooks/train_residual_model.ipynb`, `src/ml/`) already does for a single scalar, extending it to (a) 3 RIC components, (b) multiple horizons, and (c) space-weather inputs.

---

## 2. Target: RIC frame

Rotate `error_vec` into the orbit-relative RIC frame at `t_eval`, from the predicted state `(r_pred, v_pred)`:

```
R̂ = r_pred / |r_pred|                 # radial (out from Earth)
Ĉ = (r_pred × v_pred) / |r_pred × v_pred|   # cross-track (orbit normal)
Î = Ĉ × R̂                             # in-track / along-track (≈ velocity dir)
error_RIC = [ error_vec·R̂ , error_vec·Î , error_vec·Ĉ ]   # km
```

Along-track (`Î`) carries the bulk of SGP4 drag error and grows monotonically with time-since-epoch — a clean regression target. Predicting three scalars in km avoids every geodetic-degree pathology from v1.

---

## 3. Features (per prediction, tabular — one row per sample)

| Group | Features |
|---|---|
| Orbit (from `TLE_k`) | `mean_motion`, `eccentricity`, `inclination_deg`, `raan_deg`, `arg_perigee_deg`, `bstar`, `altitude_km` |
| Time | `time_since_epoch_hours` (the horizon) |
| Space weather at `t_eval` | `f107`, `f107_81d_avg`, `ap_daily`, `kp_sum`, and 1–3-day lags |
| Optional | `beta_angle_deg` (Sun–orbit geometry, drives density), `sin/cos(arg_lat)` |

Space weather is fetched once from CelesTrak's consolidated file (`SW-Last5Years.csv`, free, no account) and joined on date. F10.7 and Ap are the standard NRLMSISE-00 drag drivers, so they are the physically-motivated inputs SGP4 lacks.

---

## 4. Model

- **Primary:** `LightGBM` regressor, one per RIC axis (or `MultiOutput`), objective = Huber/L1 (robust to decayed-TLE outliers, as in the shipped model).
- **Controls:** (a) raw SGP4 (predict zero correction) — the baseline to beat; (b) a linear/ridge model — to confirm trees add value; (c) the v1 winner (do-nothing) sanity check carried over.
- Time-ordered 70/15/15 split; early stopping on validation L1; ~hundreds of trees. **Training target: < 1 minute on CPU.**

No GPU, no Colab session-persistence problems, no LSTM divergence.

---

## 5. Evaluation (mirror v1 §6 so results are comparable)

1. **Along-track / radial / cross-track MAE & RMSE (km)** by horizon, corrected vs raw SGP4.
2. **MAE vs time-since-epoch** cohorts `{<1d, 1–3d, 3–5d}` — now populated with real data, unlike v1 §6.2.
3. **Ablations:** orbit-only vs orbit+space-weather (does F10.7/Ap actually help?); LightGBM vs linear.
4. **Percent within ±X km** (operational metric the shipped model uses).
5. Honest write-up either way. A negative result here is still informative because the design is now sound.

---

## 6. Work plan (small, incremental, each step independently useful)

| Step | Deliverable | Compute |
|---|---|---|
| 1 | `notebooks/05_residual_trees.ipynb` — space-weather fetch + RIC transform + consecutive-TLE-pair sampler (scaffolded) | CPU |
| 2 | Re-use `data/collected` TLE history (already fetched) to build the v2 sample table | CPU, seconds |
| 3 | Train LightGBM, run ablations, fill §5 tables | CPU, < 5 min total |
| 4 | If it beats SGP4: wire into `src/ml/` behind the existing app toggle. If not: append negative result to this doc. | — |

Steps 1–3 reuse the TLEs already in `data/collected/` (no re-fetch needed for a first pass); only space weather is a new, tiny download.

---

## References

Same as `RESEARCH_PLAN.md`. The consecutive-TLE-pair ground-truth construction follows Peng & Bai (2018, 2019) [5, 6]; F10.7/Ap as drag drivers follow the NRLMSISE-00 atmosphere model.
