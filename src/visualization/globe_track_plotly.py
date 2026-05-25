"""3D globe visualization using Plotly Scattergeo.

Uses Plotly's built-in offline geography data — no external tile server,
no API key, and no internet connection required.
"""
from __future__ import annotations

from typing import List, Optional, Sequence, Tuple

import plotly.graph_objects as go

from .ground_track import ecef_to_geodetic_latlon


def build_globe_chart(
    ecef_series_km: Sequence[Tuple[float, float, float]],
    station_lat: float,
    station_lon: float,
    pass_events_latlon: Optional[List[Tuple[float, float]]] = None,
) -> go.Figure:
    """Build a Plotly 3D orthographic globe showing the satellite ground track.

    Args:
        ecef_series_km:    Sequence of satellite ECEF positions in km.
        station_lat:       Observer geodetic latitude in degrees.
        station_lon:       Observer geodetic longitude in degrees.
        pass_events_latlon: Optional list of (lat, lon) tuples in groups of 3
                            (AOS, TCA, LOS) for each pass, to highlight on the globe.

    Returns:
        A go.Figure object ready for st.plotly_chart().
    """
    # Convert ECEF positions to lat/lon
    latlons = [ecef_to_geodetic_latlon(p) for p in ecef_series_km]
    track_lats = [ll[0] for ll in latlons]
    track_lons = [ll[1] for ll in latlons]

    fig = go.Figure()

    # ---- Satellite ground track ----
    fig.add_trace(go.Scattergeo(
        lat=track_lats,
        lon=track_lons,
        mode="lines",
        line=dict(color="#00aaff", width=1.5),
        name="Ground Track",
        hoverinfo="skip",
    ))

    # ---- Observer / ground station ----
    fig.add_trace(go.Scattergeo(
        lat=[station_lat],
        lon=[station_lon],
        mode="markers+text",
        marker=dict(color="#ffd700", size=12, symbol="circle"),
        text=["Your Station"],
        textfont=dict(color="#ffd700", size=11),
        textposition="top right",
        name="Your Station",
        hovertemplate=(
            f"<b>Your Station</b><br>"
            f"Lat: {station_lat:.3f}°<br>"
            f"Lon: {station_lon:.3f}°"
            "<extra></extra>"
        ),
    ))

    # ---- Pass event markers (AOS / TCA / LOS) ----
    if pass_events_latlon:
        event_types = ["AOS", "TCA", "LOS"]
        event_colors = ["#00ff66", "#ff8800", "#ff3333"]

        for type_idx, (etype, color) in enumerate(zip(event_types, event_colors)):
            e_lats = [pass_events_latlon[i][0]
                      for i in range(type_idx, len(pass_events_latlon), 3)]
            e_lons = [pass_events_latlon[i][1]
                      for i in range(type_idx, len(pass_events_latlon), 3)]
            pass_nums = [i // 3 + 1
                         for i in range(type_idx, len(pass_events_latlon), 3)]
            hover = [f"<b>{etype} — Pass {n}</b><br>Lat: {la:.2f}°<br>Lon: {lo:.2f}°"
                     for n, la, lo in zip(pass_nums, e_lats, e_lons)]

            fig.add_trace(go.Scattergeo(
                lat=e_lats,
                lon=e_lons,
                mode="markers",
                marker=dict(color=color, size=9, symbol="circle",
                            line=dict(color="white", width=0.5)),
                name=etype,
                text=hover,
                hoverinfo="text",
            ))

    # ---- Layout ----
    fig.update_layout(
        geo=dict(
            projection_type="orthographic",
            # Centre the view on the observer location
            projection_rotation=dict(lon=station_lon, lat=station_lat, roll=0),
            showland=True,
            landcolor="rgb(42, 58, 72)",
            showocean=True,
            oceancolor="rgb(8, 22, 42)",
            showcountries=True,
            countrycolor="rgba(130, 150, 170, 0.6)",
            countrywidth=0.5,
            showcoastlines=True,
            coastlinecolor="rgba(140, 170, 200, 0.9)",
            coastlinewidth=0.8,
            showlakes=True,
            lakecolor="rgb(8, 22, 42)",
            showframe=False,
            bgcolor="rgb(5, 10, 20)",
            lataxis=dict(
                showgrid=True,
                gridcolor="rgba(80, 80, 80, 0.25)",
                gridwidth=0.5,
            ),
            lonaxis=dict(
                showgrid=True,
                gridcolor="rgba(80, 80, 80, 0.25)",
                gridwidth=0.5,
            ),
        ),
        paper_bgcolor="rgb(13, 17, 23)",
        font=dict(color="white"),
        legend=dict(
            bgcolor="rgba(25, 30, 40, 0.85)",
            bordercolor="rgba(100, 100, 120, 0.5)",
            borderwidth=1,
            font=dict(color="white", size=12),
        ),
        margin=dict(l=0, r=0, t=10, b=0),
        height=600,
    )

    return fig
