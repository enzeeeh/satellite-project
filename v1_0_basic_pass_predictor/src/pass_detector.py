"""
Pass detection utilities.
- Detect passes where elevation exceeds a threshold
- Interpolate AOS/LOS times at threshold crossing
- Find time of maximum elevation within each pass
"""
from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import List, Sequence


@dataclass
class PassEvent:
    start_time: datetime  # AOS (threshold crossing)
    max_time: datetime
    end_time: datetime    # LOS (threshold crossing)
    max_elevation_deg: float


def _interp_time(t0: datetime, t1: datetime, y0: float, y1: float, y: float) -> datetime:
    """Linearly interpolate time when y crosses a target between two samples."""
    if y1 == y0:
        return t0
    frac = (y - y0) / (y1 - y0)
    return t0 + (t1 - t0) * max(0.0, min(1.0, frac))


def detect_passes(times: Sequence[datetime], elev_deg: Sequence[float], threshold_deg: float = 10.0) -> List[PassEvent]:
    """Detect satellite passes where elevation exceeds threshold.

    Args:
        times: Sequence of UTC datetimes (monotonic increasing)
        elev_deg: Sequence of elevation angles in degrees (same length as times)
        threshold_deg: Elevation threshold for a pass (deg)

    Returns:
        List of PassEvent objects.
    """
    if not times or len(times) != len(elev_deg):
        return []

    passes: List[PassEvent] = []

    in_pass = False
    aos_time = None
    max_el = -1e9
    max_time = None

    for i in range(1, len(times)):
        t0, t1 = times[i - 1], times[i]
        e0, e1 = elev_deg[i - 1], elev_deg[i]

        if not in_pass:
            # Check for threshold crossing upward
            if e0 <= threshold_deg and e1 > threshold_deg:
                aos_time = _interp_time(t0, t1, e0, e1, threshold_deg)
                in_pass = True
                max_el = e1
                max_time = t1
            elif e1 > threshold_deg and e0 > threshold_deg and aos_time is None:
                # Started above threshold at the beginning of the window; treat t0 as AOS
                aos_time = t0
                in_pass = True
                max_el = max(e0, e1)
                max_time = t0 if e0 >= e1 else t1
        else:
            # Within a pass, update max elevation
            if e1 > max_el:
                max_el = e1
                max_time = t1

            # Check for downward crossing to end the pass
            if e0 > threshold_deg and e1 <= threshold_deg:
                los_time = _interp_time(t0, t1, e0, e1, threshold_deg)
                passes.append(PassEvent(start_time=aos_time, max_time=max_time, end_time=los_time, max_elevation_deg=max_el))
                in_pass = False
                aos_time = None
                max_el = -1e9
                max_time = None

    # Handle pass that continues past the final sample
    if in_pass and aos_time is not None:
        passes.append(PassEvent(start_time=aos_time, max_time=max_time, end_time=times[-1], max_elevation_deg=max_el))

    return passes
