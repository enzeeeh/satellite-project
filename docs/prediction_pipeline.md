# Satellite Pass Prediction: How It Works

A practical walkthrough of how the project turns 3 lines of TLE text plus a ground station location into predicted satellite passes, with optional machine-learning residual corrections.

## Inputs
- Two-Line Element (TLE) set (3 lines including name)
- Ground station geodetic coordinates (lat, lon, altitude)
- Time window and step size (e.g., 48 hours, 30 s)

## Pipeline at a Glance
1) Parse TLE → orbital elements
2) Propagate with SGP4 → TEME position/velocity over time
3) Rotate TEME → ECEF using GMST (Earth rotation)
4) Convert ground station WGS84 → ECEF
5) Relative geometry: ECEF → ENU → elevation/azimuth
6) Detect passes with elevation threshold crossings
7) (Optional) Apply ML residual correction along track
8) Output pass list, plots, JSON

## Part 1 — TLE: Orbit in Three Lines
TLE encodes six classical orbital elements plus metadata:
- Inclination, RAAN, eccentricity, argument of perigee, mean anomaly, mean motion
- Epoch (time of validity), drag term, revolution count
These fully determine the Keplerian orbit; perturbation terms guide SGP4 on drag and Earth oblateness effects.

## Part 2 — SGP4 Propagation (Where is the satellite?)
SGP4 integrates orbital elements forward in time, adding key perturbations:
- $J_2$ Earth oblateness, atmospheric drag, solar/lunar gravity, radiation pressure (simplified)
- Outputs TEME-frame position $\vec r$ and velocity $\vec v$ (km, km/s) at each timestamp.

## Part 3 — Coordinate Transforms (Space-fixed → Earth-fixed)
1) Compute GMST $\theta_{GMST}(t)$ to account for Earth rotation.
2) Rotate TEME → ECEF via a Z-rotation by $\theta_{GMST}$:
   \[
   \begin{bmatrix}x_{ECEF}\\y_{ECEF}\\z_{ECEF}\end{bmatrix}=
   \begin{bmatrix}\cos\theta & -\sin\theta & 0\\ \sin\theta & \cos\theta & 0\\ 0 & 0 & 1\end{bmatrix}
   \begin{bmatrix}x_{TEME}\\y_{TEME}\\z_{TEME}\end{bmatrix}
   \]
3) Ground station WGS84 geodetic → ECEF using ellipsoid radii (accounts for flattening).
4) Relative position: $\Delta = r_{sat,ECEF} - r_{gs,ECEF}$.
5) Rotate ECEF → ENU (local horizon frame) and compute elevation:
   $\text{elev} = \arctan2(u, \sqrt{e^2+n^2}) \times 180/\pi$.

## Part 4 — Pass Detection (When is it visible?)
**What happens:** sample elevation over time (e.g., every 30 s) and find where it crosses a visibility threshold (default 10°).

**Threshold-based state machine:**
- States: NOT_IN_PASS → IN_PASS when elevation crosses upward through threshold; revert when it crosses downward.
- Crossing times are linearly interpolated between samples for precise AOS/LOS.
- Outputs per pass: start (AOS), peak time/elevation, end (LOS).

**Why threshold crossing?**
- Directly encodes “above horizon and clear enough” with minimal assumptions.
- Robust to noisy samples: only sign changes around the threshold matter.
- Fast: $O(N)$ over time samples; no root-finding or heavy optimization needed.
- Transparent: easy to audit and tune (e.g., change threshold for different antennas).

**What about other methods?**
- **Continuous root-finding on elevation(t):** solve elevation(t)=0 with higher-order interpolation; more complex and rarely needed for minute-level planning.
- **Smoothing + derivative tests:** fit splines to elevation then find zeros and maxima; adds numerical complexity with limited benefit at 30 s cadence.
- **Probabilistic/HMM approaches:** model visibility as latent states with emission noise; useful for noisy sensor data, overkill for deterministic SGP4 outputs.
- **Direct geometric horizon test without sampling:** derive rise/set analytically from orbit and station vectors; more intricate for perturbed orbits and rotating Earth.

**How do we know the trajectory with only 3 lines?**
- The two orbital-element lines encode a full dynamical model; SGP4 integrates those elements continuously, giving position/velocity at any time. The “three lines” are not sparse samples; they are the parameters of the orbit, so we can reconstruct the entire trajectory deterministically within the TLE’s validity window.

## Part 5 — ML Residual Correction (Why FCN, what else?)
**Goal:** reduce along-track error that accumulates as TLE ages (drag, unmodeled forces).

**Chosen model: Fully-Connected Network (FCN)**
- Inputs: [time since epoch (h), mean motion (rev/day), eccentricity, inclination (deg)].
- Layers: 64 → 32 → 16 (ReLU + dropout), then 1 output = along-track error (km).
- Reasoning: small, tabular feature set; FCN is light, fast, and expressive enough for smooth residual mappings. CNNs are for spatial grids/images, not needed here.
- Application: predict residual, unit-velocity vector = $\hat v = \vec v/\lVert\vec v\rVert$, correction = $\hat v \times \text{residual}$, add to ECEF position.

**Alternative methods (when/why):**
- **Gradient-boosted trees (XGBoost/LightGBM):** strong tabular regressors; fast to train, good with mixed feature scales; less smooth extrapolation in time.
- **Random forest:** simple baseline; robust but can be noisy for continuous residuals and extrapolations.
- **Gaussian Process Regression:** provides uncertainty; good for small datasets; scales poorly with large data.
- **Polynomial/basis-function regression:** lightweight, interpretable; may underfit complex residual patterns.
- **Kalman filter / Extended Kalman / Unscented Kalman:** state-space approach using measurements (if available) to fuse predicted and observed positions; great when you have live tracking data.
- **Sequence models (RNN/LSTM/Transformer):** if you have time-series of observed errors, they can model temporal drift; more data-hungry and heavier.

**Why not CNN here?**
- No spatial grid structure; only 4 scalar features per sample. CNN inductive bias (local spatial filters) does not help and adds complexity.

## Part 6 — Outputs
- Pass list: AOS, peak time/elevation, LOS, max elevation
- Optional plots: elevation vs. time, ground track maps
- Optional JSON: for automation/integration

## Practical Notes
- Accuracy depends on TLE age; corrections help most when TLE is several hours to days old.
- Step size trades speed vs. temporal resolution of AOS/LOS; smaller steps yield more precise crossings.
- Threshold should match antenna horizon mask and desired link margin; 5–15° is common.
