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

The *SGP4 baseline* repeats the last observed position (from the final timestep of the input window) as the prediction for all four horizons. This is equivalent to zero-velocity dead reckoning and represents the accuracy of a stale TLE without any learned correction.

> **Note:** A stronger baseline would propagate each test window's most recent TLE directly with SGP4. This is left as a future extension (see Section 9).

---

## 6. Experiments

*Results to be filled after running Notebooks 03 and 04.*

### 6.1 Overall Accuracy

| Model | MAE T+10 | MAE T+30 | MAE T+60 | MAE T+120 | RMSE T+60 |
|---|---|---|---|---|---|
| SGP4 baseline | — | — | — | — | — |
| LSTM | — | — | — | — | — |
| Transformer | — | — | — | — | — |

### 6.2 Accuracy vs TLE Age (T+60)

| TLE Age | SGP4 MAE | LSTM MAE | Transformer MAE |
|---|---|---|---|
| < 1 day | — | — | — |
| 1–3 days | — | — | — |
| 3–7 days | — | — | — |
| > 7 days | — | — | — |

---

## 7. Discussion

*To be written after experiments.*

Expected findings based on the literature and the project hypothesis:
- The ML models should match or exceed SGP4 accuracy at all horizons when the TLE is fresh (< 1 day), since the 90-minute input window captures the satellite's current dynamical state.
- The advantage of the ML models is expected to be largest for TLE ages > 3 days, where SGP4 accumulates significant unmodelled drag error but the model's learned dynamics remain anchored to recent observations.
- The Transformer may outperform the LSTM on longer horizons (T+120) due to its ability to attend to non-contiguous patterns in the input window (e.g., re-entry of the satellite into eclipse, which has a consistent effect on drag).

---

## 8. Conclusion

*To be written after experiments.*

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
