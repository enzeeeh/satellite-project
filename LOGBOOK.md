# Project Logbook

Running journal of where the project is, what was done, and what could come next.
Newest entry first. (Release-style notes live in `CHANGELOG.md`; this file is the working journal.)

---

## 2026-07-18 → 2026-07-23 — The Big Refocus

### Where the project stands right now

| Piece | State |
|---|---|
| **App** | Pure-SGP4 pass predictor. Streamlit, 6 tabs (Passes / Elevation / Sky View / Ground Track / Globe / 📋 Summary), per-tab "what am I looking at" help, Summary tab with computed conclusion + the 5-step "how the prediction works" explainer. City dropdown for location (16 Indonesian cities + 6 world cities, **default Jakarta**) with Custom coordinates fallback. Groq AI explanations optional. **41/41 tests pass.** |
| **Data science** | One self-contained, executed notebook: [`notebooks/satellite_prediction_accuracy.ipynb`](notebooks/satellite_prediction_accuracy.ipynb) — SGP4 error vs TLE age on 180 days of real ISS data (11,267 measurements, cached in `data/analysis/`). |
| **Portfolio** | [`PORTFOLIO.md`](PORTFOLIO.md) — honest positioning doc, linked from README. |
| **Archive** | All old ML lives in [`archive/`](archive/): deep-net study NB01–04, unpursued LightGBM plan (NB05 + RESEARCH_PLAN_V2), old residual corrector (`src_ml/`, model weights, ML_MODEL.md). |
| **Run it** | `python run_streamlit.py` → <http://localhost:8501> (venv also has `pytest` + `nbconvert` installed). |
| **Git** | ⚠️ **Everything below is still uncommitted** — the whole refocus sits in the working tree. |

### What happened (in order)

1. **Closed the deep-learning study as an honest negative result.** Filled `RESEARCH_PLAN.md` §6–8
   with the real numbers: SGP4-stale baseline 6.3 km MAE flat; LSTM 12–17, Transformer 19–27,
   MLP 41–48 km; a *do-nothing* control (zero residual) ties the baseline — every trained model made
   predictions worse. Root causes were design-level (target *and* baseline were both SGP4 →
   ceiling = "tie SGP4"; geodetic-degree residuals ill-posed; >3-day cohorts had no data).
2. **Designed a corrected v2** (LightGBM + space-weather + RIC-frame targets + consecutive-TLE-pair
   ground truth) and scaffolded NB05 — then consciously **chose not to pursue it** (portfolio focus).
   Preserved in `archive/`.
3. **Reproduced NB04 and caught a reproducibility bug:** the on-disk `.npy` data/scalers (Jun 3) and
   `.pt` weights (Jun 4) were from different runs — mismatched artifacts gave LSTM ≈130 km and a
   biased do-nothing control. Also caught the ±180° longitude wrap poisoning the residual scaler
   (lon std ≈ 9°). Classic Colab download-shuffle lesson.
4. **Refocused the portfolio** (decision: explainability beats sophistication). Built the simple DS
   notebook with self-collected Space-Track data. Findings: error <1 km fresh → ~55 km at 7 days
   (~7 km/day); trend R² = 0.98 but individual R² = 0.08; **naive baseline (19.8 km MAE) beat the
   linear model (23.7 km)** → the right fix is refreshing the TLE, which is what the app does.
5. **Archived NB01–05 + research docs**; `notebooks/` now holds only the portfolio notebook.
6. **Removed ML from the app entirely** — sidebar toggle, `--ai-correct` CLI flag, wizard step,
   `src/ml/`, model weights, `torch` dependency, and every doc mention (README, FAQ, ARCHITECTURE,
   DEVELOPMENT, CONTRIBUTING, deep-dive). App is pure physics; CI workflows verified clean.
7. **App UX upgrades:** educational help box per tab; new **Summary** tab (bottom line, key metrics,
   best-pass detail, what-each-tab-told-us, viewing tip); the **"How does this prediction actually
   work?" 5-step explainer**; **city dropdown** location picker defaulting to Jakarta.
8. **Wrote `PORTFOLIO.md`** with the DS positioning and the interview story.

### Numbers worth memorising (interview crib)

- ISS prediction error: **<1 km fresh → ~55 km at 7 days** (≈ **7 km/day**).
- Average trend **R² = 0.98**; individual predictions **R² = 0.08** (space weather + ISS burns = noise).
- **Baseline beat the model:** 19.8 km vs 23.7 km MAE — reported honestly, drove the design decision.
- Deep nets never beat SGP4 (6.3 km) — best LSTM run 11.6 km at T+30.

### Open items — where we left off

- [x] **Commit everything** — done 2026-07-23, pushed to GitHub as `fb8d644` (research/archive),
      `0c495be` (app rework), `f0fca9e` (notebook + portfolio + logbook).
- [ ] README screenshots (`docs/images/`) predate the new sidebar + Summary tab → retake.
- [ ] App currently running locally on :8501 (kill with Task Manager / `taskkill //IM streamlit.exe`).

---

## Future ideas (upgrade / fix / explore)

### ⭐ Recommended next feature — "TLE freshness meter"
Show the loaded TLE's age in the app and translate it using *our own study*:
`"Your TLE is 2.3 days old → expect roughly ±17 km position error (see the analysis notebook)."`
One small UI element that **turns the notebook's finding into a product feature** — the perfect
portfolio story (analysis → decision → feature) and only a few lines of code.

### Quick wins
- Deploy to **Streamlit Community Cloud** (free) → live demo link in README + resume.
- Retake README screenshots (sidebar + Summary tab changed).
- Switch `main.py` CLI defaults from USA coordinates to Jakarta (app is done; CLI still USA).
- Delete the stray empty `src/analysis/` folder.

### Product upgrades (still simple + explainable)
- **Local-time display (WIB)** — all times are UTC today; a timezone selector would be a big
  usability win for Indonesian users.
- **Export passes to calendar (.ics)** — "add the best pass to Google Calendar."
- **TLE caching** — skip re-fetching if the cached TLE is < a few hours old.
- **Multi-satellite compare** — pick 2–3 satellites, merge their pass schedules.

### Data-science extensions (optional; keep them scoped)
- **Decay rate vs altitude:** repeat the accuracy study for 3–4 satellites at different altitudes
  (e.g. ISS ~420 km vs NOAA-19 ~870 km) — same method, one new chart, richer conclusion.
- **Explain the noise:** join daily space-weather indices (F10.7 / Ap from CelesTrak, free CSV) onto
  the error data and test whether they explain the residual scatter (the R² = 0.08). This upgrades
  the story from "individuals are noise" to "here's *what* the noise is."
- **Write it up:** the negative-result story ("I tested ML against physics; physics won") as a blog
  or LinkedIn post — great visibility for a DS profile.

### Hygiene
- Add small unit tests for the new helpers (`_compass`, summary logic).
- Pin dependency versions in `requirements.txt` before deploying.
- Confirm CI is green after the big commit (workflows already verified free of ML references).

---

*Earlier history (v1.0 → v3.0 consolidation, ML training runs 1–5) is recorded in `CHANGELOG.md`.*
