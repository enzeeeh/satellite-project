"""
Unified Satellite Pass Predictor

Single entry point supporting:
- Basic pass prediction
- Visualization (matplotlib/plotly)
- Synthetic deviation analysis
"""

from __future__ import annotations
import argparse
import os
import sys
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
        description="Unified Satellite Pass Predictor (supports basic prediction, visualization, and analysis)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic prediction
  python main.py --tle data/tle_leo/AO-91.txt

  # With visualization
  python main.py --tle data/tle_leo/AO-91.txt --plot matplotlib

  # With analysis and interactive plots
  python main.py --tle data/tle_leo/AO-91.txt --plot plotly --analyze-deviation

  # All features combined
  python main.py --tle data/tle_leo/AO-91.txt --plot both --analyze-deviation
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


def _parse_line2_features(line2: str) -> Tuple[float, float, float]:
    """Extract mean motion (rev/day), eccentricity, inclination (deg) from TLE line 2.

    Follows standard TLE fixed-width fields.
    """
    try:
        # Inclination (deg) columns 9-16 (1-based); Python slice 8:16
        inc_deg = float(line2[8:16].strip())
        # Eccentricity columns 27-33 as 7-digit fractional without decimal; slice 26:33
        ecc_str = line2[26:33].strip()
        eccentricity = float(f"0.{ecc_str}") if ecc_str else 0.0
        # Mean motion (rev/day) columns 53-63; slice 52:63
        mm_rev_per_day = float(line2[52:63].strip())
        return mm_rev_per_day, eccentricity, inc_deg
    except Exception:
        # Fallback using split if fixed-width parse fails
        parts = line2.split()
        inc_deg = float(parts[2])
        eccentricity = float(f"0.{parts[4]}")
        mm_rev_per_day = float(parts[7])
        return mm_rev_per_day, eccentricity, inc_deg


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
            "deviation_analysis": args.analyze_deviation,
        },
        "num_passes": len(passes),
    }


def _discover_tle_files() -> List[Path]:
    """Find all .txt TLE files under data/."""
    data_dir = Path("data")
    if not data_dir.exists():
        return []
    return sorted(data_dir.rglob("*.txt"))


def _prompt(prompt_text: str, default: str = "") -> str:
    """Print a prompt and return stripped input, falling back to default."""
    suffix = f" [{default}]" if default else ""
    raw = input(f"  {prompt_text}{suffix}: ").strip()
    return raw if raw else default


def _prompt_int(prompt_text: str, default: int, min_val: int = 1, max_val: int = 9999) -> int:
    """Prompt for an integer within range."""
    while True:
        raw = _prompt(prompt_text, str(default))
        try:
            val = int(raw)
            if min_val <= val <= max_val:
                return val
            print(f"    ⚠  Please enter a number between {min_val} and {max_val}.")
        except ValueError:
            print("    ⚠  That doesn't look like a number, try again.")


def _prompt_float(prompt_text: str, default: float, min_val: float = None, max_val: float = None) -> float:
    """Prompt for a float, optionally bounded."""
    while True:
        raw = _prompt(prompt_text, str(default))
        try:
            val = float(raw)
            if min_val is not None and val < min_val:
                print(f"    ⚠  Minimum value is {min_val}.")
                continue
            if max_val is not None and val > max_val:
                print(f"    ⚠  Maximum value is {max_val}.")
                continue
            return val
        except ValueError:
            print("    ⚠  That doesn't look like a number, try again.")


def _choose_from_menu(title: str, options: List[str], default_idx: int = 0) -> int:
    """Display a numbered menu and return the chosen 0-based index."""
    print(f"\n  {title}")
    for i, opt in enumerate(options, 1):
        marker = "●" if i - 1 == default_idx else " "
        print(f"  {marker} {i}. {opt}")
    while True:
        raw = _prompt(f"Enter number (1-{len(options)})", str(default_idx + 1))
        try:
            idx = int(raw) - 1
            if 0 <= idx < len(options):
                return idx
            print(f"    ⚠  Please choose between 1 and {len(options)}.")
        except ValueError:
            print("    ⚠  Please enter a number.")


# Ground station presets (name, lat, lon, alt_m)
_GS_PRESETS = [
    ("Boulder, CO, USA",          40.00, -105.00, 1600),
    ("San Francisco, CA, USA",    37.77, -122.41,  100),
    ("London, UK",                51.51,   -0.13,   20),
    ("Sydney, Australia",        -33.87,  151.21,   50),
    ("Tokyo, Japan",              35.68,  139.69,   30),
    ("Nairobi, Kenya",            -1.29,   36.82, 1795),
    ("Enter custom location",     None,    None,  None),
]


