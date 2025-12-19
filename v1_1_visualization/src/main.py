from __future__ import annotations
import argparse
import os
from datetime import datetime, timedelta, timezone
from typing import List, Tuple

from .tle_loader import load_tle
from .propagator import satrec_from_tle, propagate_teme, gmst_angle, teme_to_ecef
from .ground_station import GroundStation
from .pass_detector import detect_passes
from .visualization.ground_track import plot_ground_track_matplotlib, plot_ground_track_plotly
from .visualization.elevation_plot import plot_elevation_matplotlib, plot_elevation_plotly

DEFAULT_LAT = 40.0
DEFAULT_LON = -105.0
DEFAULT_ALT_M = 1600.0
DEFAULT_THRESHOLD_DEG = 10.0


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Satellite pass predictor with optional visualization (v1.1)")
    p.add_argument("--tle", type=str, default="v1_0_basic_pass_predictor/data/tle.txt", help="Path to TLE text file")
    p.add_argument("--lat", type=float, default=DEFAULT_LAT, help="Ground station latitude (deg)")
    p.add_argument("--lon", type=float, default=DEFAULT_LON, help="Ground station longitude (deg)")
    p.add_argument("--alt", type=float, default=DEFAULT_ALT_M, help="Ground station altitude (meters)")
    p.add_argument("--threshold", type=float, default=DEFAULT_THRESHOLD_DEG, help="Elevation threshold (deg)")
    p.add_argument("--step", type=float, default=30.0, help="Propagation step seconds (default 30s)")
    p.add_argument("--hours", type=float, default=48.0, help="Prediction horizon hours (default 48h)")
    p.add_argument("--start-utc", type=str, default=None, help="Start time in UTC ISO format (default now)")
    p.add_argument("--plots", type=str, default="none", choices=["none", "matplotlib", "plotly", "both"], help="Which visualizations to produce")
    p.add_argument("--outdir", type=str, default=os.path.join(os.path.dirname(__file__), "..", "outputs", "plots"), help="Output directory for plots")
    return p.parse_args()


def datetime_range(start: datetime, end: datetime, step_seconds: float) -> List[datetime]:
    times: List[datetime] = []
    t = start
    from datetime import timedelta
    step = timedelta(seconds=step_seconds)
    while t <= end:
        times.append(t)
        t += step
    return times


def main():
    args = parse_args()

    os.makedirs(args.outdir, exist_ok=True)

    # Load TLE and initialize propagator
    _, l1, l2 = load_tle(args.tle)
    sat = satrec_from_tle(l1, l2)

    # Ground station
    gs = GroundStation(lat_deg=args.lat, lon_deg=args.lon, alt_m=args.alt)

    # Time grid
    start_utc = (
        datetime.fromisoformat(args.start_utc.replace("Z", "+00:00")).astimezone(timezone.utc)
        if args.start_utc else datetime.now(timezone.utc)
    )
    end_utc = start_utc + timedelta(hours=args.hours)
    times = datetime_range(start_utc, end_utc, args.step)

    # Propagate and compute elevations + store ECEF for ground track
    elevations: List[float] = []
    ecef_series: List[Tuple[float, float, float]] = []
    for dt in times:
        teme = propagate_teme(sat, dt)
        gmst = gmst_angle(dt)
        r_ecef = teme_to_ecef(teme.r_km, gmst)
        ecef_series.append(r_ecef)
        el = gs.elevation_deg(r_ecef)
        elevations.append(el)

    # Detect passes
    passes = detect_passes(times, elevations, threshold_deg=args.threshold)

    # Visualization (optional)
    ts_suffix = start_utc.strftime("%Y%m%dT%H%M%SZ")
    if args.plots in ("matplotlib", "both"):
        gt_path = os.path.join(args.outdir, f"ground_track_matplotlib_{ts_suffix}.png")
        ev_path = os.path.join(args.outdir, f"elevation_matplotlib_{ts_suffix}.png")
        plot_ground_track_matplotlib(times, ecef_series, gt_path)
        plot_elevation_matplotlib(times, elevations, passes, ev_path)
        print(f"Saved: {gt_path}")
        print(f"Saved: {ev_path}")
    if args.plots in ("plotly", "both"):
        gt_path = os.path.join(args.outdir, f"ground_track_plotly_{ts_suffix}.png")
        ev_path = os.path.join(args.outdir, f"elevation_plotly_{ts_suffix}.png")
        gt_out = plot_ground_track_plotly(times, ecef_series, gt_path)
        ev_out = plot_elevation_plotly(times, elevations, passes, ev_path)
        print(f"Saved: {gt_out}")
        print(f"Saved: {ev_out}")

    # Print JSON-like summary for CLI parity (not writing file here)
    import json
    result = [
        {
            "startTime": p.start_time.astimezone(timezone.utc).isoformat().replace("+00:00", "Z"),
            "maxTime": p.max_time.astimezone(timezone.utc).isoformat().replace("+00:00", "Z"),
            "endTime": p.end_time.astimezone(timezone.utc).isoformat().replace("+00:00", "Z"),
            "maxElevationDeg": round(p.max_elevation_deg, 3),
        }
        for p in passes
    ]
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
