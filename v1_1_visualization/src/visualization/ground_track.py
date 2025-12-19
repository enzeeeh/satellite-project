from __future__ import annotations
from typing import Sequence, Tuple
from datetime import datetime
import math

import matplotlib.pyplot as plt
import plotly.graph_objects as go

# WGS84 constants (km)
_A = 6378.137
_F = 1.0 / 298.257223563
_E2 = _F * (2 - _F)


def ecef_to_geodetic_latlon(ecef_km: Tuple[float, float, float]) -> Tuple[float, float]:
    """Convert ECEF (km) to geodetic latitude/longitude in degrees (WGS84).
    Altitude is not needed for ground track; use standard iterative method.
    """
    x, y, z = ecef_km
    lon = math.degrees(math.atan2(y, x))
    # Iterative latitude
    r = math.hypot(x, y)
    if r == 0:
        return (90.0 if z > 0 else -90.0, lon)
    # Initial guess
    lat = math.atan2(z, r)
    for _ in range(5):  # few iterations suffice
        sin_lat = math.sin(lat)
        N = _A / math.sqrt(1.0 - _E2 * sin_lat * sin_lat)
        lat = math.atan2(z + N * _E2 * sin_lat, r)
    return (math.degrees(lat), lon)


def plot_ground_track_matplotlib(times: Sequence[datetime], ecef_series_km: Sequence[Tuple[float, float, float]], out_path: str, title: str = "Ground Track") -> str:
    latlons = [ecef_to_geodetic_latlon(r) for r in ecef_series_km]
    lats = [lat for lat, _ in latlons]
    lons = [((lon + 180) % 360) - 180 for _, lon in latlons]  # wrap to [-180,180]

    plt.figure(figsize=(10, 4))
    plt.plot(lons, lats, linewidth=1.5)
    plt.title(title)
    plt.xlabel("Longitude (deg)")
    plt.ylabel("Latitude (deg)")
    plt.grid(True, linestyle='--', alpha=0.5)
    plt.xlim(-180, 180)
    plt.ylim(-90, 90)
    plt.tight_layout()
    plt.savefig(out_path, dpi=150)
    plt.close()
    return out_path


def plot_ground_track_plotly(times: Sequence[datetime], ecef_series_km: Sequence[Tuple[float, float, float]], out_path: str, title: str = "Ground Track") -> str:
    latlons = [ecef_to_geodetic_latlon(r) for r in ecef_series_km]
    lats = [lat for lat, _ in latlons]
    lons = [((lon + 180) % 360) - 180 for _, lon in latlons]

    fig = go.Figure()
    fig.add_trace(go.Scattergl(x=lons, y=lats, mode='lines', line=dict(width=2)))
    fig.update_layout(title=title, xaxis_title="Longitude (deg)", yaxis_title="Latitude (deg)",
                      xaxis=dict(range=[-180, 180]), yaxis=dict(range=[-90, 90]))
    try:
        fig.write_image(out_path)  # requires kaleido
    except Exception:
        # Fallback to HTML if static export not available
        html_path = out_path.replace('.png', '.html')
        fig.write_html(html_path)
        return html_path
    return out_path
