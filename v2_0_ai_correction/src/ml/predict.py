"""
Inference utilities for orbital residual prediction.

Load trained model and apply corrections to SGP4 predictions.
"""

import torch
import numpy as np
from pathlib import Path
from .model import ResidualPredictor


class ResidualCorrector:
    """Applies ML-based residual correction to SGP4 predictions."""
    
    def __init__(self, model_path: str, device: str = None):
        """
        Load trained model.
        
        Args:
            model_path: Path to saved model weights
            device: 'cuda' or 'cpu'
        """
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
        """
        Predict along-track residual for a single sample.
        
        Args:
            time_since_epoch_hours: Hours since TLE epoch
            mean_motion_rev_per_day: Mean motion (revolutions/day)
            eccentricity: Orbital eccentricity
            inclination_deg: Inclination (degrees)
        
        Returns:
            Predicted along-track position error (km)
        """
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
        """
        Predict residuals for a batch of samples.
        
        Args:
            features_array: Array of shape (N, 4) with orbital elements
        
        Returns:
            Array of shape (N,) with predicted residuals
        """
        with torch.no_grad():
            x = torch.from_numpy(features_array.astype(np.float32)).to(self.device)
            preds = self.model(x).cpu().numpy().flatten()
        
        return preds


def apply_correction_to_position(
    position_ecef_km: tuple,
    velocity_ecef_km_s: tuple,
    residual_km: float
) -> tuple:
    """
    Apply along-track residual correction to ECEF position.
    
    Args:
        position_ecef_km: (x, y, z) in km
        velocity_ecef_km_s: (vx, vy, vz) in km/s
        residual_km: Along-track residual to apply
    
    Returns:
        Corrected position (x, y, z) in km
    """
    pos = np.array(position_ecef_km)
    vel = np.array(velocity_ecef_km_s)
    
    # Normalize velocity to along-track direction
    vel_mag = np.linalg.norm(vel)
    if vel_mag > 0:
        along_track_unit = vel / vel_mag
    else:
        along_track_unit = np.array([1.0, 0.0, 0.0])
    
    # Apply residual as offset in along-track direction
    corrected_pos = pos + residual_km * along_track_unit
    
    return tuple(corrected_pos)
