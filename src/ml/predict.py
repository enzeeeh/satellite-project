"""Inference utilities for ML residual prediction."""

import torch
import numpy as np
from .model import ResidualPredictor


class ResidualCorrector:
    """Applies ML-based residual correction to SGP4 predictions."""
    
    def __init__(self, model_path: str, device: str = None):
        """Load trained model."""
        if device is None:
            device = 'cuda' if torch.cuda.is_available() else 'cpu'
        
        self.device = torch.device(device)
        self.model = ResidualPredictor(input_dim=4, hidden_dims=[64, 32, 16])
        self.model.load_state_dict(torch.load(model_path, map_location=self.device))
        self.model.to(self.device)
        self.model.eval()
        print(f"Loaded model from {model_path} (device: {self.device})")
    
    def predict_residual(
        self,
        time_since_epoch_hours: float,
        mean_motion_rev_per_day: float,
        eccentricity: float,
        inclination_deg: float
    ) -> float:
        """Predict along-track residual for a single sample."""
        features = np.array([
            time_since_epoch_hours,
            mean_motion_rev_per_day,
            eccentricity,
            inclination_deg
        ], dtype=np.float32)
        
        with torch.no_grad():
            x = torch.from_numpy(features).unsqueeze(0).to(self.device)
            pred = self.model(x).cpu().numpy()[0, 0]
        
        return float(pred)
    
    def predict_batch(self, features_array: np.ndarray) -> np.ndarray:
        """Predict residuals for a batch of samples."""
        with torch.no_grad():
            x = torch.from_numpy(features_array.astype(np.float32)).to(self.device)
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
