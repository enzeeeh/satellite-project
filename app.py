"""Satellite Pass Predictor - Streamlit Dashboard.

Run with:
    streamlit run app.py

Loads Space-Track credentials automatically from a .env file if present.
"""
from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import List, Tuple

import streamlit as st

# Load .env credentials before any other imports that might need them
try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent / ".env")
except ImportError:
    pass  # python-dotenv not installed; env vars must be set manually

from src.core import (
    load_tle,
    satrec_from_tle,
    propagate_teme,
    gmst_angle,
    teme_to_ecef,
    GroundStation,
    detect_passes,
    PassEvent,
    fetch_tle_celestrak,
    fetch_tle_spacetrack,
)
from src.visualization import (
    plot_elevation_plotly,
    plot_ground_track_plotly,
    plot_sky_polar,
)

# Globe visualization (Plotly-based, always available)
from src.visualization import build_globe_chart
_PYDECK_AVAILABLE = True  # kept for tab-label logic; always True now

# AI explainer is optional (openai package may not be installed)
try:
    import openai as _openai_pkg  # noqa: F401
    _OPENAI_AVAILABLE = True
except ImportError:
    _OPENAI_AVAILABLE = False


# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Satellite Pass Predictor",
    page_icon="satellite",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("Satellite Pass Predictor")
st.caption("Predict when a satellite is visible from your location.")


# ---------------------------------------------------------------------------
# Preset observer locations: "City, Country" -> (lat_deg, lon_deg, altitude_m)
# ---------------------------------------------------------------------------
_CITIES = {
    # Indonesia
    "Jakarta, Indonesia":         (-6.2088, 106.8456,   8.0),
    "Surabaya, Indonesia":        (-7.2575, 112.7521,   5.0),
    "Bandung, Indonesia":         (-6.9175, 107.6191, 768.0),
    "Medan, Indonesia":           ( 3.5952,  98.6722,  25.0),
    "Semarang, Indonesia":        (-6.9667, 110.4167,   2.0),
    "Makassar, Indonesia":        (-5.1477, 119.4327,   5.0),
    "Palembang, Indonesia":       (-2.9761, 104.7754,   8.0),
    "Yogyakarta, Indonesia":      (-7.7956, 110.3695, 113.0),
    "Denpasar (Bali), Indonesia": (-8.6705, 115.2126,   4.0),
    "Balikpapan, Indonesia":      (-1.2379, 116.8529,  10.0),
    "Manado, Indonesia":          ( 1.4748, 124.8421,  13.0),
    "Padang, Indonesia":          (-0.9471, 100.4172,   4.0),
    "Pekanbaru, Indonesia":       ( 0.5071, 101.4478,  10.0),
    "Malang, Indonesia":          (-7.9797, 112.6304, 429.0),
    "Pontianak, Indonesia":       (-0.0263, 109.3425,   3.0),
    "Batam, Indonesia":           ( 1.0456, 104.0305,  30.0),
    # Rest of the world (for demos)
    "Singapore":                  ( 1.3521, 103.8198,  15.0),
    "Kuala Lumpur, Malaysia":     ( 3.1390, 101.6869,  66.0),
    "Tokyo, Japan":               (35.6762, 139.6503,  40.0),
    "Sydney, Australia":          (-33.8688, 151.2093, 58.0),
    "London, UK":                 (51.5074,  -0.1278,  11.0),
    "New York, USA":              (40.7128, -74.0060,  10.0),
}
_CUSTOM_LOCATION = "📍 Custom (enter coordinates…)"


# ---------------------------------------------------------------------------
# TLE freshness helpers (used in the sidebar, so defined before it)
# ---------------------------------------------------------------------------
def _tle_age_days(line1: str):
    """Age (in days) of a TLE at the current time, parsed from its epoch field. None on error."""
    try:
        s = line1[18:32].strip()
        yy = int(s[:2]); year = 2000 + yy if yy < 57 else 1900 + yy
        epoch = datetime(year, 1, 1, tzinfo=timezone.utc) + timedelta(days=float(s[2:]) - 1)
        return max(0.0, (datetime.now(timezone.utc) - epoch).total_seconds() / 86400.0)
    except Exception:
        return None


