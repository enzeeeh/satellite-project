# Portfolio Notes — What This Project Demonstrates

*A short guide for anyone reviewing this repository: what it is, the data-science work inside it,
and what I learned building it.*

---

## The project in one paragraph

**Satellite Pass Predictor** is a working web app that tells you when a satellite (like the ISS)
will be visible from your location — built on real orbital physics (SGP4), live orbital data
(TLEs from CelesTrak/Space-Track), and an interactive Streamlit dashboard with five visualization
tabs plus a plain-English summary. Alongside the app, I ran a **data-science study** on the
question the app depends on: *how fast does a satellite prediction go stale?*

Two parts, one honest story:

| Part | What it is | Where |
|---|---|---|
| **The product** | SGP4 pass-prediction app: live TLE fetch → physics → pass detection → 6 tabs | [`app.py`](app.py), [`src/core/`](src/core/) |
| **The data science** | Measured how SGP4 accuracy decays as its input data ages, on real ISS data | [`notebooks/satellite_prediction_accuracy.ipynb`](notebooks/satellite_prediction_accuracy.ipynb) |

---

## The data-science study (the part I'd discuss in a DS interview)

**Question.** Satellite predictions come from a small data snapshot called a TLE. TLEs age.
How much accuracy do we lose per day — and can a model predict that error?

**Data.** I collected **180 days of real ISS orbital history** from the Space-Track API and
built **11,267 measurements** of (TLE age → prediction error), using each freshly-fitted TLE
as ground truth for older ones. Self-collected, not a Kaggle download.

**Findings (all reproducible in the notebook):**

| Finding | Number |
|---|---|
| Error when TLE is fresh (< 12 h) | **< 1 km** |
| Error at 7 days old | **~55 km** |
| Average decay rate | **~7 km per day** (linear fit) |
| Fit on the *average* trend | **R² = 0.98** — highly predictable |
| Fit on *individual* predictions | **R² = 0.08** — dominated by noise |
| Naive baseline MAE vs my model's MAE | **19.8 km vs 23.7 km — the baseline won** |

**Conclusion.** The *average* decay is beautifully linear, but *individual* errors are governed by
unpredictable space weather (and ISS engine burns) — so a naive baseline beat my model on single
predictions. The right engineering answer was therefore **not** a correction model but **refreshing
the input data** — which is exactly what the app does. The analysis directly justified a product
decision.

**The deeper experiment.** Before this, I also tested whether deep sequence models
(MLP / LSTM / Transformer) could beat the SGP4 physics model outright. Across five training runs
with a properly-constructed baseline and a do-nothing control, **no model beat the physics** —
and the study identified *why* the problem was ill-posed. I documented it as a negative result and
archived it ([`archive/`](archive/)) rather than shipping a worse model.

---

## What this demonstrates (my honest skills map)

- **Data acquisition** — pulled and processed real data from a live API (Space-Track), built a
  clean cached dataset ([`data/analysis/`](data/analysis/)).
- **Exploratory analysis** — visualized error growth, separated the predictable trend from the noise.
- **Modeling with baseline discipline** — every model was tested against a naive baseline on a
  held-out test split; when the baseline won, I said so.
- **Statistical judgment** — distinguishing "the average is predictable (R² 0.98)" from "individuals
  are not (R² 0.08)" and understanding why (unmodeled physical drivers).
- **Knowing when *not* to use ML** — the physics baseline won; I removed ML from the product
  instead of shipping a model that made predictions worse.
- **Shipping** — a deployed, documented, tested app (41 passing tests), not just a notebook.
- **Communication** — the notebook, the app's built-in explanations, and this document are written
  so a non-specialist can follow every step.

## Honest limitations

- Ground truth is the *next fitted TLE*, not independent tracking data (standard practice, but a proxy).
- One satellite (ISS) for the main study; other orbits will have different decay rates.
- The linear model is deliberately simple — the point of the study was the decision, not the model.

---

## See it yourself

```bash
pip install -r requirements.txt
streamlit run app.py          # the product  → http://localhost:8501
# then open notebooks/satellite_prediction_accuracy.ipynb for the analysis
```
