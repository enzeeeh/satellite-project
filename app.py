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
# Sidebar: inputs
# ---------------------------------------------------------------------------
with st.sidebar:
    st.header("Observer Location")
    st.caption("Enter where you are on Earth. The app uses this to compute which satellite passes are visible from your exact spot.")
    lat = st.number_input("Latitude (deg)", min_value=-90.0, max_value=90.0, value=40.0, step=0.1, format="%.4f")
    lon = st.number_input("Longitude (deg)", min_value=-180.0, max_value=180.0, value=-105.0, step=0.1, format="%.4f")
    alt_m = st.number_input("Altitude (m)", min_value=0.0, max_value=8848.0, value=1600.0, step=10.0)

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

    st.divider()
    st.header("Prediction Window")
    st.caption("Control how far ahead to scan, the minimum elevation a pass must reach to count, and how finely to sample the orbit (smaller step = more accurate but slower).")
    hours = st.slider("Hours ahead", min_value=1, max_value=168, value=48, step=1)
    threshold = st.slider("Min elevation (deg)", min_value=0, max_value=89, value=10, step=1)
    step_sec = st.select_slider("Time step (sec)", options=[10, 15, 30, 60, 120], value=30)

    st.divider()
    st.header("ML Correction")
    st.caption("Optionally apply a neural-network model to reduce small timing errors in the standard SGP4 orbit calculation.")
    _default_model = Path("models/residual_model.pt")
    _model_found = _default_model.exists()
    ml_enabled = st.toggle(
        "Apply SGP4 residual correction",
        value=False,
        disabled=not _model_found,
        help="Uses a trained neural network to reduce SGP4 along-track drift. "
             "Requires models/residual_model.pt.",
    )
    if not _model_found:
        st.caption("No model found at `models/residual_model.pt`. Train via the notebook first.")
    elif ml_enabled:
        st.caption(f"Model loaded: `{_default_model}`")

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
    ml_model_path: str = None,
) -> Tuple[List[datetime], List[float], List[float], List[Tuple], List[PassEvent], bool]:
    """Propagate satellite and detect passes. Returns parallel lists + ml_applied flag."""
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

    # -- Optional ML residual correction ------------------------------------
    ml_applied = False
    if ml_model_path and times:
        try:
            from src.ml.predict import ResidualCorrector, apply_correction_to_position, features_from_satrec

            corrector = ResidualCorrector(model_path=ml_model_path)
            epoch_dt  = sat.epoch  # sgp4 Satrec stores epoch as Python datetime via jday

            corrected_ecef, corrected_elev = [], []
            for dt, pos_ecef in zip(times, ecef_series):
                tse_h = (dt - start).total_seconds() / 3600.0  # approx hours since start
                state = propagate_teme(sat, dt)
                v_ecef = teme_to_ecef(state.v_km_s, gmst_angle(dt))
                residual_km = corrector.predict_from_satrec(sat, tse_h)
                pos_corr = apply_correction_to_position(pos_ecef, v_ecef, residual_km)
                corrected_ecef.append(pos_corr)
                corrected_elev.append(station.elevation_azimuth_deg(pos_corr)[0])

            ecef_series = corrected_ecef
            elevations  = corrected_elev
            ml_applied  = True
        except Exception as _exc:
            pass  # fall back to uncorrected predictions silently

    passes = detect_passes(times, elevations, threshold_deg)
    return times, elevations, azimuths, ecef_series, passes, ml_applied


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
# Main panel
# ---------------------------------------------------------------------------
if run_btn:
    if tle_line1 is None or tle_line2 is None:
        st.error("No TLE loaded. Select a local file or fetch from a live source in the sidebar.")
    else:
        with st.spinner("Running prediction..."):
            times, elevations, azimuths, ecef_series, passes, ml_applied = _run_prediction(
                tle_line1, tle_line2,
                lat, lon, alt_m,
                float(hours), float(threshold), float(step_sec),
                ml_model_path=str(_default_model) if ml_enabled else None,
            )

        sat_name = tle_name or "Satellite"
        if ml_applied:
            st.info("ML residual correction applied to all position samples.")

        if not passes:
            st.warning(f"No passes above {threshold}° found in the next {hours} hours.")
        else:
            st.success(f"Found **{len(passes)}** pass(es) for **{sat_name}** in the next **{hours}** hours.")

        # ----- Tabs -----
        tab_labels = ["Passes", "Elevation", "Sky View", "Ground Track"]
        if _PYDECK_AVAILABLE:
            tab_labels.append("Globe")
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
            st.caption(
                "Lists every predicted pass sorted by time. "
                "Use it to plan when to point your antenna or open your radio app. "
                "Green = Excellent (≥60°), Blue = Good, Amber = Fair, Red = Low quality."
            )
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
                    passes=passes, ml_applied=ml_applied,
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
            st.caption(
                "Shows how high the satellite appears in your sky over time. "
                "Higher elevation = stronger signal. "
                "The shaded bands mark each visible pass window above your minimum threshold."
            )
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
            st.caption(
                "Top-down view of your sky. Centre = directly overhead (90°), outer ring = horizon (0°). "
                "Each arc shows the satellite's path through your sky during a pass — "
                "use the compass angle to know which direction to face."
            )
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
            st.caption(
                "Shows the satellite's path projected onto Earth's surface. "
                "The marker is your ground station. "
                "Use this to see whether the satellite is approaching or moving away from your location."
            )
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
                st.caption(
                    "Interactive 3D view of the satellite's ground track. "
                    "Drag to rotate, scroll to zoom. "
                    "Yellow = your station · Green = AOS · Orange = TCA (closest approach) · Red = LOS."
                )
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
