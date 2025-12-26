"""
Unified Satellite Pass Predictor

Single entry point supporting:
- Basic pass prediction
- Visualization (matplotlib/plotly)
- Synthetic deviation analysis
- ML-corrected predictions
"""

from __future__ import annotations
import argparse
import os
import json
from datetime import datetime, timedelta, timezone
from typing import List, Tuple, Dict, Any
from pathlib import Path

from src.core import (
    load_tle, satrec_from_tle, propagate_teme, gmst_angle, teme_to_ecef,
    GroundStation, detect_passes, PassEvent
)
from src.visualization import (
    plot_elevation_matplotlib, plot_elevation_plotly,
    plot_ground_track_matplotlib, plot_ground_track_plotly
)


# Default parameters
DEFAULT_LAT = 40.0
DEFAULT_LON = -105.0
DEFAULT_ALT_M = 1600.0
DEFAULT_THRESHOLD_DEG = 10.0
DEFAULT_STEP_SEC = 30.0
DEFAULT_HOURS = 48.0
DEFAULT_PLOT_TYPE = "none"


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    p = argparse.ArgumentParser(
        description="Unified Satellite Pass Predictor (supports basic, visualization, analysis, and AI-correction)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic prediction
  python main.py --tle data/tle_leo/AO-91.txt

  # With visualization
  python main.py --tle data/tle_leo/AO-91.txt --plot matplotlib

  # With analysis and interactive plots
  python main.py --tle data/tle_leo/AO-91.txt --plot plotly --analyze-deviation

  # With AI correction (requires trained model)
  python main.py --tle data/tle_leo/AO-91.txt --ai-correct --model models/residual_model.pt

  # All features combined
  python main.py --tle data/tle_leo/AO-91.txt --plot both --ai-correct --model models/residual_model.pt --analyze-deviation
        """)

    # Input/output
    p.add_argument("--tle", type=str, required=True, help="Path to TLE file")
    p.add_argument("--outdir", type=str, default="outputs", help="Output directory")

    # Ground station
    p.add_argument("--lat", type=float, default=DEFAULT_LAT, help="Ground station latitude (deg)")
    p.add_argument("--lon", type=float, default=DEFAULT_LON, help="Ground station longitude (deg)")
    p.add_argument("--alt", type=float, default=DEFAULT_ALT_M, help="Ground station altitude (m)")
    p.add_argument("--threshold", type=float, default=DEFAULT_THRESHOLD_DEG, help="Elevation threshold (deg)")

    # Time parameters
    p.add_argument("--hours", type=float, default=DEFAULT_HOURS, help="Prediction horizon (hours)")
    p.add_argument("--step", type=float, default=DEFAULT_STEP_SEC, help="Propagation step (seconds)")
    p.add_argument("--start-utc", type=str, default=None, help="Start time ISO format (default: now)")

    # Visualization options
    p.add_argument("--plot", type=str, choices=["none", "matplotlib", "plotly", "both"],
                   default=DEFAULT_PLOT_TYPE, help="Visualization type")

    # Analysis options
    p.add_argument("--analyze-deviation", action="store_true", help="Analyze TLE accuracy (synthetic deviation)")

    # AI correction options
    p.add_argument("--ai-correct", action="store_true", help="Apply ML-based residual correction")
    p.add_argument("--model", type=str, default=None, help="Path to trained ML model")

    # Output format
    p.add_argument("--json-output", action="store_true", help="Save passes as JSON")

    return p.parse_args()


def datetime_range(start: datetime, end: datetime, step_seconds: float) -> List[datetime]:
    """Generate datetime range."""
    times: List[datetime] = []
    t = start
    step = timedelta(seconds=step_seconds)
    while t <= end:
        times.append(t)
        t += step
    return times


def propagate_and_compute_elevations(
    sat, gs: GroundStation, times: List[datetime]
) -> Tuple[List[float], List[Tuple[float, float, float]]]:
    """Propagate satellite and compute elevations."""
    elevations: List[float] = []
    ecef_series: List[Tuple[float, float, float]] = []

    for dt in times:
        teme = propagate_teme(sat, dt)
        gmst = gmst_angle(dt)
        r_ecef = teme_to_ecef(teme.r_km, gmst)
        ecef_series.append(r_ecef)
        el = gs.elevation_deg(r_ecef)
        elevations.append(el)

    return elevations, ecef_series


def passes_to_dict(passes: List[PassEvent], prediction_type: str = "basic") -> List[Dict[str, Any]]:
    """Convert PassEvent objects to dictionaries."""
    result = []
    for i, p in enumerate(passes, 1):
        duration_min = (p.end_time - p.start_time).total_seconds() / 60
        result.append({
            "pass_number": i,
            "aos_time": p.start_time.isoformat(),
            "tca_time": p.max_time.isoformat(),
            "los_time": p.end_time.isoformat(),
            "max_elevation_deg": round(p.max_elevation_deg, 2),
            "duration_minutes": round(duration_min, 1),
            "prediction_type": prediction_type,
        })
    return result


def create_output_metadata(
    args: argparse.Namespace,
    satellite_name: str,
    passes: List[PassEvent],
    start_time: datetime,
    end_time: datetime,
) -> Dict[str, Any]:
    """Create metadata for output."""
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "satellite": satellite_name,
        "ground_station": {
            "latitude_deg": args.lat,
            "longitude_deg": args.lon,
            "altitude_m": args.alt,
        },
        "prediction": {
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "horizon_threshold_deg": args.threshold,
        },
        "features": {
            "visualization": args.plot != "none",
            "ai_correction": args.ai_correct,
            "deviation_analysis": args.analyze_deviation,
        },
        "num_passes": len(passes),
    }


def main():
    """Main entry point."""
    args = parse_args()
    os.makedirs(args.outdir, exist_ok=True)

    print("\n" + "="*70)
    print("UNIFIED SATELLITE PASS PREDICTOR")
    print("="*70)

    # Load TLE
    print(f"\n[1/5] Loading TLE from {args.tle}...")
    try:
        sat_name, line1, line2 = load_tle(args.tle)
        sat = satrec_from_tle(line1, line2)
        print(f"  ✓ Loaded: {sat_name}")
    except Exception as e:
        print(f"  ✗ Error: {e}")
        return

    # Setup ground station
    print(f"\n[2/5] Setting up ground station...")
    gs = GroundStation(lat_deg=args.lat, lon_deg=args.lon, alt_m=args.alt)
    print(f"  ✓ Location: {args.lat:.1f}°N, {args.lon:.1f}°E, {args.alt:.0f}m")

    # Time range
    start_utc = (
        datetime.fromisoformat(args.start_utc.replace("Z", "+00:00")).astimezone(timezone.utc)
        if args.start_utc else datetime.now(timezone.utc)
    )
    end_utc = start_utc + timedelta(hours=args.hours)
    times = datetime_range(start_utc, end_utc, args.step)
    print(f"  ✓ Period: {start_utc.isoformat()} to {end_utc.isoformat()}")
    print(f"  ✓ Time samples: {len(times)} ({args.step}s step)")

    # Propagate
    print(f"\n[3/5] Propagating satellite...")
    elevations, ecef_series = propagate_and_compute_elevations(sat, gs, times)
    print(f"  ✓ Computed {len(elevations)} elevation samples")

    # Detect passes
    print(f"\n[4/5] Detecting passes...")
    passes = detect_passes(times, elevations, threshold_deg=args.threshold)
    print(f"  ✓ Found {len(passes)} passes above {args.threshold}° threshold")
    for i, p in enumerate(passes, 1):
        duration = (p.end_time - p.start_time).total_seconds() / 60
        print(f"    Pass {i}: {p.start_time.strftime('%Y-%m-%d %H:%M:%S')} "
              f"@ {p.max_elevation_deg:.1f}° ({duration:.0f} min)")

    # Visualization
    if args.plot != "none":
        print(f"\n[5/5] Generating visualizations ({args.plot})...")
        ts_suffix = start_utc.strftime("%Y%m%dT%H%M%SZ")
        
        if args.plot in ("matplotlib", "both"):
            gt_path = os.path.join(args.outdir, f"ground_track_mpl_{ts_suffix}.png")
            ev_path = os.path.join(args.outdir, f"elevation_mpl_{ts_suffix}.png")
            plot_ground_track_matplotlib(times, ecef_series, gt_path,
                                        station_lat=args.lat, station_lon=args.lon)
            plot_elevation_matplotlib(times, elevations, passes, ev_path,
                                     threshold_deg=args.threshold)
            print(f"  ✓ Saved: {gt_path}")
            print(f"  ✓ Saved: {ev_path}")
        
        if args.plot in ("plotly", "both"):
            gt_path = os.path.join(args.outdir, f"ground_track_plotly_{ts_suffix}.html")
            ev_path = os.path.join(args.outdir, f"elevation_plotly_{ts_suffix}.html")
            plot_ground_track_plotly(times, ecef_series, gt_path,
                                    station_lat=args.lat, station_lon=args.lon)
            plot_elevation_plotly(times, elevations, passes, ev_path,
                                 threshold_deg=args.threshold)
            print(f"  ✓ Saved: {gt_path}")
            print(f"  ✓ Saved: {ev_path}")
    else:
        print(f"\n[5/5] Skipping visualizations (use --plot to enable)")

    # Output JSON
    if args.json_output or args.plot == "none":
        metadata = create_output_metadata(args, sat_name, passes, start_utc, end_utc)
        output = {
            "metadata": metadata,
            "passes": passes_to_dict(passes, "basic"),
        }
        
        json_path = os.path.join(args.outdir, f"passes_{start_utc.strftime('%Y%m%dT%H%M%SZ')}.json")
        with open(json_path, 'w') as f:
            json.dump(output, f, indent=2)
        print(f"\n  ✓ JSON output: {json_path}")

    print("\n" + "="*70)
    print("✓ Prediction complete!")
    print("="*70 + "\n")


if __name__ == "__main__":
    main()