def _freshness(age_days: float):
    """Map a TLE age to a freshness rating. Returns (emoji, label, streamlit-level, message)."""
    if age_days < 1.0:
        return ("🟢", "Fresh", "success",
                "Predictions should be reliable — this orbital data is up to date.")
    if age_days < 4.0:
        return ("🟡", "Aging", "info",
                "Still usable, but accuracy slips as the data ages (SGP4 error grows a few km per day "
                "for low orbits). Fetch a newer TLE for best results.")
    return ("🔴", "Stale", "warning",
            "This data is old — the prediction could be off by tens of km. Switch the sidebar TLE source "
            "to a live fetch to get the latest orbit.")


# ---------------------------------------------------------------------------
# Sidebar: inputs
# ---------------------------------------------------------------------------
with st.sidebar:
    st.header("Observer Location")
    st.caption("Pick your city, or choose Custom to type exact coordinates. The app uses this to work out which satellite passes are visible from your spot.")
    _location = st.selectbox("City", list(_CITIES.keys()) + [_CUSTOM_LOCATION], index=0)
    if _location == _CUSTOM_LOCATION:
        lat = st.number_input("Latitude (deg)", min_value=-90.0, max_value=90.0, value=-6.2088, step=0.1, format="%.4f")
        lon = st.number_input("Longitude (deg)", min_value=-180.0, max_value=180.0, value=106.8456, step=0.1, format="%.4f")
        alt_m = st.number_input("Altitude (m)", min_value=0.0, max_value=8848.0, value=8.0, step=10.0)
    else:
        lat, lon, alt_m = _CITIES[_location]
        st.caption(f"📍 {lat:.4f}°,  {lon:.4f}°,  {alt_m:.0f} m above sea level")

    st.divider()
    st.header("Satellite")
    st.caption("Pick where to get the satellite's orbital data (TLE). Use a local file for offline use, or fetch live data from CelesTrak / Space-Track for up-to-date orbits.")
    data_source = st.radio(
        "TLE source",
        ["Local file", "CelesTrak (live)", "Space-Track (live)"],
        index=0,
    )

    tle_name, tle_line1, tle_line2 = None, None, None
    fetch_error = None

    if data_source == "Local file":
        tle_dir = Path("data")
        tle_files = sorted(tle_dir.rglob("*.txt"))
        if tle_files:
            selected = st.selectbox(
                "TLE file",
                options=tle_files,
                format_func=lambda p: str(p.relative_to(tle_dir)),
            )
            try:
                tle_name, tle_line1, tle_line2 = load_tle(str(selected))
            except Exception as e:
                fetch_error = str(e)
        else:
            st.warning("No .txt files found in data/.")

    else:
        norad_id = st.number_input("NORAD Catalog ID", min_value=1, value=43017, step=1)
        fetch_btn = st.button("Fetch latest TLE")
        if fetch_btn:
            with st.spinner("Fetching TLE..."):
                try:
                    if data_source == "CelesTrak (live)":
                        tle_name, tle_line1, tle_line2 = fetch_tle_celestrak(int(norad_id))
                    else:
                        tle_name, tle_line1, tle_line2 = fetch_tle_spacetrack(int(norad_id))
                    st.session_state["tle"] = (tle_name, tle_line1, tle_line2)
                    st.success(f"Fetched: {tle_name}")
                except Exception as e:
                    fetch_error = str(e)

        if "tle" in st.session_state:
            tle_name, tle_line1, tle_line2 = st.session_state["tle"]
            st.caption(f"Loaded: **{tle_name}**")

    if fetch_error:
        st.error(f"TLE error: {fetch_error}")

    # -- TLE freshness meter --
    if tle_line1:
        _age = _tle_age_days(tle_line1)
        if _age is not None:
            _emoji, _label, _, _ = _freshness(_age)
            st.caption(f"{_emoji} TLE age: **{_age:.1f} days** — {_label}")

    st.divider()
    st.header("Prediction Window")
    st.caption("Control how far ahead to scan, the minimum elevation a pass must reach to count, and how finely to sample the orbit (smaller step = more accurate but slower).")
    hours = st.slider("Hours ahead", min_value=1, max_value=168, value=48, step=1)
    threshold = st.slider("Min elevation (deg)", min_value=0, max_value=89, value=10, step=1)
    step_sec = st.select_slider("Time step (sec)", options=[10, 15, 30, 60, 120], value=30)

    st.divider()
    st.header("AI Explanation")
    _groq_key = os.environ.get("GROQ_API_KEY", "")
    if not _OPENAI_AVAILABLE:
        st.caption("Install `openai` to enable: `pip install openai`")
        llm_enabled = False
    elif not _groq_key:
        st.caption("Add `GROQ_API_KEY=...` to your `.env` file to enable AI explanations.")
        llm_enabled = False
    else:
        llm_enabled = st.toggle("Explain results with AI", value=False)
        if llm_enabled:
            st.caption("Powered by Groq — llama-3.1-8b-instant")

    st.divider()
    run_btn = st.button("Run Prediction", type="primary", use_container_width=True)


