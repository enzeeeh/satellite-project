"""Inference utilities for ML residual prediction."""

import json
import math
import torch
import numpy as np
from pathlib import Path
from .model import ResidualPredictor

# Physical constants — must match the notebook's orbital_features() exactly
_MU_KM3_S2  = 398600.4418   # Earth gravitational parameter (km³/s²)
_R_EARTH_KM = 6371.0        # mean Earth radius (km)


def features_from_satrec(sat, time_since_epoch_hours: float) -> list:
    """Compute the 6 training features from a sgp4 Satrec object.

    This function uses the **identical** formula as the notebook's
    ``orbital_features()`` so training and inference are always consistent.

    Feature order (matches FEATURE_NAMES in the notebook):
      0  time_since_epoch_hours
      1  mean_motion_rev_per_day  — no_kozai [rad/min] × 1440 ÷ 2π
      2  eccentricity
      3  inclination_deg
      4  bstar
      5  altitude_km              — (µ / (no_kozai/60)²)^(1/3) − R_earth
    """
    no_rad_min  = sat.no_kozai                             # rad/min (native sgp4)
    no_rad_s    = no_rad_min / 60.0                        # rad/s for Kepler
    # NOTE: training data used no_rad_s * 1440/(2π) ≈ 0.25 — must match model.
    # Update to no_rad_min * 1440/(2π) after retraining with corrected notebook.
    mean_motion = no_rad_s * (1440.0 / (2 * math.pi))     # matches training (~0.25)
    a_km        = (_MU_KM3_S2 / no_rad_s ** 2) ** (1.0 / 3.0)
    altitude_km = a_km - _R_EARTH_KM
    return [
        time_since_epoch_hours,
        mean_motion,
        sat.ecco,
        math.degrees(sat.inclo),
        sat.bstar,
        altitude_km,
    ]


class ResidualCorrector:
    """Applies ML-based residual correction to SGP4 predictions."""

    def __init__(self, model_path: str, device: str = None):
        """Load trained model and optional normalisation stats.

        If a ``<model_path_stem>.json`` file exists next to the model weights,
        the feature normalisation (mean / std) saved during training is loaded
        and applied automatically at inference time.
        """
        if device is None:
            device = 'cuda' if torch.cuda.is_available() else 'cpu'

        self.device = torch.device(device)
        # Load normalisation stats to determine architecture at runtime
        stats_path = Path(model_path).with_suffix('.json')
        if stats_path.exists():
            with open(stats_path) as f:
                stats = json.load(f)
            hidden_dims = stats.get('hidden_dims', [256, 128, 64, 32])
            input_dim   = stats.get('input_dim',   6)
            self.X_mean = np.array(stats['X_mean'], dtype=np.float32)
            self.X_std  = np.array(stats['X_std'],  dtype=np.float32)
        else:
            # Fallback defaults matching notebook training config
            hidden_dims = [256, 128, 64, 32]
            input_dim   = 6
            self.X_mean = np.zeros(input_dim, dtype=np.float32)
            self.X_std  = np.ones(input_dim,  dtype=np.float32)

        self.model = ResidualPredictor(input_dim=input_dim, hidden_dims=hidden_dims)
        self.model.load_state_dict(torch.load(model_path, map_location=self.device,
                                              weights_only=True))
        self.model.to(self.device)
        self.model.eval()

        print(f"Loaded model from {model_path} (device: {self.device})")

    def predict_residual(
        self,
        time_since_epoch_hours: float,
        mean_motion_rev_per_day: float,
        eccentricity: float,
        inclination_deg: float,
        bstar: float = 0.0,
        altitude_km: float = 500.0,
    ) -> float:
        """Predict along-track residual for a single sample (explicit features)."""
        features = np.array([
            time_since_epoch_hours,
            mean_motion_rev_per_day,
            eccentricity,
            inclination_deg,
            bstar,
            altitude_km,
        ], dtype=np.float32)

        # Apply same normalisation used during training
        features = (features - self.X_mean) / self.X_std

        with torch.no_grad():
            x = torch.from_numpy(features).unsqueeze(0).to(self.device)
            pred = self.model(x).cpu().numpy()[0, 0]

        return float(pred)

    def predict_from_satrec(self, sat, time_since_epoch_hours: float) -> float:
        """Predict along-track residual directly from a sgp4 Satrec object.

        Preferred over ``predict_residual`` because feature extraction is
        done by the shared ``features_from_satrec()`` helper, guaranteeing
        the same formula is used at training time and inference time.
        """
        feats = features_from_satrec(sat, time_since_epoch_hours)
        return self.predict_residual(*feats)

    def predict_batch(self, features_array: np.ndarray) -> np.ndarray:
        """Predict residuals for a batch of samples (un-normalised features)."""
        normed = (features_array.astype(np.float32) - self.X_mean) / self.X_std
        with torch.no_grad():
            x = torch.from_numpy(normed).to(self.device)
            preds = self.model(x).cpu().numpy().flatten()
        return preds


def apply_correction_to_position(
    position_ecef_km: tuple,
    velocity_ecef_km_s: tuple,
    residual_km: float
) -> tuple:
    """Apply along-track residual correction to ECEF position."""
    pos = np.array(position_ecef_km)
    vel = np.array(velocity_ecef_km_s)
    
    # Normalize velocity to get along-track direction
    vel_mag = np.linalg.norm(vel)
    if vel_mag == 0:
        return position_ecef_km
    
    along_track = vel / vel_mag
    correction = along_track * residual_km
    
    corrected_pos = pos + correction
    return tuple(corrected_pos.tolist())