def interactive_mode() -> argparse.Namespace:
    """Run interactive step-by-step wizard and return a populated Namespace.

    Returns the same Namespace that parse_args() would return so the rest
    of main() works unchanged.
    """
    print("\n" + "═" * 70)
    print("  SATELLITE PASS PREDICTOR  ·  Interactive Mode")
    print("  (Run  python main.py --help  for the non-interactive CLI)")
    print("═" * 70)

    # ── STEP 1 : Choose satellite ─────────────────────────────────────────
    print("\n┌─ STEP 1 of 4 ─ Choose a satellite ─────────────────────────────┐")
    tle_files = _discover_tle_files()
    if not tle_files:
        print("  ✗  No TLE files found under data/  – exiting.")
        sys.exit(1)

    tle_labels = [str(f) for f in tle_files]
    chosen_tle_idx = _choose_from_menu("Available TLE files:", tle_labels, default_idx=0)
    tle_path = str(tle_files[chosen_tle_idx])

    # Preview the satellite name
    try:
        sat_name_preview, _, _ = load_tle(tle_path)
        print(f"  ✓  Selected: {sat_name_preview}  ({tle_path})")
    except Exception as e:
        print(f"  ✗  Could not read TLE: {e}")
        sys.exit(1)

    # ── STEP 2 : Ground station ───────────────────────────────────────────
    print("\n┌─ STEP 2 of 4 ─ Ground station (your location) ────────────────┐")
    gs_labels = [f"{name}  ({lat}°, {lon}°)" if lat is not None else name
                 for name, lat, lon, _ in _GS_PRESETS]
    gs_idx = _choose_from_menu("Choose a preset or enter custom:", gs_labels, default_idx=0)

    preset = _GS_PRESETS[gs_idx]
    if preset[1] is None:  # custom
        lat  = _prompt_float("Latitude  (°, positive = North)", 40.0, -90.0,  90.0)
        lon  = _prompt_float("Longitude (°, positive = East)", -105.0, -180.0, 180.0)
        alt  = _prompt_float("Altitude  (metres above sea level)", 0.0, 0.0)
    else:
        lat, lon, alt = preset[1], preset[2], preset[3]
        print(f"  ✓  Station: {preset[0]}  →  {lat}°, {lon}°, {alt} m")

    # ── STEP 3 : Prediction window ─────────────────────────────────────────
    print("\n┌─ STEP 3 of 4 ─ Prediction window ──────────────────────────────┐")
    hours = _prompt_float("Prediction duration (hours, e.g. 24 or 48)", 24.0, 1.0, 720.0)

    _step_map = {0: 10.0, 1: 30.0, 2: 60.0, 3: 120.0}
    step_sec = _step_map[_choose_from_menu(
        "Propagation step size:",
        ["10 seconds  (highest accuracy, slower)",
         "30 seconds  (recommended)",
         "60 seconds  (fast, slightly lower accuracy)",
         "120 seconds (very fast, rough)"],
        default_idx=1,
    )]

    threshold = _prompt_float("Minimum elevation threshold (°, typical = 10)", 10.0, 0.0, 90.0)
    print(f"  ✓  Window: next {hours:.0f}h  |  step: {step_sec:.0f}s  |  threshold: {threshold}°")

    # ── STEP 4 : Visualization ─────────────────────────────────────────────
    print("\n┌─ STEP 4 of 4 ─ Visualization ──────────────────────────────────┐")
    plot_idx = _choose_from_menu(
        "Generate plots?",
        ["No plots  (text + JSON output only)",
         "Matplotlib  (PNG files saved to outputs/)",
         "Plotly      (interactive HTML files saved to outputs/)",
         "Both        (PNG + HTML)"],
        default_idx=1,
    )
    plot_map = {0: "none", 1: "matplotlib", 2: "plotly", 3: "both"}
    plot_choice = plot_map[plot_idx]
    if plot_choice != "none":
        print(f"  ✓  Plots: {plot_choice}  →  saved to outputs/")

    # ── CONFIRMATION ──────────────────────────────────────────────────────
    print("\n" + "─" * 70)
    print("  SUMMARY – about to run with these settings:")
    print(f"    Satellite  :  {sat_name_preview}  ({tle_path})")
    print(f"    Station    :  lat={lat}°  lon={lon}°  alt={alt}m")
    print(f"    Window     :  {hours:.0f}h  |  step={step_sec:.0f}s  |  threshold={threshold}°")
    print(f"    Plots      :  {plot_choice}")
    print("─" * 70)

    confirm = _prompt("Press ENTER to run, or type 'q' to quit", "")
    if confirm.lower() == "q":
        print("  Aborted.")
        sys.exit(0)

    # Build a Namespace that matches what parse_args() would return
    ns = argparse.Namespace(
        tle=tle_path,
        outdir="outputs",
        lat=lat,
        lon=lon,
        alt=alt,
        threshold=threshold,
        hours=hours,
        step=step_sec,
        start_utc=None,
        plot=plot_choice,
        analyze_deviation=False,
        json_output=True,
    )
    return ns


def main():
    """Main entry point.

    Launches the interactive wizard when no arguments are passed,
    otherwise falls through to the standard CLI parser.
    """
    if len(sys.argv) == 1:
        args = interactive_mode()
    else:
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