# ---------------------------------------------------------------------------
# Run prediction
# ---------------------------------------------------------------------------
def _run_prediction(
    line1: str,
    line2: str,
    lat: float,
    lon: float,
    alt_m: float,
    hours: float,
    threshold_deg: float,
    step_sec: float,
) -> Tuple[List[datetime], List[float], List[float], List[Tuple], List[PassEvent]]:
    """Propagate satellite and detect passes. Returns parallel lists."""
    sat = satrec_from_tle(line1, line2)
    station = GroundStation(lat_deg=lat, lon_deg=lon, alt_m=alt_m)

    start = datetime.now(timezone.utc)
    end = start + timedelta(hours=hours)

    times, elevations, azimuths, ecef_series = [], [], [], []
    t = start
    delta = timedelta(seconds=step_sec)

    while t <= end:
        try:
            state = propagate_teme(sat, t)
            gmst = gmst_angle(t)
            ecef = teme_to_ecef(state.r_km, gmst)
            el, az = station.elevation_azimuth_deg(ecef)
            times.append(t)
            elevations.append(el)
            azimuths.append(az)
            ecef_series.append(ecef)
        except RuntimeError:
            pass
        t += delta

    passes = detect_passes(times, elevations, threshold_deg)
    return times, elevations, azimuths, ecef_series, passes


# ---------------------------------------------------------------------------
# Pass quality helper
# ---------------------------------------------------------------------------
def _pass_quality(max_el: float) -> str:
    if max_el >= 60:
        return "Excellent"
    if max_el >= 30:
        return "Good"
    if max_el >= 15:
        return "Fair"
    return "Low"


def _quality_color(quality: str) -> str:
    return {"Excellent": "green", "Good": "blue", "Fair": "orange", "Low": "red"}.get(quality, "gray")


