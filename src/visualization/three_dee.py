"""3D Orbit Visualization using Plotly."""
from typing import List, Tuple
import plotly.graph_objects as go
import numpy as np
from src.core.ground_station import GroundStation, _A as EARTH_RADIUS_KM

def plot_3d_orbit_plotly(
    ecef_series: List[Tuple[float, float, float]],
    output_path: str,
    station_lat: float,
    station_lon: float,
    visible_indices: List[int],
):
    """
    Generates an interactive 3D plot of the satellite's orbit.
    """
    # Create the Earth sphere
    u = np.linspace(0, 2 * np.pi, 100)
    v = np.linspace(0, np.pi, 100)
    x_earth = EARTH_RADIUS_KM * np.outer(np.cos(u), np.sin(v))
    y_earth = EARTH_RADIUS_KM * np.outer(np.sin(u), np.sin(v))
    z_earth = EARTH_RADIUS_KM * np.outer(np.ones(np.size(u)), np.cos(v))

    earth = go.Surface(x=x_earth, y=y_earth, z=z_earth, colorscale=[[0, 'blue'], [1, 'blue']], showscale=False, cmin=0, cmax=1)

    # Unpack ECEF coordinates for the orbit
    x_orbit, y_orbit, z_orbit = zip(*ecef_series)

    # Create the orbit path
    orbit_trace = go.Scatter3d(
        x=x_orbit, y=y_orbit, z=z_orbit,
        mode='lines',
        line=dict(color='red', width=2),
        name='Orbit'
    )

    # Create visible segments
    x_vis, y_vis, z_vis = [], [], []
    for i in visible_indices:
        x_vis.append(x_orbit[i])
        y_vis.append(y_orbit[i])
        z_vis.append(z_orbit[i])

    visible_trace = go.Scatter3d(
        x=x_vis, y=y_vis, z=z_vis,
        mode='markers',
        marker=dict(color='yellow', size=3),
        name='Visible'
    )

    # Calculate ground station ECEF coordinates
    gs = GroundStation(lat_deg=station_lat, lon_deg=station_lon, alt_m=0)
    gs_x, gs_y, gs_z = gs.ecef_km()

    # Create the ground station marker
    gs_trace = go.Scatter3d(
        x=[gs_x], y=[gs_y], z=[gs_z],
        mode='markers',
        marker=dict(color='green', size=7, symbol='diamond'),
        name='Ground Station'
    )

    fig = go.Figure(data=[earth, orbit_trace, gs_trace, visible_trace])
    fig.update_layout(
        title_text='Satellite Orbit Visualization',
        scene=dict(
            xaxis_title='X (km)',
            yaxis_title='Y (km)',
            zaxis_title='Z (km)',
            aspectmode='data'
        )
    )
    fig.write_html(output_path)
