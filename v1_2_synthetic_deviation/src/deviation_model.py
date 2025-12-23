"""
Orbital deviation model for synthetic truth generation.

Simulates three types of orbital prediction errors:
1. Along-track drift: Linear growth in along-track position error
2. Cross-track noise: Random walk perpendicular to velocity
3. Timing perturbation: Random shift in pass start/end times
"""

import numpy as np
from datetime import timedelta
from typing import Tuple


def perturb_position(
    pos_ecef: np.ndarray,
    vel_ecef: np.ndarray,
    time_since_epoch_hours: float,
    along_track_rate_km_per_hour: float = 0.05,
    cross_track_sigma_km: float = 0.02,
    seed: int = None
) -> np.ndarray:
    """
    Perturb an ECEF position to simulate orbital prediction error.
    
    Args:
        pos_ecef: ECEF position [x, y, z] in km
        vel_ecef: ECEF velocity [vx, vy, vz] in km/s
        time_since_epoch_hours: Hours since reference epoch
        along_track_rate_km_per_hour: Along-track drift rate (km/hour)
        cross_track_sigma_km: Cross-track noise std dev (km)
        seed: Random seed for reproducibility
    
    Returns:
        Perturbed ECEF position [x, y, z] in km
    """
    if seed is not None:
        seed = int(seed) % (2**32)  # Ensure seed is within valid range
        np.random.seed(seed)
    
    # Normalize velocity to get along-track unit vector
    vel_mag = np.linalg.norm(vel_ecef)
    along_track_unit = vel_ecef / vel_mag if vel_mag > 0 else np.array([1, 0, 0])
    
    # Create orthogonal cross-track vectors using Gram-Schmidt
    # First perpendicular: position-based
    radial_unit = pos_ecef / np.linalg.norm(pos_ecef)
    cross1 = np.cross(along_track_unit, radial_unit)
    cross1 = cross1 / np.linalg.norm(cross1)
    cross2 = np.cross(along_track_unit, cross1)
    cross2 = cross2 / np.linalg.norm(cross2)
    
    # Apply along-track drift
    along_track_offset = along_track_rate_km_per_hour * time_since_epoch_hours
    pos_perturbed = pos_ecef + along_track_offset * along_track_unit
    
    # Apply cross-track noise
    cross_noise1 = np.random.normal(0, cross_track_sigma_km)
    cross_noise2 = np.random.normal(0, cross_track_sigma_km)
    pos_perturbed = pos_perturbed + cross_noise1 * cross1 + cross_noise2 * cross2
    
    return pos_perturbed


def perturb_pass_times(
    pass_start_utc,
    pass_end_utc,
    max_timing_error_minutes: float = 2.0,
    seed: int = None
) -> Tuple:
    """
    Add random timing perturbations to pass start/end times.
    
    Args:
        pass_start_utc: AOS datetime
        pass_end_utc: LOS datetime
        max_timing_error_minutes: Maximum ±timing error (minutes)
        seed: Random seed for reproducibility
    
    Returns:
        (perturbed_start, perturbed_end) as datetime objects
    """
    if seed is not None:
        seed = int(seed) % (2**32)  # Ensure seed is within valid range
        np.random.seed(seed)
    
    start_error_minutes = np.random.uniform(-max_timing_error_minutes, max_timing_error_minutes)
    end_error_minutes = np.random.uniform(-max_timing_error_minutes, max_timing_error_minutes)
    
    perturbed_start = pass_start_utc + timedelta(minutes=float(start_error_minutes))
    perturbed_end = pass_end_utc + timedelta(minutes=float(end_error_minutes))
    
    return perturbed_start, perturbed_end


def compute_position_error(pos_sgp4_km: np.ndarray, pos_truth_km: np.ndarray) -> float:
    """
    Compute Euclidean distance error between SGP4 and truth positions.
    
    Args:
        pos_sgp4_km: SGP4 position [x, y, z] in km
        pos_truth_km: Truth position [x, y, z] in km
    
    Returns:
        Position error in km
    """
    return float(np.linalg.norm(pos_truth_km - pos_sgp4_km))


def compute_timing_error(time_sgp4, time_truth) -> float:
    """
    Compute timing error in seconds.
    
    Args:
        time_sgp4: SGP4 prediction (datetime)
        time_truth: Truth value (datetime)
    
    Returns:
        Timing error in seconds
    """
    delta = time_truth - time_sgp4
    return delta.total_seconds()
