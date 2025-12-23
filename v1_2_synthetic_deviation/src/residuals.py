"""
Residual analysis and statistics computation.

Compares SGP4 predictions against perturbed truth and generates statistics.
"""

import json
from typing import List, Dict, Any
from datetime import datetime
import numpy as np


class ResidualStats:
    """Container for residual statistics."""
    
    def __init__(self):
        self.position_errors_km = []
        self.timing_errors_sec = []
        self.aos_errors_sec = []
        self.los_errors_sec = []
        self.max_elevation_errors_deg = []
        self.pass_count = 0
    
    def add_pass_residual(
        self,
        position_error: float,
        aos_error: float,
        los_error: float,
        max_el_error: float
    ):
        """Record residuals for a single pass."""
        self.position_errors_km.append(position_error)
        self.aos_errors_sec.append(aos_error)
        self.los_errors_sec.append(los_error)
        self.max_elevation_errors_deg.append(max_el_error)
        self.pass_count += 1
    
    def compute_stats(self) -> Dict[str, Any]:
        """Compute summary statistics."""
        if self.pass_count == 0:
            return {
                "pass_count": 0,
                "position_error_km": {},
                "aos_error_sec": {},
                "los_error_sec": {},
                "max_elevation_error_deg": {}
            }
        
        def stats_dict(errors):
            return {
                "mean": float(np.mean(errors)),
                "std": float(np.std(errors)),
                "min": float(np.min(errors)),
                "max": float(np.max(errors)),
                "median": float(np.median(errors))
            }
        
        return {
            "pass_count": self.pass_count,
            "position_error_km": stats_dict(self.position_errors_km),
            "aos_error_sec": stats_dict(self.aos_errors_sec),
            "los_error_sec": stats_dict(self.los_errors_sec),
            "max_elevation_error_deg": stats_dict(self.max_elevation_errors_deg)
        }


def write_residuals_json(
    filepath: str,
    residuals_by_pass: List[Dict[str, Any]],
    overall_stats: Dict[str, Any]
):
    """
    Write residuals to JSON file.
    
    Args:
        filepath: Output JSON file path
        residuals_by_pass: List of residual dicts (one per pass)
        overall_stats: Dictionary of overall statistics
    """
    output = {
        "metadata": {
            "generated_utc": datetime.utcnow().isoformat() + "Z",
            "version": "1.0",
            "purpose": "SGP4 vs synthetic truth residuals for ML training"
        },
        "overall_statistics": overall_stats,
        "residuals_by_pass": residuals_by_pass
    }
    
    with open(filepath, 'w') as f:
        json.dump(output, f, indent=2)


def write_passes_json(
    filepath: str,
    passes: List[Dict[str, Any]],
    satellite_name: str,
    prediction_source: str
):
    """
    Write pass predictions to JSON file.
    
    Args:
        filepath: Output JSON file path
        passes: List of pass dicts
        satellite_name: Name of satellite
        prediction_source: "sgp4" or "synthetic_truth"
    """
    output = {
        "metadata": {
            "generated_utc": datetime.utcnow().isoformat() + "Z",
            "satellite_name": satellite_name,
            "prediction_source": prediction_source,
            "version": "1.0"
        },
        "passes": passes,
        "pass_count": len(passes)
    }
    
    with open(filepath, 'w') as f:
        json.dump(output, f, indent=2)
