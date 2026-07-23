# Research Plan: Replacing SGP4 with Deep Sequence Models for Satellite Orbit Prediction

---

## Abstract

The Simplified General Perturbations 4 (SGP4) propagator is the operational standard for predicting the positions of Earth-orbiting objects from Two-Line Element (TLE) sets. Its accuracy degrades progressively as TLE age increases, with errors reaching tens of kilometres within days of the epoch for Low Earth Orbit (LEO) satellites. This work investigates whether deep sequence models — specifically Long Short-Term Memory (LSTM) networks and Transformer encoders — trained on historical TLE-derived position time series can produce multi-horizon orbit predictions that outperform SGP4 on stale TLEs. We collect six months of TLE history for five diverse satellites from the Space-Track catalogue, propagate each TLE set at one-minute resolution to produce geodetic position and velocity time series, engineer a 15-dimensional feature vector per timestep, and train both architectures to predict position at T+10, T+30, T+60, and T+120 minutes from a 90-minute observation window. We will compare MAE (km) and RMSE (km) across horizons and TLE age cohorts to test the hypothesis that learned dynamics correct for the systematic SGP4 drift caused by atmospheric drag and unmodelled perturbations.

---

## 1. Introduction

Accurate knowledge of satellite positions is critical for collision avoidance, pass scheduling at ground stations, and space situational awareness. The dominant operational approach — SGP4 applied to TLEs published by the 18th Space Control Squadron — is deterministic, computationally cheap, and universally available. However, TLE accuracy degrades at a rate that depends strongly on orbital altitude and the current state of the upper atmosphere. For LEO satellites such as the International Space Station (ISS, NORAD 25544), a 7-day-old TLE can accumulate positional errors exceeding 50 km, rendering it useless for close-approach monitoring.

Machine learning approaches to orbit prediction have received growing attention since approximately 2018 [5, 6]. Two broad families exist: (1) *residual correction* models that apply a learned offset to SGP4 predictions, and (2) *end-to-end* models that learn orbital dynamics directly from observed position sequences. This project pursues the latter because it removes SGP4 entirely from the inference path, which eliminates the TLE-age dependency as a fundamental limitation.

Our contributions are:
1. An open, reproducible data collection pipeline using the Space-Track `gp_history` endpoint.
2. A systematic feature engineering approach encoding orbital geometry for sequence models.
3. A head-to-head benchmark of LSTM vs Transformer vs SGP4 across multiple forecast horizons.
4. Analysis of model advantage stratified by TLE age, validating the core hypothesis.

---

## 2. Background

### 2.1 Two-Line Element Sets

A TLE is a compact ASCII representation of a satellite's mean Keplerian orbital elements at a reference epoch, formatted per the NORAD standard [1]. Elements include semi-major axis (encoded as mean motion), eccentricity, inclination, right ascension of ascending node, argument of perigee, and mean anomaly. TLEs are published with a typical update cadence of one to three days for tracked objects.

### 2.2 SGP4 Propagation

SGP4 integrates the mean-element differential equations forward in time using simplified analytic perturbation models that account for the dominant harmonics of Earth's gravitational potential (J2, J3, J4), atmospheric drag (parametrised by the BSTAR drag term in the TLE), and solar radiation pressure [1, 2]. Because atmospheric density is modelled at the epoch of each TLE, drag predictions become increasingly inaccurate as the difference between propagation time and epoch grows.

### 2.3 Accuracy Degradation

Vallado et al. [2] quantified SGP4 errors as a function of TLE age using independent radar tracking data. For LEO objects, the along-track error grows roughly linearly at 0.5–2 km per day under nominal solar activity, reaching ~10 km after one week and potentially much more during geomagnetic storms.

---

## 3. Related Work

**Peng & Bai (2018)** [5] used feedforward neural networks to predict along-track corrections to SGP4 predictions using TLE-derived input features, achieving error reductions of up to 40% over a 7-day propagation window for LEO satellites.

**Peng & Bai (2019)** [6] extended their framework to incorporate multiple historical TLEs as inputs, demonstrating that richer orbital history further reduced prediction error.

