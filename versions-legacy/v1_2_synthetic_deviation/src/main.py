"""
Main orchestration for synthetic deviation simulation.

Generates:
1. SGP4 pass predictions (nominal)
2. Synthetic truth passes (perturbed SGP4 positions)
3. Residual statistics comparing the two
"""

import json
import argparse
import sys
from pathlib import Path
from datetime import datetime, timedelta
import numpy as np

# Local imports (v1_2 has its own copies)
from . import tle_loader, propagator, ground_station, pass_detector, deviation_model, residuals

# Convenience
load_tle = tle_loader.load_tle
propagate_satellite = propagator.propagate_satellite
GroundStation = ground_station.GroundStation
PassDetector = pass_detector.PassDetector
perturb_position = deviation_model.perturb_position
compute_position_error = deviation_model.compute_position_error
compute_timing_error = deviation_model.compute_timing_error
ResidualStats = residuals.ResidualStats
write_residuals_json = residuals.write_residuals_json
write_passes_json = residuals.write_passes_json


def propagate_and_detect_passes(
    tle_lines: tuple,
    start_utc: datetime,
    end_utc: datetime,
    step_seconds: int,
    ground_station: GroundStation,
    threshold_deg: float,
    use_perturbation: bool = False,
    perturbation_seed: int = None
) -> tuple:
    """
    Propagate orbit and detect passes.
    
    Args:
        tle_lines: (name, line1, line2) tuple
        start_utc: Start time
        end_utc: End time
        step_seconds: Propagation step in seconds
        ground_station: Observer location
        threshold_deg: Elevation threshold
        use_perturbation: Apply deviation perturbation
        perturbation_seed: Random seed for reproducibility
    
    Returns:
        (passes_list, positions_dict) where positions_dict[datetime] = (pos_ecef, vel_ecef)
    """
    sat_name, line1, line2 = tle_lines
    
    # Create detector
    detector = PassDetector(threshold_deg)
    
    # Time grid
    times = []
    current = start_utc
    while current <= end_utc:
        times.append(current)
        current += timedelta(seconds=step_seconds)
    
    positions_dict = {}
    elevations = []
    
    for t in times:
        # Propagate
        pos_teme, vel_teme = propagate_satellite(line1, line2, t)
        pos_ecef, vel_ecef = pos_teme, vel_teme
        
        # Apply perturbation if needed
        if use_perturbation:
            hours_since_epoch = (t - start_utc).total_seconds() / 3600.0
            seed = perturbation_seed + hash(t) if perturbation_seed else None
            pos_ecef = perturb_position(
                np.array(pos_ecef), np.array(vel_ecef),
                hours_since_epoch,
                along_track_rate_km_per_hour=0.05,
                cross_track_sigma_km=0.02,
                seed=seed
            )
            pos_ecef = tuple(pos_ecef)
        
        positions_dict[t] = (pos_ecef, vel_ecef)
        
        # Compute elevation
        elevation = ground_station.compute_elevation(pos_ecef)
        elevations.append((t, elevation))
        
        # Feed to detector
        detector.update(elevation, t)
    
    # Extract passes
    passes = detector.get_passes()
    
    return passes, positions_dict, elevations


