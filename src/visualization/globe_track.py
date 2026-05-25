"""3D globe visualization using Pydeck.

Renders the satellite ground track and observer location on an interactive
3D globe. Designed to be embedded inside a Streamlit app via st.pydeck_chart.
"""
from __future__ import annotations

from typing import List, Sequence, Tuple

import pydeck as pdk

from .ground_track import ecef_to_geodetic_latlon


def build_globe_chart(
    ecef_series_km: Sequence[Tuple[float, float, float]],
    station_lat: float,
    station_lon: float,
    pass_events_latlon: List[Tuple[float, float]] | None = None,
) -> pdk.Deck:
    """Build a Pydeck 3D globe showing the satellite ground track.

    Args:
        ecef_series_km: Sequence of satellite ECEF positions in km.
        station_lat: Observer geodetic latitude in degrees.
        station_lon: Observer geodetic longitude in degrees.
        pass_events_latlon: Optional list of (lat, lon) points marking
            AOS/TCA/LOS events to highlight on the globe.

    Returns:
        A pdk.Deck object ready for st.pydeck_chart().
    """
    # Convert ECEF to lat/lon
    latlons = [ecef_to_geodetic_latlon(p) for p in ecef_series_km]

    # Build path data for the ground track line
    path_data = [
        {
            "path": [[lon, lat] for lat, lon in latlons],
            "name": "Ground Track",
            "color": [0, 180, 255],
        }
    ]

    # Build scatter data for the ground station
    station_data = [
        {
            "lat": station_lat,
            "lon": station_lon,
            "label": "Ground Station",
            "color": [255, 200, 0],
            "radius": 80000,
        }
    ]

    # Build scatter data for pass events (AOS/TCA/LOS)
    event_data = []
    event_colors = [
        [0, 255, 80],    # AOS - green
        [255, 120, 0],   # TCA - orange
        [255, 50, 50],   # LOS - red
    ]
    if pass_events_latlon:
        for idx, (lat, lon) in enumerate(pass_events_latlon):
            color = event_colors[idx % len(event_colors)]
            event_data.append({
                "lat": lat,
                "lon": lon,
                "color": color,
                "radius": 120000,
            })

    # Ground track path layer
    path_layer = pdk.Layer(
        "PathLayer",
        data=path_data,
        get_path="path",
        get_color="color",
        width_min_pixels=2,
        width_scale=5,
        pickable=False,
    )

    # Ground station marker
    station_layer = pdk.Layer(
        "ScatterplotLayer",
        data=station_data,
        get_position=["lon", "lat"],
        get_fill_color="color",
        get_radius="radius",
        pickable=True,
        tooltip=True,
    )

    # Pass event markers
    event_layer = pdk.Layer(
        "ScatterplotLayer",
        data=event_data,
        get_position=["lon", "lat"],
        get_fill_color="color",
        get_radius="radius",
        pickable=False,
        opacity=0.85,
    )

    # Centre the initial view on the ground station
    view_state = pdk.ViewState(
        latitude=station_lat,
        longitude=station_lon,
        zoom=2,
        pitch=30,
    )

    return pdk.Deck(
        layers=[path_layer, station_layer, event_layer],
        initial_view_state=view_state,
        map_provider="carto",
        map_style="dark_matter",
        tooltip={"text": "{label}"},
    )