**Hochreiter & Schmidhuber (1997)** [3] introduced LSTM, which remains among the most effective architectures for multivariate time-series prediction thanks to its learned gating mechanism that selectively retains long-range dependencies.

**Vaswani et al. (2017)** [4] proposed the Transformer, which models pairwise temporal relationships through self-attention. Transformers have since outperformed LSTMs on many sequence modelling benchmarks, though LSTMs remain competitive on shorter sequences with limited data.

Unlike prior residual-correction work, this project trains models that predict absolute position rather than corrections, enabling evaluation as a drop-in replacement rather than a post-processing layer.

---

## 4. Data

### 4.1 Source

TLE history is retrieved from Space-Track (`https://www.space-track.org`) using the `gp_history` API endpoint, which provides all published TLEs for a given NORAD catalogue number within a date range. Authentication requires a free registered account.

### 4.2 Satellites

| NORAD ID | Name | Orbit Type | Altitude (approx.) |
|---|---|---|---|
| 43017 | AO-91 (RadFxSat) | LEO Sun-sync | ~700 km |
| 43137 | AO-95 | LEO Sun-sync | ~700 km |
| 25544 | ISS | LEO Inclined | ~420 km |
| 33591 | AO-51 (EchoStar) | MEO | ~800 km |
| 20580 | Hubble Space Telescope | LEO Inclined | ~540 km |

The diverse mix of altitudes and inclinations ensures the model is not overfit to a single drag regime.

### 4.3 Collection Pipeline

For each NORAD ID:
1. Retrieve all TLEs for the trailing 180-day window.
2. For each TLE epoch, propagate forward to the epoch of the *next* TLE (or at most 3 days), at 1-minute intervals, using `sgp4.api.Satrec`.
3. Convert TEME Cartesian output to geodetic coordinates (WGS84) using an iterative algorithm.
4. Record each propagated point as a row: `timestamp_utc, lat_deg, lon_deg, alt_km, vx_km_s, vy_km_s, vz_km_s, tle_age_days`.

This produces a continuous 1-minute-resolution position series with known provenance for every point.

### 4.4 Feature Engineering

Fifteen features are computed per timestep:

| Feature | Derivation |
|---|---|
| `lat_deg`, `lon_deg`, `alt_km` | Direct from propagation |
| `vx_km_s`, `vy_km_s`, `vz_km_s` | Direct from SGP4 |
| `speed_km_s` | $\|\mathbf{v}\|$ |
| `orbital_period_min` | $2\pi\sqrt{(R_E+h)^3/\mu}$ |
| `sin_lat`, `cos_lat` | Cyclic encoding of latitude |
| `sin_lon`, `cos_lon` | Cyclic encoding of longitude |
| `hour_sin`, `hour_cos` | Cyclic encoding of UTC hour |
| `tle_age_days` | Elapsed time since TLE epoch |

Features are normalised to zero mean and unit variance using a StandardScaler fit only on the training partition to prevent leakage.

---

## 5. Methodology

### 5.1 Problem Formulation

Given an observation window of $T_{in} = 90$ consecutive timesteps (90 minutes at 1-min resolution), predict the geodetic position $(\phi, \lambda, h)$ at four future horizons $\{+10, +30, +60, +120\}$ minutes. Each prediction is a point estimate in physical units (degrees, km).

Formally:
$$\hat{\mathbf{p}}_{t+\Delta} = f_\theta\left(\mathbf{X}_{t-T_{in}:t}\right), \quad \Delta \in \{10, 30, 60, 120\}$$

where $\mathbf{X} \in \mathbb{R}^{T_{in} \times F}$ is the feature matrix ($F=15$) and $\hat{\mathbf{p}} \in \mathbb{R}^3$.

### 5.2 Dataset Split

The full time series (per satellite) is split **in time order** to prevent leakage:
- **Train:** first 70% of windows
- **Validation:** next 15%
- **Test:** final 15%

### 5.3 LSTM Architecture

