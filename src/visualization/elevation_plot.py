"""Elevation angle visualization (matplotlib and plotly)."""
from __future__ import annotations
from typing import Sequence
from datetime import datetime

import matplotlib.pyplot as plt
import plotly.graph_objects as go

from ..core import PassEvent


def plot_elevation_matplotlib(times: Sequence[datetime], elevations_deg: Sequence[float], passes: Sequence[PassEvent], out_path: str, threshold_deg: float = 10.0, title: str = "Elevation vs Time") -> str:
    """Plot elevation vs time with matplotlib."""
    fig, ax = plt.subplots(figsize=(14, 6))
    
    # Plot elevation curve
    ax.plot(times, elevations_deg, linewidth=2, color='blue', label='Elevation', zorder=3)
    
    # Plot threshold line
    ax.axhline(y=threshold_deg, color='orange', linestyle='--', linewidth=2, 
               label=f'Threshold ({threshold_deg}°)', zorder=2)
    
    # Plot horizon line
    ax.axhline(y=0, color='black', linestyle='-', linewidth=1, alpha=0.3, label='Horizon', zorder=1)
    
    # Annotate each pass
    for i, p in enumerate(passes, 1):
        # Green pass window
        ax.axvspan(p.start_time, p.end_time, color='green', alpha=0.15, zorder=0)
        
        # AOS marker and annotation
        aos_idx = min(range(len(times)), key=lambda j: abs(times[j] - p.start_time))
        aos_el = elevations_deg[aos_idx]
        ax.plot(p.start_time, aos_el, 'go', markersize=8)
        ax.annotate(f'AOS{i}\n{p.start_time.strftime("%H:%M:%S")}',
                   xy=(p.start_time, aos_el), xytext=(0, -30),
                   textcoords='offset points', fontsize=8, color='green',
                   bbox=dict(boxstyle='round,pad=0.4', facecolor='lightgreen', alpha=0.8),
                   arrowprops=dict(arrowstyle='->', color='green', lw=1),
                   ha='center')
        
        # LOS marker and annotation
        los_idx = min(range(len(times)), key=lambda j: abs(times[j] - p.end_time))
        los_el = elevations_deg[los_idx]
        ax.plot(p.end_time, los_el, 'ro', markersize=8)
        ax.annotate(f'LOS{i}\n{p.end_time.strftime("%H:%M:%S")}',
                   xy=(p.end_time, los_el), xytext=(0, -30),
                   textcoords='offset points', fontsize=8, color='red',
                   bbox=dict(boxstyle='round,pad=0.4', facecolor='lightcoral', alpha=0.8),
                   arrowprops=dict(arrowstyle='->', color='red', lw=1),
                   ha='center')
        
        # Max elevation marker and annotation
        max_el_idx = min(range(len(times)), key=lambda j: abs(times[j] - p.max_time))
        ax.plot(p.max_time, p.max_elevation_deg, 'm*', markersize=16)
        ax.annotate(f'MAX{i}\n{p.max_elevation_deg:.1f}°\n{p.max_time.strftime("%H:%M:%S")}',
                   xy=(p.max_time, p.max_elevation_deg), xytext=(0, 15),
                   textcoords='offset points', fontsize=8, color='purple',
                   bbox=dict(boxstyle='round,pad=0.4', facecolor='plum', alpha=0.8),
                   arrowprops=dict(arrowstyle='->', color='purple', lw=1),
                   ha='center')
        
        # Pass duration annotation
        duration_min = (p.end_time - p.start_time).total_seconds() / 60
        mid_time = p.start_time + (p.end_time - p.start_time) / 2
        mid_el = max(elevations_deg) * 0.85
        ax.text(mid_time, mid_el, f'Pass {i}\n{duration_min:.1f} min',
               ha='center', fontsize=7, style='italic', color='darkgreen',
               bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.6, edgecolor='green'))
    
    ax.set_title(title, fontsize=14, fontweight='bold')
    ax.set_xlabel("Time (UTC)", fontsize=11)
    ax.set_ylabel("Elevation (degrees)", fontsize=11)
    ax.grid(True, linestyle='--', alpha=0.3)
    ax.legend(loc='upper left', fontsize=9)
    
    # Format x-axis for better time display
    fig.autofmt_xdate(rotation=45)
    fig.tight_layout()
    fig.savefig(out_path, dpi=150, bbox_inches='tight')
    plt.close()
    return out_path