# ---------------------------------------------------------------------------
# Educational tab help + summary
# ---------------------------------------------------------------------------
_TAB_HELP = {
    "passes": {
        "what": "Every time the satellite climbs above your horizon during the window, listed as a schedule.",
        "look": "**AOS** = it rises into view, **TCA** = its highest point, **LOS** = it sets. **Max El** is how high it gets in degrees (higher is better); the colour rates each pass.",
        "why": "This is your “when to watch or listen” list.",
    },
    "elevation": {
        "what": "The satellite's height above your horizon (in degrees) plotted over time.",
        "look": "Each hump is one pass. A taller hump means a higher, better pass. The dashed line is your minimum-elevation cut-off — anything below it is ignored.",
        "why": "Shows how good each pass is and roughly how long it stays up.",
    },
    "skyview": {
        "what": "A radar-style map of where the satellite crosses the sky directly above you.",
        "look": "The centre is straight up (90°), the outer edge is the horizon (0°). The arc is the flight path; the compass ring tells you which way to face.",
        "why": "Tells you where to point your eyes or antenna.",
    },
    "groundtrack": {
        "what": "The point on Earth directly beneath the satellite, drawn on a world map.",
        "look": "The wavy line is the orbit's path over the ground; the marker is your location. The closer the line passes to you, the better the pass.",
        "why": "Shows the global path and when the satellite swings near you.",
    },
    "globe": {
        "what": "The same orbital track shown on an interactive 3-D globe.",
        "look": "Drag to rotate, scroll to zoom. Yellow = you, Green = rise (AOS), Orange = closest point (TCA), Red = set (LOS).",
        "why": "Gives an intuitive 3-D feel for the orbit's shape and tilt.",
    },
}


def _tab_help(key: str) -> None:
    """Render a consistent 'what am I looking at' box at the top of a tab."""
    h = _TAB_HELP[key]
    st.info(
        f"**What this shows** — {h['what']}\n\n"
        f"**What to look for** — {h['look']}\n\n"
        f"**Why it matters** — {h['why']}"
    )


def _compass(azimuth_deg: float) -> str:
    """Convert an azimuth in degrees to an 8-point compass direction."""
    dirs = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]
    return dirs[int((azimuth_deg % 360) / 45.0 + 0.5) % 8]


def _render_how_it_works():
    """Explain the core prediction pipeline, tying each step to the tab that shows it."""
    with st.expander("🔬 How does this prediction actually work? (the 5 steps)", expanded=True):
        st.markdown(
            "The app never *watches* the satellite — it **calculates** where it will be, using "
            "physics. Every tab you saw is one link in this chain:\n\n"

            "**1 · Start with the TLE — the orbit's fingerprint.**  \n"
            "A *Two-Line Element set* (TLE) is a small block of numbers describing the satellite's "
            "orbit at one moment: its size, shape, tilt, and where it was. It's the input you loaded "
            "in the sidebar.\n\n"

            "**2 · Propagate with SGP4 — the physics engine.**  \n"
            "SGP4 is the industry-standard model that takes the TLE and computes the satellite's "
            "position in space at *any* time — now, in 10 minutes, in 2 days — by stepping forward "
            "and applying orbital physics (gravity, Earth's bulge, atmospheric drag). This is the "
            "**heart of the whole prediction**; the app runs it at every time step across your window.\n\n"

            "**3 · Convert to a spot on Earth.**  \n"
            "SGP4's position is in a space-fixed frame that ignores Earth's spin, so the app rotates "
            "it into an Earth-fixed frame (accounting for how far Earth has turned) to get the point "
            "on the globe directly beneath the satellite. → the **Ground Track** and **Globe** tabs.\n\n"

            "**4 · Point it at *your* sky.**  \n"
            "From your city's coordinates, the app works out — at each moment — how high the satellite "
            "sits above your horizon (**elevation**) and which compass direction it's in (**azimuth**). "
            "→ elevation is the **Elevation** tab; direction is the **Sky View** tab.\n\n"

            "**5 · Find the passes.**  \n"
            "It then scans that elevation-over-time curve. Each time the satellite climbs above your "
            "minimum-elevation threshold and comes back down, that's **one visible pass** — the app "
            "records when it rises (**AOS**), its highest point (**TCA**), and when it sets (**LOS**). "
            "→ the **Passes** tab and the numbers at the top of this Summary.\n\n"

            "---\n"
            "**In one line:**  TLE → SGP4 physics → rotate to Earth → your local sky → detect passes.  \n"
            "No cameras, no live tracking — just orbital mechanics run forward in time.\n\n"

            "**How accurate is it?** As accurate as the TLE is *fresh*. A TLE drifts as it ages "
            "(for the ISS, position error grows on the order of a few km per day), which is why the "
            "app fetches the **latest** TLE instead of reusing an old one."
        )