A bidirectional two-layer LSTM with hidden dimension 256 processes the input sequence. The final hidden states from forward and backward directions are concatenated and passed through a two-layer fully-connected head (GELU activation, layer normalisation, dropout 0.1) that outputs 12 values (4 horizons × 3 targets).

Total trainable parameters: ~2.5 M.

### 5.4 Transformer Architecture

A linear input projection maps the $F$-dimensional features to a $d_{model}=256$ embedding space. Sinusoidal positional encodings are added. Two `nn.TransformerEncoderLayer` blocks (4 attention heads, feed-forward dimension 512, pre-norm, dropout 0.1) process the sequence. The output is mean-pooled and passed through the same FC head as the LSTM.

Total trainable parameters: ~1.8 M.

### 5.5 Training

- **Loss:** MSE on the 12 output values
- **Optimiser:** AdamW, weight decay $10^{-4}$
- **Learning rate:** $10^{-3}$ with cosine annealing to $10^{-5}$
- **Batch size:** 128
- **Early stopping:** patience 10 epochs on validation loss
- **Gradient clipping:** max norm 1.0

### 5.6 Baseline

The **SGP4-stale baseline** propagates, for each prediction time, the most recent TLE that is at least `STALE_DAYS` old (3 days in the reported run), producing a full SGP4 position estimate at every horizon. This is a strong, operationally realistic baseline: it is exactly what a ground station would obtain by running SGP4 on the freshest TLE it happened to have a few days ago.

> **Note:** An earlier draft of this plan specified a weaker dead-reckoning baseline (repeat the last observed position). That was replaced during implementation by the full SGP4-stale propagation above, which is a materially harder target to beat. See §5.7.

### 5.7 Implementation notes — deviations from the original plan

The notebooks as executed differ from the plan in §5.1–§5.6 in two important ways. Both are recorded here so the results in §6 are interpreted against what was actually run, not against the original intent.

1. **Residual correction, not end-to-end replacement.** §1 and §5.1 frame the models as predicting *absolute* position and removing SGP4 from the inference path. The implemented models instead predict the **residual** `y_true − y_SGP4_stale` and add it back to the SGP4-stale baseline (see NB02 §4 and NB04 `predict_corrected`). SGP4 therefore remains in the loop; the ML layer is a correction, not a replacement.
2. **"Ground truth" is itself SGP4.** The target series `y_true` is produced by propagating each satellite's *freshest available* TLE with SGP4 (NB01, cell 10). There is no independent measured ephemeris in the dataset. The learning target is thus the divergence between two SGP4 runs (fresh-TLE vs stale-TLE), i.e. SGP4's own analytic drag behaviour — not real physical error. This bounds what any model can achieve (see §7) and is the single most important caveat on the results below.

---

## 6. Experiments

Results are from the completed four-way benchmark on the held-out test set (**31,541 windows**, final 15% by time; training-log "Run 3", `STALE_DAYS = 3`). All figures are 3-D geodetic position error in km (great-circle surface distance combined in quadrature with altitude difference). The ML systems predict a residual on top of the SGP4-stale baseline (§5.6–§5.7).

### 6.1 Overall Accuracy

Columns T+10…T+120 are MAE in km; the final column is RMSE at T+60.

| System | T+10 | T+30 | T+60 | T+120 | RMSE T+60 |
|---|---|---|---|---|---|
| **SGP4-stale (baseline)** | **6.30** | **6.29** | **6.29** | **6.29** | **8.56** |
| Do-nothing (predict zero residual) | 6.31 | 6.31 | 6.31 | 6.31 | — |
| LSTM | 11.78 | 11.58 | 16.81 | 14.46 | 31.98 |
| Transformer | 19.46 | 26.71 | 26.79 | 24.67 | 37.39 |
| MLP (ablation) | 41.25 | 43.86 | 46.15 | 48.26 | 57.78 |

