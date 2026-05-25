"""Sky/polar plot showing satellite pass as seen from the observer.

The chart is a top-down view of the sky dome:
- Centre = zenith (directly overhead, 90 deg elevation)
- Outer ring = horizon (0 deg elevation)
- Angular axis = azimuth, clockwise from North (0=N, 90=E, 180=S, 270=W)

This view lets observers immediately see which direction to point and how
high the satellite will get during each pass.
"""
from __future__ import annotations

from datetime import datetime
from typing import List, Sequence, Tuple

import plotly.graph_objects as go

from ..core import PassEvent


def _elevation_to_radial(elevation_deg: float) -> float:
    """Convert elevation angle to polar radial distance.

    At zenith (90 deg) the radial value is 0 (centre of plot).
    At horizon (0 deg) the radial value is 90 (outer edge).
    """
    return 90.0 - elevation_deg


def plot_sky_polar(
    times: Sequence[datetime],
    elevations_deg: Sequence[float],
    azimuths_deg: Sequence[float],
    passes: Sequence[PassEvent],
    threshold_deg: float = 10.0,
    title: str = "Sky View",
) -> go.Figure:
    """Create an interactive polar sky plot with Plotly.

    Args:
        times: UTC timestamps for each sample.
        elevations_deg: Elevation angle in degrees for each sample.
        azimuths_deg: Azimuth angle in degrees for each sample (0=N, CW).
        passes: Detected pass events for annotation.
        threshold_deg: Elevation threshold used during detection.
        title: Chart title.

    Returns:
        Plotly Figure object (call .show() or embed in Streamlit).
    """
    fig = go.Figure()

    # Background threshold ring
    theta_ring = list(range(0, 361, 5))
    r_ring = [_elevation_to_radial(threshold_deg)] * len(theta_ring)
    fig.add_trace(go.Scatterpolar(
        r=r_ring,
        theta=theta_ring,
        mode="lines",
        line=dict(color="orange", width=1.5, dash="dash"),
        name=f"Threshold ({threshold_deg}°)",
        hoverinfo="skip",
    ))

    # Full satellite track (below threshold, dimmed)
    r_all = [_elevation_to_radial(max(e, 0.0)) for e in elevations_deg]
    fig.add_trace(go.Scatterpolar(
        r=r_all,
        theta=list(azimuths_deg),
        mode="lines",
        line=dict(color="lightblue", width=1),
        name="Full track",
        hoverinfo="skip",
        opacity=0.4,
    ))

    # One trace per pass (visible portion, above threshold)
    colors = [
        "#00cc44", "#3399ff", "#ff6600", "#cc00ff",
        "#ff3366", "#00cccc", "#ffcc00",
    ]

    for i, p in enumerate(passes):
        color = colors[i % len(colors)]

        # Gather samples within this pass window
        mask = [p.start_time <= t <= p.end_time for t in times]
        r_pass = [_elevation_to_radial(elevations_deg[j]) for j, m in enumerate(mask) if m]
        az_pass = [azimuths_deg[j] for j, m in enumerate(mask) if m]
        t_pass = [times[j] for j, m in enumerate(mask) if m]

        if not r_pass:
            continue

        hover = [
            f"Az: {az:.1f}° | El: {90 - r:.1f}°<br>{t.strftime('%H:%M:%S UTC')}"
            for r, az, t in zip(r_pass, az_pass, t_pass)
        ]

        fig.add_trace(go.Scatterpolar(
            r=r_pass,
            theta=az_pass,
            mode="lines",
            line=dict(color=color, width=3),
            name=f"Pass {i + 1}",
            text=hover,
            hoverinfo="text",
        ))

        # AOS marker
        fig.add_trace(go.Scatterpolar(
            r=[r_pass[0]],
            theta=[az_pass[0]],
            mode="markers+text",
            marker=dict(color="green", size=12, symbol="circle"),
            text=[f"AOS {i + 1}"],
            textposition="top right",
            textfont=dict(color="#00ff88", size=11),
            showlegend=False,
            hoverinfo="skip",
        ))

        # LOS marker
        fig.add_trace(go.Scatterpolar(
            r=[r_pass[-1]],
            theta=[az_pass[-1]],
            mode="markers+text",
            marker=dict(color="red", size=12, symbol="circle"),
            text=[f"LOS {i + 1}"],
            textposition="top right",
            textfont=dict(color="#ff6666", size=11),
            showlegend=False,
            hoverinfo="skip",
        ))

        # Max elevation marker (star)
        max_idx = min(
            range(len(t_pass)),
            key=lambda j: abs(t_pass[j] - p.max_time),
        )
        fig.add_trace(go.Scatterpolar(
            r=[r_pass[max_idx]],
            theta=[az_pass[max_idx]],
            mode="markers+text",
            marker=dict(color=color, size=16, symbol="star"),
            text=[f"{p.max_elevation_deg:.1f}°"],
            textposition="top right",
            textfont=dict(color="#ffdd00", size=11),
            showlegend=False,
            hovertemplate=(
                f"Pass {i + 1} max<br>"
                f"El: {p.max_elevation_deg:.1f}°<br>"
                f"Az: {az_pass[max_idx]:.1f}°<br>"
                f"{p.max_time.strftime('%H:%M:%S UTC')}"
                "<extra></extra>"
            ),
        ))

    fig.update_layout(
        title=dict(text=title, x=0.5),
        polar=dict(
            angularaxis=dict(
                tickmode="array",
                tickvals=[0, 45, 90, 135, 180, 225, 270, 315],
                ticktext=["N", "NE", "E", "SE", "S", "SW", "W", "NW"],
                direction="clockwise",
                rotation=90,
                tickfont=dict(color="white", size=12),
                linecolor="rgba(180,180,180,0.4)",
            ),
            radialaxis=dict(
                range=[0, 90],
                tickmode="array",
                tickvals=[0, 30, 60, 90],
                ticktext=["90°", "60°", "30°", "0°"],
                tickfont=dict(color="rgba(200,200,200,0.8)", size=10),
                gridcolor="rgba(180,180,180,0.4)",
            ),
            bgcolor="rgba(10, 10, 30, 0.95)",
        ),
        paper_bgcolor="#0d1117",
        font=dict(color="white"),
        legend=dict(
            bgcolor="rgba(30,30,30,0.8)",
            bordercolor="gray",
            borderwidth=1,
        ),
        height=600,
    )

    return fig
