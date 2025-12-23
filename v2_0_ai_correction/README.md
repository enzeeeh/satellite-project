# v2.0 — AI-Corrected Orbital Pass Prediction

## Overview
Combines **SGP4 orbit propagation** with **PyTorch neural networks** to predict and correct orbital modeling errors. Trains on synthetic residuals to learn the systematic biases in TLE-based predictions, then applies ML corrections for improved accuracy.

## Architecture

### Three-Layer Pipeline
1. **SGP4 Baseline** — Standard orbit propagation from TLE
2. **ML Prediction** — Neural network predicts along-track residual
3. **Position Correction** — Apply residual correction to ECEF coordinates

### Model Details
- **Input features** (4):
  - `time_since_tle_epoch_hours` — Age of TLE data
  - `mean_motion_rev_per_day` — Orbital period (revolutions/day)
  - `eccentricity` — Orbit shape parameter
  - `inclination_deg` — Orbit inclination

- **Architecture**:
  - Fully connected neural network
  - Hidden layers: 64 → 32 → 16 neurons
  - ReLU activations
  - Dropout (0.1) for regularization
  - Single output: along-track position error (km)

- **Training**:
  - Loss: Mean squared error (MSE)
  - Optimizer: Adam (lr=0.001)
  - Epochs: 50 (default)
  - Train/val split: 80/20
  - Synthetic data: 500 samples (ISS-like orbits)

## Usage

### Step 1: Train the Model
Generate synthetic training data and train the neural network:
```bash
python -m v2_0_ai_correction.src.main train \
  --epochs 50 \
  --batch-size 32 \
  --learning-rate 0.001 \
  --num-samples 500 \
  --data-dir data \
  --model-dir models
```

This will:
1. Generate 500 synthetic samples with realistic orbital variations
2. Split into 400 training + 100 validation samples
3. Train for 50 epochs
4. Save the best model to `models/residual_model.pt`
5. Report validation RMSE

### Step 2: Use Trained Model for Predictions
Predict passes with ML-based corrections:
```bash
python -m v2_0_ai_correction.src.main predict \
  --tle v1_0_basic_pass_predictor/data/tle.txt \
  --model models/residual_model.pt \
  --hours 24 \
  --step 300 \
  --threshold 10.0
```

Disable corrections for comparison (baseline SGP4):
```bash
python -m v2_0_ai_correction.src.main predict \
  --tle v1_0_basic_pass_predictor/data/tle.txt \
  --model models/residual_model.pt \
  --hours 24 \
  --step 300 \
  --no-correction
```

### Custom Ground Station
```bash
python -m v2_0_ai_correction.src.main predict \
  --tle v1_0_basic_pass_predictor/data/tle.txt \
  --model models/residual_model.pt \
  --station-lat 51.5 \
  --station-lon -0.1 \
  --station-alt 0.01
```

## Output

### Training Output
```
Generated 400 training samples -> data/train.csv
Generated 100 validation samples -> data/val.csv
Using device: cuda

Training for 50 epochs...
Epoch 1  | Train Loss: 0.052341 | Val Loss: 0.048923
Epoch 10 | Train Loss: 0.012453 | Val Loss: 0.011892
Epoch 50 | Train Loss: 0.001234 | Val Loss: 0.001456

Final validation (on best model):
  RMSE: 0.038145 km
  Model saved to: models/residual_model.pt
```

### Prediction Output
```
Predicting passes (correction: ON)
  TLE: v1_0_basic_pass_predictor/data/tle.txt
  Model: models/residual_model.pt
  Window: 2025-12-23T04:00:00 to 2025-12-24T04:00:00
  Station: (40.0°, -105.0°, 1.6km)

Detected 4 passes

Pass predictions:
  Pass 1: 2025-12-23T04:49:30Z to 2025-12-23T04:56:25Z
    Max elevation: 26.31°
  Pass 2: 2025-12-23T06:24:58Z to 2025-12-23T06:31:35Z
    Max elevation: 23.05°
  ...

ML Correction statistics:
  Mean correction: 0.0342 km
  Std deviation: 0.0156 km
  Range: [-0.0234, 0.0892] km
```

## Synthetic Data Generation

The training data is **synthetically generated** with:
- Time-dependent drift: `0.05 * hours_since_epoch`
- Eccentricity effect: `0.1 * eccentricity * 100`
- Inclination bias: `0.001 * (inclination - 97°)`
- Gaussian noise: `N(0, 0.02 km)`
- Clipped range: `[-0.5, +0.5] km`

This simulates realistic TLE aging: older TLEs accumulate growing errors proportional to orbital parameters.

## How ML Correction Works

1. **Extract orbital parameters** from TLE lines
2. **Compute TLE age** (hours since epoch date)
3. **Network inference**: 4 inputs → 1 residual prediction
4. **Apply correction**: Offset SGP4 position in along-track direction
5. **Compute elevation** from corrected position
6. **Detect passes** using corrected trajectory

## Key Files

- `src/ml/model.py` — Neural network architecture
- `src/ml/train.py` — Training loop, synthetic data generation
- `src/ml/predict.py` — Inference, correction application
- `src/pipeline.py` — Integration with v1_0 physics
- `src/main.py` — CLI entry point
- `models/residual_model.pt` — Trained weights (after training)

## Performance Notes

- **Inference time**: ~1ms per propagation (CPU)
- **GPU support**: Automatic CUDA detection (uses GPU if available)
- **Model size**: ~50KB (very lightweight)
- **Typical RMSE**: 0.03-0.05 km on validation set

## ML Workflow for Future Improvements

1. **Collect real residuals**: Compare SGP4 vs. actual observations
2. **Retrain model**: Feed real data instead of synthetic
3. **Cross-validate**: Test on held-out satellite passes
4. **Ensemble**: Combine multiple models for robustness
5. **Temporal features**: Add time-of-day, season, solar activity

## Dependencies
- `sgp4` (≥2.22): Orbital propagation
- `torch` (≥2.0.0): PyTorch neural network framework
- `numpy` (≥1.23): Numerical operations

## See Also
- v1.0: Core SGP4 pass prediction
- v1.1: Visualization of passes
- v1.2: Synthetic residual generation