def _render_freshness_meter(tle_age_days):
    """Prominent TLE-freshness callout tying data age to expected reliability."""
    if tle_age_days is None:
        return
    emoji, label, level, message = _freshness(tle_age_days)
    text = (f"{emoji} **TLE freshness: {label}** — this orbital data is **{tle_age_days:.1f} days old.**  \n"
            f"{message}")
    getattr(st, level)(text)


def _render_summary(sat_name, passes, times, azimuths, hours, threshold_deg, tle_age_days=None):
    """Plain-English conclusion that ties every tab together."""
    st.subheader(f"Summary — {sat_name}")
    _render_freshness_meter(tle_age_days)

    if not passes:
        st.warning(
            f"**No visible passes** for **{sat_name}** above **{threshold_deg:.0f}°** "
            f"in the next **{hours:.0f} hours**.\n\n"
            "Try lowering the *Min elevation* threshold or increasing *Hours ahead* in the "
            "sidebar, then run the prediction again."
        )
        _render_how_it_works()
        return

    now = datetime.now(timezone.utc)
    best = max(passes, key=lambda p: p.max_elevation_deg)
    nxt = min(passes, key=lambda p: p.start_time)
    hrs_to_next = (nxt.start_time - now).total_seconds() / 3600.0
    best_quality = _pass_quality(best.max_elevation_deg)

    # Compass direction the satellite faces at the best pass's peak
    try:
        idx = min(range(len(times)), key=lambda j: abs(times[j] - best.max_time))
        best_dir = _compass(azimuths[idx])
    except (ValueError, IndexError):
        best_dir = "?"

    st.markdown(
        "### 🛰️ Bottom line\n"
        f"**{sat_name}** makes **{len(passes)}** visible pass(es) over your location in the next "
        f"**{hours:.0f} hours**. The **best** one is a **{best_quality}** pass on "
        f"**{best.max_time.strftime('%b %d, %H:%M UTC')}**, reaching **{best.max_elevation_deg:.0f}°** "
        f"high toward the **{best_dir}**."
    )

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Passes found", len(passes))
    c2.metric("Best elevation", f"{best.max_elevation_deg:.0f}°", help="Higher = better / closer pass")
    c3.metric("Next pass in", f"{max(hrs_to_next, 0):.1f} h")
    c4.metric("Best quality", best_quality)

    from collections import Counter
    counts = Counter(_pass_quality(p.max_elevation_deg) for p in passes)
    breakdown = "  ·  ".join(f"{q}: {counts[q]}" for q in ["Excellent", "Good", "Fair", "Low"] if counts.get(q))
    st.caption(f"**Quality mix:** {breakdown}")

    dur_min = (best.end_time - best.start_time).total_seconds() / 60.0
    st.markdown(
        f"**Best pass detail** — rises (AOS) {best.start_time.strftime('%H:%M:%S')} · "
        f"peak (TCA) {best.max_time.strftime('%H:%M:%S')} at {best.max_elevation_deg:.0f}° · "
        f"sets (LOS) {best.end_time.strftime('%H:%M:%S')} · lasts ~{dur_min:.0f} min (times UTC)."
    )

    st.markdown("### 📑 What each tab told us")
    st.markdown(
        f"- **Passes** — the schedule: **{len(passes)}** pass(es) to plan around.\n"
        f"- **Elevation** — the highest the satellite gets is **{best.max_elevation_deg:.0f}°** "
        "(taller peaks = better passes).\n"
        f"- **Sky View** — for the best pass, face toward the **{best_dir}**.\n"
        "- **Ground Track / Globe** — the orbit's path over Earth and how close it comes to you."
    )

    tips = {
        "Excellent": "A near-overhead pass — excellent for viewing or radio contact. Just find an open patch of sky.",
        "Good": "A high pass — good signal and easy to spot. A mostly-clear sky is enough.",
        "Fair": "A medium pass — usable, but pick a spot with a low, unobstructed horizon.",
        "Low": "A low pass — you'll need a very clear horizon (no buildings or trees) in that direction.",
    }
    st.success(f"**Viewing tip:** {tips[best_quality]}")

    _render_how_it_works()