def main():
    parser = argparse.ArgumentParser(description="Satellite synthetic deviation simulator")
    parser.add_argument("--tle", required=True, help="TLE file path")
    parser.add_argument("--hours", type=int, default=24, help="Prediction window (hours)")
    parser.add_argument("--step", type=int, default=60, help="Time step (seconds)")
    parser.add_argument("--threshold", type=float, default=10.0, help="Elevation threshold (degrees)")
    parser.add_argument("--station-lat", type=float, default=40.0, help="Station latitude (degrees)")
    parser.add_argument("--station-lon", type=float, default=-105.0, help="Station longitude (degrees)")
    parser.add_argument("--station-alt", type=float, default=1.6, help="Station altitude (km)")
    parser.add_argument("--outdir", default="outputs", help="Output directory")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for reproducibility")
    
    args = parser.parse_args()
    
    # Create output directory
    out_path = Path(args.outdir)
    out_path.mkdir(parents=True, exist_ok=True)
    
    # Load TLE
    sat_name, line1, line2 = load_tle(args.tle)
    print(f"Loaded: {sat_name}")
    
    # Time window
    start_utc = datetime.utcnow()
    end_utc = start_utc + timedelta(hours=args.hours)
    print(f"Time window: {start_utc.isoformat()} to {end_utc.isoformat()}")
    
    # Ground station
    station = GroundStation(args.station_lat, args.station_lon, args.station_alt)
    
    print(f"Computing SGP4 passes...")
    sgp4_passes, sgp4_positions, sgp4_elevations = propagate_and_detect_passes(
        (sat_name, line1, line2),
        start_utc, end_utc, args.step,
        station, args.threshold,
        use_perturbation=False
    )
    
    print(f"Computing synthetic truth passes...")
    truth_passes, truth_positions, truth_elevations = propagate_and_detect_passes(
        (sat_name, line1, line2),
        start_utc, end_utc, args.step,
        station, args.threshold,
        use_perturbation=True,
        perturbation_seed=args.seed
    )
    
    # Convert passes to JSON-serializable format
    def pass_to_dict(p):
        return {
            "start_utc": p.startTime.isoformat() + "Z",
            "end_utc": p.endTime.isoformat() + "Z",
            "max_elevation_deg": round(p.maxElevationDeg, 4),
            "duration_sec": int((p.endTime - p.startTime).total_seconds())
        }
    
    sgp4_passes_json = [pass_to_dict(p) for p in sgp4_passes]
    truth_passes_json = [pass_to_dict(p) for p in truth_passes]
    
    # Write passes
    write_passes_json(
        str(out_path / "passes_sgp4.json"),
        sgp4_passes_json,
        sat_name,
        "sgp4"
    )
    write_passes_json(
        str(out_path / "passes_synthetic_truth.json"),
        truth_passes_json,
        sat_name,
        "synthetic_truth"
    )
    
    # Compute residuals for matched passes
    residuals_list = []
    stats = ResidualStats()
    
    # Match passes by proximity
    for i, sgp4_pass in enumerate(sgp4_passes):
        # Find closest truth pass
        if not truth_passes:
            continue
        
        diffs = [abs((p.startTime - sgp4_pass.startTime).total_seconds()) for p in truth_passes]
        closest_idx = np.argmin(diffs)
        truth_pass = truth_passes[closest_idx]
        
        # Compute residuals
        aos_error = compute_timing_error(sgp4_pass.startTime, truth_pass.startTime)
        los_error = compute_timing_error(sgp4_pass.endTime, truth_pass.endTime)
        max_el_error = truth_pass.maxElevationDeg - sgp4_pass.maxElevationDeg
        
        # Position error at max elevation time
        max_el_time = sgp4_pass.startTime + (sgp4_pass.endTime - sgp4_pass.startTime) / 2
        pos_error = 0.0
        if max_el_time in sgp4_positions and max_el_time in truth_positions:
            pos_sgp4, _ = sgp4_positions[max_el_time]
            pos_truth, _ = truth_positions[max_el_time]
            pos_error = compute_position_error(pos_sgp4, pos_truth)
        
        residuals_dict = {
            "pass_index": i,
            "sgp4_aos_utc": sgp4_pass.startTime.isoformat() + "Z",
            "truth_aos_utc": truth_pass.startTime.isoformat() + "Z",
            "aos_error_sec": float(aos_error),
            "sgp4_los_utc": sgp4_pass.endTime.isoformat() + "Z",
            "truth_los_utc": truth_pass.endTime.isoformat() + "Z",
            "los_error_sec": float(los_error),
            "sgp4_max_el_deg": round(sgp4_pass.maxElevationDeg, 4),
            "truth_max_el_deg": round(truth_pass.maxElevationDeg, 4),
            "max_el_error_deg": round(float(max_el_error), 4),
            "position_error_km": round(pos_error, 4)
        }
        residuals_list.append(residuals_dict)
        stats.add_pass_residual(pos_error, aos_error, los_error, max_el_error)
    
    overall_stats = stats.compute_stats()
    
    # Write residuals
    write_residuals_json(
        str(out_path / "residuals.json"),
        residuals_list,
        overall_stats
    )
    
    print(f"\nResults:")
    print(f"  SGP4 passes: {len(sgp4_passes)}")
    print(f"  Truth passes: {len(truth_passes)}")
    print(f"  Matched passes: {stats.pass_count}")
    
    if stats.pass_count > 0:
        print(f"\nResidual statistics:")
        print(f"  Position error (km):    μ={overall_stats['position_error_km']['mean']:.4f}, σ={overall_stats['position_error_km']['std']:.4f}")
        print(f"  AOS error (seconds):    μ={overall_stats['aos_error_sec']['mean']:.2f}, σ={overall_stats['aos_error_sec']['std']:.2f}")
        print(f"  LOS error (seconds):    μ={overall_stats['los_error_sec']['mean']:.2f}, σ={overall_stats['los_error_sec']['std']:.2f}")
        print(f"  Max elevation error (°): μ={overall_stats['max_elevation_error_deg']['mean']:.4f}, σ={overall_stats['max_elevation_error_deg']['std']:.4f}")
    else:
        print("\nNo passes detected in this window.")
    
    print(f"\nOutput files:")
    print(f"  {out_path / 'passes_sgp4.json'}")
    print(f"  {out_path / 'passes_synthetic_truth.json'}")
    print(f"  {out_path / 'residuals.json'}")


if __name__ == "__main__":
    main()