**The hypothesis is not supported.** No ML system beats the SGP4-stale baseline at any horizon. The decisive control is the *do-nothing* row: a model that emits a zero residual scores 6.31 km — indistinguishable from the baseline (a residual-scaler mean-shift of only `[-0.0001, -0.003, +0.062]` confirms there is no bias artefact). Every trained model therefore scores **worse than applying no correction at all**; the learned corrections add error rather than removing it. Error also grows with model flexibility in the wrong direction (MLP ≫ Transformer ≫ LSTM ≫ baseline), the signature of models fitting noise in the residual target.

### 6.2 Accuracy vs TLE Age (T+60)

| TLE Age | SGP4-stale | LSTM | Transformer | MLP |
|---|---|---|---|---|
| < 1 day | 6.39 | 17.01 | 27.00 | 46.40 |
| 1–3 days | 2.95 | 6.98 | 19.37 | 35.17 |
| 3–7 days | *no test samples* | — | — | — |
| > 7 days | *no test samples* | — | — | — |

The staleness hypothesis predicts an ML advantage precisely in the **> 3-day** cohorts — and those cohorts are empty. Because each TLE is propagated at most 3 days from its own epoch (NB01), the fresh-track TLE age used for binning never exceeds ~3 days, so the regime the experiment was designed to probe is not present in the data. Within the ages that *do* exist, the baseline is strongest exactly where SGP4 is expected to be strong (freshest TLEs), and the models never close the gap.

> **Reproducibility note (2026-07-18).** The numbers above are the committed NB04 outputs (a self-consistent Run-3 artifact set). Re-executing NB04 against the *current* `data/collected/` artifacts does **not** reproduce them: the on-disk `.npy` data + scalers are dated 2026-06-03 while the `.pt` weights are dated 2026-06-04 — they are **from different runs**. Evaluating mismatched artifacts yields LSTM ≈ 130 km and breaks the do-nothing control (6.98 km vs a 6.22 km baseline, i.e. a spurious bias). The residual scaler itself is pathological — `scale_ = [0.82, 8.96, 0.52]`, i.e. a **~9° longitude-residual std** caused by ±180° wrapping (see §7.3). Conclusions are unaffected (every model remains far worse than SGP4, only more so), but publication-grade numbers require one **self-consistent** NB02→NB03→NB04 run with matched artifacts. This artifact-versioning fragility is itself an argument for the single-machine v2 pipeline (`docs/RESEARCH_PLAN_V2.md`).

---

## 7. Discussion

The experiment returns a clear **negative result**: lightweight sequence models trained on TLE-derived position series do not beat SGP4 on this task. This is consistent across five training runs (see `CHANGELOG.md` → *ML Training Run Log*), and no amount of the tuning attempted (capacity increases, dropout, weight decay, Optuna/ASHA search) reversed it. Four structural reasons explain why, in decreasing order of importance:

1. **There is no independent ground truth — the ceiling is "tie SGP4."** Both the target and the baseline are SGP4 outputs (§5.7). The only learnable signal is the difference between a fresh-TLE and a stale-TLE SGP4 run, which is dominated by SGP4's own analytic along-track drag divergence — a quantity SGP4 already computes deterministically from `BSTAR` and elapsed time. A network cannot out-predict the physics model at reproducing the physics model; the best attainable score is to match the baseline, and the models fall short of even that.

2. **The residual target is small and noisy at 3-day staleness.** With a 3-day-old TLE the SGP4-stale error is only ~6 km, much of it near the numerical/geometric noise floor. There is little coherent structure for the model to capture, so it fits noise — the classic small-signal / flexible-model failure. (Raising `STALE_DAYS` to 7 in Run 4 to manufacture a larger residual is diagnostic of this problem, not a fix: it changes the *problem* to flatter the model rather than answering the original question, and the models still lost.)

3. **Residuals are learned in an ill-posed coordinate system.** Targets are geodetic `(lat°, lon°, alt km)` residuals, standard-scaled. One degree of longitude is ~111 km at the equator and ~0 km at the poles, and longitude wraps at ±180°, so a fixed-scale regression target is physically inconsistent across the globe. Position residuals should be expressed in an orbit-relative Cartesian frame (radial / along-track / cross-track, i.e. RIC) in km, where the dominant error (along-track) is a single well-behaved axis.