# ---------------------------------------------------------------------------
# Main panel
# ---------------------------------------------------------------------------
if run_btn:
    if tle_line1 is None or tle_line2 is None:
        st.error("No TLE loaded. Select a local file or fetch from a live source in the sidebar.")
    else:
        with st.spinner("Running prediction..."):
            times, elevations, azimuths, ecef_series, passes = _run_prediction(
                tle_line1, tle_line2,
                lat, lon, alt_m,
                float(hours), float(threshold), float(step_sec),
            )

        sat_name = tle_name or "Satellite"

        if not passes:
            st.warning(f"No passes above {threshold}° found in the next {hours} hours.")
        else:
            st.success(f"Found **{len(passes)}** pass(es) for **{sat_name}** in the next **{hours}** hours.")

        # ----- Tabs -----
        tab_labels = ["Passes", "Elevation", "Sky View", "Ground Track"]
        if _PYDECK_AVAILABLE:
            tab_labels.append("Globe")
        tab_labels.append("📋 Summary")
        tabs = st.tabs(tab_labels)

        # shared helper for per-tab AI explanation
        def _tab_explain(tab_key: str, prompt_fn, *prompt_args):
            """Stream or show cached explanation for a tab."""
            if not (llm_enabled and _OPENAI_AVAILABLE):
                return
            from src.llm_explainer import stream_explanation
            _prompt = prompt_fn(*prompt_args)
            _ck = hash(_prompt)
            _sk = f"_expl_key_{tab_key}"
            _st = f"_expl_text_{tab_key}"
            with st.expander("🤖 AI Explanation", expanded=True):
                if st.session_state.get(_sk) != _ck:
                    try:
                        _text = st.write_stream(stream_explanation(_prompt))
                        st.session_state[_sk] = _ck
                        st.session_state[_st] = _text
                    except Exception as _exc:
                        st.error(f"AI explanation failed: {_exc}")
                else:
                    st.markdown(st.session_state[_st])

        # ---- Tab 1: Pass table ----
        with tabs[0]:
            st.subheader("Detected Passes")
            _tab_help("passes")
            if not passes:
                st.info("No passes detected with the current settings.")
            else:
                import pandas as pd
                rows = []
                for i, p in enumerate(passes, 1):
                    quality = _pass_quality(p.max_elevation_deg)
                    rows.append({
                        "#": i,
                        "AOS (UTC)": p.start_time.strftime("%Y-%m-%d %H:%M:%S"),
                        "TCA (UTC)": p.max_time.strftime("%Y-%m-%d %H:%M:%S"),
                        "LOS (UTC)": p.end_time.strftime("%Y-%m-%d %H:%M:%S"),
                        "Max El (°)": f"{p.max_elevation_deg:.1f}",
                        "Duration (s)": f"{(p.end_time - p.start_time).total_seconds():.0f}",
                        "Quality": quality,
                    })
                df = pd.DataFrame(rows)

                def _color_quality(val: str):
                    colors = {"Excellent": "#1a7a1a", "Good": "#1a3d7a", "Fair": "#7a4d00", "Low": "#7a1a1a"}
                    bg = colors.get(val, "")
                    return f"background-color: {bg}; color: white" if bg else ""

                styled = df.style.map(_color_quality, subset=["Quality"])
                st.dataframe(styled, use_container_width=True, hide_index=True)
            if llm_enabled and _OPENAI_AVAILABLE:
                from src.llm_explainer import build_explanation_prompt, stream_explanation
                _gp = build_explanation_prompt(
                    sat_name=sat_name, lat=lat, lon=lon, alt_m=alt_m,
                    hours=float(hours), threshold_deg=float(threshold),
                    passes=passes,
                )
                _gck = hash(_gp)
                with st.expander("🤖 AI Explanation", expanded=True):
                    st.caption("Powered by Groq — llama-3.1-8b-instant")
                    if st.session_state.get("_expl_key_passes") != _gck:
                        try:
                            _gt = st.write_stream(stream_explanation(_gp))
                            st.session_state["_expl_key_passes"] = _gck
                            st.session_state["_expl_text_passes"] = _gt
                        except Exception as _exc:
                            st.error(f"AI explanation failed: {_exc}")
                    else:
                        st.markdown(st.session_state["_expl_text_passes"])

        # ---- Tab 2: Elevation plot ----
        with tabs[1]:
            st.subheader("Elevation over Time")
            _tab_help("elevation")
            if times:
                fig = plot_elevation_plotly(
                    times, elevations, passes,
                    out_path="",
                    threshold_deg=float(threshold),
                    title=f"{sat_name} - Elevation",
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No data to display.")
            from src.llm_explainer import build_visual_prompt
            _tab_explain("elevation", build_visual_prompt, "elevation", sat_name, passes)

        # ---- Tab 3: Sky view ----
        with tabs[2]:
            st.subheader("Sky View (Polar)")
            _tab_help("skyview")
            if times and azimuths:
                fig = plot_sky_polar(
                    times, elevations, azimuths, passes,
                    threshold_deg=float(threshold),
                    title=f"{sat_name} - Sky View",
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No data to display.")
            from src.llm_explainer import build_visual_prompt
            _tab_explain("skyview", build_visual_prompt, "skyview", sat_name, passes)

        # ---- Tab 4: Ground track ----
        with tabs[3]:
            st.subheader("Ground Track")
            _tab_help("groundtrack")
            if ecef_series:
                fig = plot_ground_track_plotly(
                    times, ecef_series,
                    out_path="",
                    title=f"{sat_name} - Ground Track",
                    station_lat=lat,
                    station_lon=lon,
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No data to display.")
            from src.llm_explainer import build_visual_prompt
            _tab_explain("groundtrack", build_visual_prompt, "groundtrack", sat_name, passes)

        # ---- Tab 5: Globe (optional) ----
        if _PYDECK_AVAILABLE:
            with tabs[4]:
                st.subheader("3D Globe")
                _tab_help("globe")
                if ecef_series and passes:
                    from src.visualization.ground_track import ecef_to_geodetic_latlon
                    event_latlons = []
                    for p in passes:
                        for t_event in [p.start_time, p.max_time, p.end_time]:
                            idx = min(range(len(times)), key=lambda j: abs(times[j] - t_event))
                            event_latlons.append(ecef_to_geodetic_latlon(ecef_series[idx]))
                    fig = build_globe_chart(
                        ecef_series_km=ecef_series,
                        station_lat=lat,
                        station_lon=lon,
                        pass_events_latlon=event_latlons,
                    )
                    st.plotly_chart(fig, use_container_width=True)
                elif ecef_series:
                    fig = build_globe_chart(
                        ecef_series_km=ecef_series,
                        station_lat=lat,
                        station_lon=lon,
                    )
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("No data to display.")
                from src.llm_explainer import build_visual_prompt
                _tab_explain("globe", build_visual_prompt, "globe", sat_name, passes)

        # ---- Summary tab (conclusion that ties all tabs together) ----
        with tabs[-1]:
            _render_summary(sat_name, passes, times, azimuths, float(hours), float(threshold),
                            tle_age_days=_tle_age_days(tle_line1))

else:
    st.info("Configure your settings in the sidebar and click **Run Prediction** to start.")
    with st.expander("Quick reference: popular NORAD IDs"):
        st.markdown("""
        | Satellite | NORAD ID |
        |---|---|
        | ISS | 25544 |
        | AO-91 (Fox-1B) | 43017 |
        | AO-95 (Fox-1Cliff) | 43770 |
        | Hubble Space Telescope | 20580 |
        | NOAA-19 | 33591 |
        | METEOR-M 2 | 40069 |
        """)
