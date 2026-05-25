"""LLM-based explanation helper for satellite pass prediction results.

Supports any OpenAI-compatible API endpoint:
  - Ollama  (local, free)  http://localhost:11434/v1
  - OpenAI  (cloud)        https://api.openai.com/v1
  - Groq    (cloud, fast)  https://api.groq.com/openai/v1
  - Any custom endpoint that speaks the OpenAI chat-completions protocol.
"""
from __future__ import annotations

from typing import Generator, List


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _quality_label(el_deg: float) -> str:
    if el_deg >= 60:
        return "Excellent"
    elif el_deg >= 30:
        return "Good"
    elif el_deg >= 15:
        return "Fair"
    return "Low"


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def build_explanation_prompt(
    sat_name: str,
    lat: float,
    lon: float,
    alt_m: float,
    hours: float,
    threshold_deg: float,
    passes: list,
    ml_applied: bool,
) -> str:
    """Build the prompt that will be sent to the LLM.

    Args:
        passes: List of PassEvent objects from src.core.pass_detector.
    """
    pass_lines: List[str] = []
    for i, p in enumerate(passes, 1):
        duration_s = (p.end_time - p.start_time).total_seconds()
        quality = _quality_label(p.max_elevation_deg)
        pass_lines.append(
            f"  Pass {i}: "
            f"AOS {p.start_time.strftime('%Y-%m-%d %H:%M')} UTC | "
            f"TCA {p.max_time.strftime('%H:%M')} UTC (max elevation {p.max_elevation_deg:.1f}°) | "
            f"LOS {p.end_time.strftime('%H:%M')} UTC | "
            f"duration {duration_s:.0f} s | quality: {quality}"
        )

    passes_text = (
        "\n".join(pass_lines) if pass_lines
        else "  No passes detected above the minimum elevation threshold."
    )

    ml_note = (
        "Yes — a trained neural-network model was applied to reduce SGP4 along-track drift errors."
        if ml_applied
        else "No — standard SGP4 propagation only (no ML correction)."
    )

    return f"""You are a friendly satellite-tracking and amateur-radio expert.
Explain the satellite pass prediction results below in plain, easy-to-understand language
for someone completely new to this topic. Define every technical term you use.

=== PREDICTION RESULTS ===
Satellite          : {sat_name}
Observer location  : {lat:.4f}° lat, {lon:.4f}° lon, {alt_m:.0f} m altitude
Prediction window  : next {hours:.0f} hours
Min elevation used : {threshold_deg:.1f}° (passes below this are ignored)
ML correction      : {ml_note}

Passes found ({len(passes)} total):
{passes_text}
=== END ===

Please cover all of the following points clearly:

1. **Plain-English summary** — what do these results tell me in one or two sentences?
2. **AOS, TCA, LOS** — what do these abbreviations stand for and what do they mean in practice?
3. **Elevation** — why does a higher elevation angle matter, and what do the numbers mean for visibility?
4. **Best passes** — which pass(es) should I pay attention to and why?
5. **Quality ratings** — what do Excellent (≥60°), Good (30–60°), Fair (15–30°), and Low (<15°) actually feel like in practice?
6. **ML correction** — in simple terms, what does applying a machine-learning correction do?
7. **Practical tips** — one or two actionable tips for actually observing or communicating through this satellite.

Keep the tone warm, educational, and accessible — like explaining to a curious beginner.
Avoid overwhelming them; keep each section concise.
Use proper markdown formatting: **bold** for section headers, and `- ` bullet points where lists are needed."""


def build_visual_prompt(tab: str, sat_name: str, passes: list) -> str:
    """Build a short, chart-specific explanation prompt for a visualization tab.

    Args:
        tab:      One of "elevation", "skyview", "groundtrack", "globe".
        sat_name: Human-readable satellite name.
        passes:   List of PassEvent objects.
    """
    n = len(passes)
    pass_summary = f"{n} pass{'es' if n != 1 else ''} detected" if passes else "no passes detected"
    best = max(passes, key=lambda p: p.max_elevation_deg) if passes else None
    best_el = f"{best.max_elevation_deg:.1f}°" if best else "N/A"

    base = (
        f"You are a friendly satellite-tracking expert. "
        f"Reply with exactly 3-4 bullet points using proper markdown format: "
        f"start each point with `- ` (a hyphen followed by a space). "
        f"No headers, no numbered lists, no Unicode bullet characters (•). "
        f"Be beginner-friendly and concise.\n\n"
        f"Satellite: {sat_name} | {pass_summary} | best elevation: {best_el}\n\n"
    )

    if tab == "elevation":
        return base + (
            "Explain the Elevation over Time chart. Cover: "
            "(1) what the elevation angle Y-axis means in plain terms, "
            "(2) why the curve rises and then falls during a pass, "
            "(3) what the shaded pass windows represent, "
            "(4) one practical insight a beginner can take away from this chart."
        )
    if tab == "skyview":
        return base + (
            "Explain the Sky View polar chart. Cover: "
            "(1) how to read it — centre = zenith (directly overhead), outer ring = horizon, "
            "(2) what each arc drawn on it represents, "
            "(3) what the compass angle (azimuth) tells you about where to look, "
            "(4) one practical insight a beginner can take away from this chart."
        )
    if tab == "groundtrack":
        return base + (
            "Explain the Ground Track map. Cover: "
            "(1) what a ground track is and why it matters, "
            "(2) why the path curves on a flat map, "
            "(3) what the observer marker on the map shows, "
            "(4) one practical insight a beginner can take away from this map."
        )
    if tab == "globe":
        return base + (
            "Explain the 3D Globe view. Cover: "
            "(1) what the line on the globe represents, "
            "(2) what the yellow observer dot shows, "
            "(3) what the highlighted pass event markers along the track mean, "
            "(4) one practical insight a beginner can take away from this 3D view."
        )
    return base + "Explain what this satellite visualization shows in simple terms."


def stream_explanation(prompt: str) -> Generator[str, None, None]:
    """Call the Groq API and stream back text chunks.

    Reads GROQ_API_KEY from the environment (loaded from .env by app.py).

    Yields:
        String chunks as they arrive from the model.
    """
    import os
    from openai import OpenAI

    client = OpenAI(
        api_key=os.environ["GROQ_API_KEY"],
        base_url="https://api.groq.com/openai/v1",
    )
    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": prompt}],
        stream=True,
        temperature=0.7,
        max_tokens=1200,
    )
    for chunk in response:
        delta = chunk.choices[0].delta.content
        if delta:
            yield delta