4. **The experiment cannot test its own central hypothesis.** As shown in §6.2, the dataset contains no windows in the > 3-day staleness regime where an ML advantage was predicted. Even a favourable outcome in the measured cohorts would not have confirmed the hypothesis.

Taken together, these are design-level issues, not hyperparameter issues. Deeper networks or longer searches cannot overcome a target that is bounded above by the baseline it is trying to beat.

---

## 8. Conclusion

Within the scope studied — TLE-only data, SGP4-derived targets, LEO satellites, limited (single-GPU / Colab) compute — **deep sequence models do not improve on SGP4 for multi-horizon orbit prediction, and in practice degrade it.** The result is robust across architectures (MLP, LSTM, Transformer), across five training runs, and against a correctly-constructed strong baseline with a verified do-nothing control.

This is a genuine and useful finding: it rules out a tempting but ill-posed approach and localises *why* it fails. The productive next step is not a bigger model but a better-posed problem. Specifically (see §9 and `docs/RESEARCH_PLAN_V2.md`):

- Replace SGP4-vs-SGP4 targets with a proxy for **real** SGP4 error — the divergence of each TLE from the *next* independently-fitted TLE at its epoch (the standard Peng & Bai formulation [5, 6]).
- Add **space-weather drivers** (F10.7, Ap/Kp) — the physical cause of drag error that SGP4 cannot see and the only place a genuine learnable signal exists.
- Learn residuals in the **RIC** frame (km), not geodetic degrees.
- Use **gradient-boosted trees** (LightGBM) rather than deep nets: better suited to this small, tabular, low-signal regression, and trainable in seconds on CPU — a direct match for the project's compute constraints.

---

## 9. Future Work

- **Stronger SGP4 baseline:** Re-propagate the most recent TLE for each test window (requires storing the TLE alongside each window) rather than using static dead-reckoning.
- **Online fine-tuning:** Given a stream of newly published TLEs, fine-tune the model on recent observations to adapt to secular changes in drag (e.g., due to varying solar activity).
- **Uncertainty quantification:** Replace point estimates with predictive intervals (e.g., MC dropout or conformal prediction) to enable probabilistic conjunction analysis.
- **GEO satellites:** The current study focuses on LEO/MEO. Geostationary satellites have different error profiles (less drag, more solar-radiation pressure), and separate models may be required.
- **Integration with Streamlit dashboard:** Expose model predictions as an optional tab alongside SGP4 in the existing visualisation application.

---

## References

[1] Hoots, F. R., & Roehrich, R. L. (1980). *Spacetrack Report No. 3: Models for Propagation of NORAD Element Sets*. USAF Aerospace Defense Command.

[2] Vallado, D. A., Crawford, P., Hujsak, R., & Kelso, T. S. (2006). Revisiting Spacetrack Report #3. *AIAA 2006-6753*. https://doi.org/10.2514/6.2006-6753

[3] Hochreiter, S., & Schmidhuber, J. (1997). Long Short-Term Memory. *Neural Computation*, 9(8), 1735–1780. https://doi.org/10.1162/neco.1997.9.8.1735

[4] Vaswani, A., Shazeer, N., Parmar, N., Uszkoreit, J., Jones, L., Gomez, A. N., Kaiser, Ł., & Polosukhin, I. (2017). Attention is All You Need. *Advances in Neural Information Processing Systems*, 30.

[5] Peng, H., & Bai, X. (2018). Artificial Neural Network–Based Machine Learning Approach to Improve Orbit Prediction Accuracy. *Journal of Spacecraft and Rockets*, 55(5), 1248–1260. https://doi.org/10.2514/1.A34171

[6] Peng, H., & Bai, X. (2019). Exploring the Capability of Machine Learning for Improving Satellite Orbit Prediction Accuracy. *Journal of Aerospace Information Systems*, 16(5), 154–165. https://doi.org/10.2514/1.I010761

---

*Last updated: see git log. Experimental results (Sections 6–8) will be populated after completing Notebooks 03 and 04.*