def plot_elevation_plotly(times: Sequence[datetime], elevations_deg: Sequence[float], passes: Sequence[PassEvent], out_path: str, threshold_deg: float = 10.0, title: str = "Elevation vs Time") -> str:
    """Plot elevation vs time with plotly (interactive)."""
    fig = go.Figure()
    
    # Main elevation curve
    fig.add_trace(go.Scattergl(x=times, y=elevations_deg, mode='lines', 
                               name='Elevation',
                               line=dict(color='blue', width=2)))
    
    # Threshold line
    fig.add_hline(y=threshold_deg, line_dash='dash', line_color='orange', 
                  name=f'Threshold ({threshold_deg}°)',
                  annotation_text=f'Threshold: {threshold_deg}°', annotation_position='right')
    
    # Horizon line
    fig.add_hline(y=0, line_dash='solid', line_color='black', opacity=0.3,
                  name='Horizon')
    
    # Annotate each pass
    for i, p in enumerate(passes, 1):
        # Pass window (green rectangle)
        fig.add_vrect(x0=p.start_time, x1=p.end_time, fillcolor='green', 
                      opacity=0.1, line_width=0, name=f'Pass {i}')
        
        # Find nearest elevation values for markers
        aos_idx = min(range(len(times)), key=lambda j: abs(times[j] - p.start_time))
        los_idx = min(range(len(times)), key=lambda j: abs(times[j] - p.end_time))
        aos_el = elevations_deg[aos_idx]
        los_el = elevations_deg[los_idx]
        
        # AOS marker
        fig.add_trace(go.Scattergl(x=[p.start_time], y=[aos_el], mode='markers',
                                   name=f'AOS{i}',
                                   marker=dict(size=8, color='green'),
                                   text=[f'AOS{i}<br>{p.start_time.strftime("%H:%M:%S")}<br>El: {aos_el:.1f}°'],
                                   hoverinfo='text', showlegend=False))
        
        # LOS marker
        fig.add_trace(go.Scattergl(x=[p.end_time], y=[los_el], mode='markers',
                                   name=f'LOS{i}',
                                   marker=dict(size=8, color='red'),
                                   text=[f'LOS{i}<br>{p.end_time.strftime("%H:%M:%S")}<br>El: {los_el:.1f}°'],
                                   hoverinfo='text', showlegend=False))
        
        # Max elevation marker
        fig.add_trace(go.Scattergl(x=[p.max_time], y=[p.max_elevation_deg], mode='markers',
                                   name=f'MAX{i}',
                                   marker=dict(size=12, color='purple', symbol='star'),
                                   text=[f'MAX{i}<br>{p.max_time.strftime("%H:%M:%S")}<br>El: {p.max_elevation_deg:.1f}°'],
                                   hoverinfo='text', showlegend=False))
        
        # Add annotations with arrows
        duration_min = (p.end_time - p.start_time).total_seconds() / 60
        fig.add_annotation(x=p.start_time, y=aos_el, 
                          text=f'AOS{i}<br>{p.start_time.strftime("%H:%M")}',
                          showarrow=True, arrowhead=2, arrowsize=1, arrowwidth=1.5, arrowcolor='green',
                          ax=0, ay=-40, bgcolor='lightgreen', bordercolor='green', borderwidth=1, opacity=0.8,
                          font=dict(size=8, color='green'))
        
        fig.add_annotation(x=p.end_time, y=los_el,
                          text=f'LOS{i}<br>{p.end_time.strftime("%H:%M")}',
                          showarrow=True, arrowhead=2, arrowsize=1, arrowwidth=1.5, arrowcolor='red',
                          ax=0, ay=-40, bgcolor='lightcoral', bordercolor='red', borderwidth=1, opacity=0.8,
                          font=dict(size=8, color='red'))
        
        fig.add_annotation(x=p.max_time, y=p.max_elevation_deg,
                          text=f'MAX{i}: {p.max_elevation_deg:.1f}°<br>{p.max_time.strftime("%H:%M:%S")}<br>Duration: {duration_min:.1f} min',
                          showarrow=True, arrowhead=2, arrowsize=1, arrowwidth=1.5, arrowcolor='purple',
                          ax=0, ay=40, bgcolor='plum', bordercolor='purple', borderwidth=1, opacity=0.8,
                          font=dict(size=8, color='purple'))
    
    fig.update_layout(title=title, 
                      xaxis_title="Time (UTC)", yaxis_title="Elevation (degrees)",
                      hovermode='x unified', width=1200, height=600,
                      showlegend=True)
    
    try:
        fig.write_image(out_path)
    except Exception:
        html_path = out_path.replace('.png', '.html')
        fig.write_html(html_path)
        return html_path
    return out_path
