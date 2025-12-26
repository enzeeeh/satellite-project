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


def plot_ground_track_matplotlib(times: Sequence[datetime], ecef_series_km: Sequence[Tuple[float, float, float]], out_path: str, title: str = "Ground Track", station_lat: float = None, station_lon: float = None) -> str:
    latlons = [ecef_to_geodetic_latlon(r) for r in ecef_series_km]
    lats = [lat for lat, _ in latlons]
    lons = [((lon + 180) % 360) - 180 for _, lon in latlons]  # wrap to [-180,180]

    fig, ax = plt.subplots(figsize=(12, 6))
    ax.plot(lons, lats, linewidth=2, color='blue', label='Ground Track')
    
    # Mark start point (green)
    ax.plot(lons[0], lats[0], 'go', markersize=10, label='Start')
    ax.annotate(f'START\n{times[0].strftime("%H:%M:%S")}', 
                xy=(lons[0], lats[0]), xytext=(10, 10), 
                textcoords='offset points', fontsize=9, color='green',
                bbox=dict(boxstyle='round,pad=0.5', facecolor='lightgreen', alpha=0.7),
                arrowprops=dict(arrowstyle='->', color='green', lw=1.5))
    
    # Mark end point (red)
    ax.plot(lons[-1], lats[-1], 'ro', markersize=10, label='End')
    ax.annotate(f'END\n{times[-1].strftime("%H:%M:%S")}', 
                xy=(lons[-1], lats[-1]), xytext=(10, -15), 
                textcoords='offset points', fontsize=9, color='red',
                bbox=dict(boxstyle='round,pad=0.5', facecolor='lightcoral', alpha=0.7),
                arrowprops=dict(arrowstyle='->', color='red', lw=1.5))
    
    # Mark max latitude point (star)
    max_lat_idx = max(range(len(lats)), key=lambda i: abs(lats[i]))
    ax.plot(lons[max_lat_idx], lats[max_lat_idx], 'y*', markersize=20, label='Max Latitude')
    ax.annotate(f'MAX LAT\n{lats[max_lat_idx]:.1f}°', 
                xy=(lons[max_lat_idx], lats[max_lat_idx]), xytext=(15, 15), 
                textcoords='offset points', fontsize=9, color='orange',
                bbox=dict(boxstyle='round,pad=0.5', facecolor='lightyellow', alpha=0.8),
                arrowprops=dict(arrowstyle='->', color='orange', lw=1.5))
    
    # Mark ground station if provided
    if station_lat is not None and station_lon is not None:
        station_lon_wrapped = ((station_lon + 180) % 360) - 180
        ax.plot(station_lon_wrapped, station_lat, 'r^', markersize=12, label='Ground Station')
        ax.annotate(f'STATION\n({station_lat:.1f}°, {station_lon_wrapped:.1f}°)', 
                    xy=(station_lon_wrapped, station_lat), xytext=(-40, -20), 
                    textcoords='offset points', fontsize=9, color='darkred',
                    bbox=dict(boxstyle='round,pad=0.5', facecolor='lightpink', alpha=0.8),
                    arrowprops=dict(arrowstyle='->', color='darkred', lw=1.5))
    
    ax.set_title(title, fontsize=14, fontweight='bold')
    ax.set_xlabel("Longitude (deg)", fontsize=11)
    ax.set_ylabel("Latitude (deg)", fontsize=11)
    ax.grid(True, linestyle='--', alpha=0.3)
    ax.set_xlim(-180, 180)
    ax.set_ylim(-90, 90)
    ax.legend(loc='upper right', fontsize=9)
    fig.tight_layout()
    fig.savefig(out_path, dpi=150, bbox_inches='tight')
    plt.close()
    return out_path


