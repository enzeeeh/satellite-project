from __future__ import annotations
from typing import Sequence
from datetime import datetime

import matplotlib.pyplot as plt
import plotly.graph_objects as go

from ..pass_detector import PassEvent


def plot_elevation_matplotlib(times: Sequence[datetime], elevations_deg: Sequence[float], passes: Sequence[PassEvent], out_path: str, title: str = "Elevation vs Time") -> str:
    plt.figure(figsize=(10, 4))
    plt.plot(times, elevations_deg, label='Elevation')
    for p in passes:
        plt.axvspan(p.start_time, p.end_time, color='green', alpha=0.2)
        plt.axvline(p.max_time, color='red', linestyle='--', alpha=0.6)
    plt.title(title)
    plt.xlabel("Time (UTC)")
    plt.ylabel("Elevation (deg)")
    plt.grid(True, linestyle='--', alpha=0.5)
    plt.tight_layout()
    plt.savefig(out_path, dpi=150)
    plt.close()
    return out_path


def plot_elevation_plotly(times: Sequence[datetime], elevations_deg: Sequence[float], passes: Sequence[PassEvent], out_path: str, title: str = "Elevation vs Time") -> str:
    fig = go.Figure()
    fig.add_trace(go.Scattergl(x=times, y=elevations_deg, mode='lines', name='Elevation'))
    for i, p in enumerate(passes):
        fig.add_vrect(x0=p.start_time, x1=p.end_time, fillcolor='green', opacity=0.2, line_width=0)
        fig.add_vline(x=p.max_time, line_dash='dash', line_color='red', opacity=0.6)
    fig.update_layout(title=title, xaxis_title="Time (UTC)", yaxis_title="Elevation (deg)")
    try:
        fig.write_image(out_path)
    except Exception:
        html_path = out_path.replace('.png', '.html')
        fig.write_html(html_path)
        return html_path
    return out_path
