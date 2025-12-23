"""
Integrated pipeline for SGP4 prediction with ML correction.

Combines SGP4 orbit propagation with ML-based residual prediction for improved accuracy.
"""

from datetime import datetime, timedelta
import numpy as np
import sys
from pathlib import Path

# Import v1_0 physics
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "v1_0_basic_pass_predictor"))
from src.tle_loader import load_tle
from src.propagator import propagate_satellite, gmst_angle
from src.ground_station import GroundStation
from src.pass_detector import detect_passes

# Import ML correction
from ml.predict import ResidualCorrector, apply_correction_to_position


def extract_tle_parameters(line1: str, line2: str) -> dict:
    """
    Extract orbital parameters from TLE lines.
    
    Args:
        line1: TLE line 1
        line2: TLE line 2
    
    Returns:
        Dictionary with mean_motion, eccentricity, inclination
    """
    # TLE format (simplified parsing)
    try:
        # Line 1: satellite number, epoch year-day, etc.
        epoch_year = int(line1[18:20])
        epoch_day = float(line1[20:32])
        
        # Line 2: inclination, RAAN, eccentricity, argument of perigee, mean anomaly, mean motion
        inclination = float(line2[8:16])
        eccentricity = float("0." + line2[26:33])
        mean_motion = float(line2[52:63])
        
        return {
            'inclination_deg': inclination,
            'eccentricity': eccentricity,
            'mean_motion_rev_per_day': mean_motion
        }
    except (ValueError, IndexError):
        # Return defaults if parsing fails
        return {
            'inclination_deg': 97.0,
            'eccentricity': 0.0005,
            'mean_motion_rev_per_day': 15.0
        }


def compute_time_since_epoch(tle_line1: str, current_utc: datetime) -> float:
    """
    Compute hours since TLE epoch to current time.
    
    Args:
        tle_line1: TLE line 1 (contains epoch)
        current_utc: Current UTC datetime
    
    Returns:
        Hours since epoch
    """
    try:
        epoch_year = int(tle_line1[18:20])
        epoch_day = float(tle_line1[20:32])
        
        # Convert to 4-digit year
        if epoch_year < 57:
            full_year = 2000 + epoch_year
        else:
            full_year = 1900 + epoch_year
        
        # Epoch date
        epoch_utc = datetime(full_year, 1, 1) + timedelta(days=epoch_day - 1)
        
        # Hours since epoch
        delta = current_utc - epoch_utc
        return delta.total_seconds() / 3600.0
    except:
        return 0.0


class CorrectedPropagator:
    """
    Combines SGP4 propagation with ML-based residual correction.
    """
    
    def __init__(self, model_path: str):
        """
        Initialize propagator with ML correction.
        
        Args:
            model_path: Path to trained PyTorch model
        """
        self.corrector = ResidualCorrector(model_path)
    
    def propagate_with_correction(
        self,
        line1: str,
        line2: str,
        current_utc: datetime,
        apply_ml_correction: bool = True
    ) -> tuple:
        """
        Propagate satellite position with optional ML correction.
        
        Args:
            line1: TLE line 1
            line2: TLE line 2
            current_utc: Current UTC datetime
            apply_ml_correction: Whether to apply ML correction
        
        Returns:
            (position_ecef_km, velocity_ecef_km_s, correction_km)
        """
        # Standard SGP4 propagation
        pos_ecef, vel_ecef = propagate_satellite(line1, line2, current_utc)
        
        correction_km = 0.0
        
        if apply_ml_correction:
            # Extract orbital parameters
            tle_params = extract_tle_parameters(line1, line2)
            time_since_epoch = compute_time_since_epoch(line1, current_utc)
            
            # Predict residual
            residual = self.corrector.predict_residual(
                time_since_epoch,
                tle_params['mean_motion_rev_per_day'],
                tle_params['eccentricity'],
                tle_params['inclination_deg']
            )
            
            # Apply correction
            pos_ecef = apply_correction_to_position(pos_ecef, vel_ecef, residual)
            correction_km = residual
        
        return pos_ecef, vel_ecef, correction_km


def predict_passes_with_correction(
    tle_path: str,
    model_path: str,
    start_utc: datetime,
    end_utc: datetime,
    step_seconds: int,
    ground_station: GroundStation,
    threshold_deg: float,
    apply_correction: bool = True
) -> tuple:
    """
    Predict passes with optional ML correction.
    
    Args:
        tle_path: Path to TLE file
        model_path: Path to trained ML model
        start_utc: Start time
        end_utc: End time
        step_seconds: Propagation step
        ground_station: Observer location
        threshold_deg: Elevation threshold
        apply_correction: Apply ML correction
    
    Returns:
        (passes_list, corrections_list)
    """
    # Load TLE
    sat_name, line1, line2 = load_tle(tle_path)
    
    # Initialize propagator
    propagator = CorrectedPropagator(model_path)
    
    # Time grid
    times = []
    current = start_utc
    while current <= end_utc:
        times.append(current)
        current += timedelta(seconds=step_seconds)
    
    elevations = []
    corrections = []
    
    for t in times:
        # Propagate with correction
        pos_ecef, vel_ecef, correction = propagator.propagate_with_correction(
            line1, line2, t, apply_ml_correction=apply_correction
        )
        corrections.append(correction)
        
        # Compute elevation
        elevation = ground_station.elevation_deg(pos_ecef)
        elevations.append(elevation)
    
    # Detect passes using v1_0 function
    passes = detect_passes(times, elevations, threshold_deg)
    
    return passes, corrections