def plot_ground_track_plotly(times: Sequence[datetime], ecef_series_km: Sequence[Tuple[float, float, float]], out_path: str, title: str = "Ground Track", station_lat: float = None, station_lon: float = None) -> str:
    latlons = [ecef_to_geodetic_latlon(r) for r in ecef_series_km]
    lats = [lat for lat, _ in latlons]
    lons = [((lon + 180) % 360) - 180 for _, lon in latlons]

    fig = go.Figure()
    
    # Main track line
    fig.add_trace(go.Scattergl(x=lons, y=lats, mode='lines', 
                               name='Ground Track',
                               line=dict(color='blue', width=2)))
    
    # Start point
    fig.add_trace(go.Scattergl(x=[lons[0]], y=[lats[0]], mode='markers',
                               name='Start',
                               marker=dict(size=12, color='green'),
                               text=[f'START<br>{times[0].strftime("%H:%M:%S")}'],
                               hoverinfo='text'))
    
    # End point
    fig.add_trace(go.Scattergl(x=[lons[-1]], y=[lats[-1]], mode='markers',
                               name='End',
                               marker=dict(size=12, color='red'),
                               text=[f'END<br>{times[-1].strftime("%H:%M:%S")}'],
                               hoverinfo='text'))
    
    # Max latitude point
    max_lat_idx = max(range(len(lats)), key=lambda i: abs(lats[i]))
    fig.add_trace(go.Scattergl(x=[lons[max_lat_idx]], y=[lats[max_lat_idx]], mode='markers',
                               name='Max Latitude',
                               marker=dict(size=16, color='gold', symbol='star'),
                               text=[f'MAX LAT<br>{lats[max_lat_idx]:.1f}°'],
                               hoverinfo='text'))
    
    # Ground station if provided
    if station_lat is not None and station_lon is not None:
        station_lon_wrapped = ((station_lon + 180) % 360) - 180
        fig.add_trace(go.Scattergl(x=[station_lon_wrapped], y=[station_lat], mode='markers',
                                   name='Ground Station',
                                   marker=dict(size=12, color='darkred', symbol='triangle-up'),
                                   text=[f'STATION<br>({station_lat:.1f}°, {station_lon_wrapped:.1f}°)'],
                                   hoverinfo='text'))
    
    # Add annotations
    fig.add_annotation(x=lons[0], y=lats[0], text=f'START<br>{times[0].strftime("%H:%M")}',
                      showarrow=True, arrowhead=2, arrowsize=1, arrowwidth=2, arrowcolor='green',
                      ax=-40, ay=40, bgcolor='lightgreen', bordercolor='green', borderwidth=1, opacity=0.8)
    
    fig.add_annotation(x=lons[-1], y=lats[-1], text=f'END<br>{times[-1].strftime("%H:%M")}',
                      showarrow=True, arrowhead=2, arrowsize=1, arrowwidth=2, arrowcolor='red',
                      ax=40, ay=-40, bgcolor='lightcoral', bordercolor='red', borderwidth=1, opacity=0.8)
    
    fig.add_annotation(x=lons[max_lat_idx], y=lats[max_lat_idx], 
                      text=f'MAX LAT<br>{lats[max_lat_idx]:.1f}°',
                      showarrow=True, arrowhead=2, arrowsize=1, arrowwidth=2, arrowcolor='orange',
                      ax=40, ay=40, bgcolor='lightyellow', bordercolor='orange', borderwidth=1, opacity=0.8)
    
    if station_lat is not None and station_lon is not None:
        station_lon_wrapped = ((station_lon + 180) % 360) - 180
        fig.add_annotation(x=station_lon_wrapped, y=station_lat,
                          text=f'STATION<br>({station_lat:.1f}°, {station_lon_wrapped:.1f}°)',
                          showarrow=True, arrowhead=2, arrowsize=1, arrowwidth=2, arrowcolor='darkred',
                          ax=-50, ay=-50, bgcolor='lightpink', bordercolor='darkred', borderwidth=1, opacity=0.8)
    
    fig.update_layout(title=title, 
                      xaxis_title="Longitude (deg)", yaxis_title="Latitude (deg)",
                      xaxis=dict(range=[-180, 180]), yaxis=dict(range=[-90, 90]),
                      hovermode='closest', width=1000, height=600)
    try:
        fig.write_image(out_path)
    except Exception:
        html_path = out_path.replace('.png', '.html')
        fig.write_html(html_path)
        return html_path
    return out_path
