# Archive — exploratory ML research (not part of the main project)

This folder holds an earlier machine-learning research effort that was **explored, concluded, and set
aside**. It is kept for reference and honesty — not as part of the portfolio narrative. The main
project (the **Satellite Pass Predictor** app) does not depend on anything in here and is unaffected.

## What's here

| Path | What it is | Outcome |
|---|---|---|
| `notebooks/01`–`04` + `docs/RESEARCH_PLAN.md` | Deep-learning study: *"can an LSTM/Transformer beat the SGP4 physics model?"* | **Negative result** — no model beat SGP4 (see RESEARCH_PLAN §6–§8). |
| `notebooks/05_residual_trees.ipynb` + `docs/RESEARCH_PLAN_V2.md` | A better-posed follow-up (gradient-boosted trees + space weather) that was **designed but not pursued**. | Not run. |
| `notebooks/train_residual_model.ipynb` | Training notebook for the small residual corrector behind the app's optional "ML correction" toggle. | Kept for retraining reference. |

## Why it was archived

The deep-learning study was an honest **negative result** (the physics baseline was not beaten) and far
too involved to be the focus of a beginner-to-intermediate portfolio. The project's machine-learning
story now lives in a single, self-contained, fully-explainable notebook:

➡️ **[`notebooks/satellite_prediction_accuracy.ipynb`](../notebooks/satellite_prediction_accuracy.ipynb)** —
measures how SGP4 prediction accuracy decays with data age, using real ISS data.

That notebook is the one to read and to talk about. Everything in this archive is background.
