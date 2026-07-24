# Data-Science Concepts — a plain-English refresher

*A study note for this project. It explains the core ideas (in plain words) and maps them to the
data-science work in [`notebooks/satellite_prediction_accuracy.ipynb`](../notebooks/satellite_prediction_accuracy.ipynb).
Written to be re-read before interviews.*

---

## 1. What machine learning actually is

- **Normal programming:** *you* write the rule. → `if elevation > 10°: it's a pass`.
- **Machine learning:** you show the computer many **examples with known answers**, and *it* works
  out the rule. Then it predicts on new, unseen data.

That's the whole idea: **learn a pattern from examples**, then use it to predict.

## 2. Supervised vs Unsupervised

The question: **do your training examples come with the answer attached?**

| | Examples have answers? | The model… | Example |
|---|---|---|---|
| **Supervised** | Yes (called *labels*) | learns input → answer | age → error |
| **Unsupervised** | No | finds hidden groups/structure | "sort customers into 3 types" |

➡️ **This project is supervised** — each row was *(TLE age → the real error)*: age is the input,
the measured error is the known answer.

## 3. Two kinds of supervised learning (the key distinction)

Supervised learning splits by **what you predict**:

| | You predict… | Scored with… | Example |
|---|---|---|---|
| **Classification** | a **category / label** | **accuracy %** | "spam / not spam" |
| **Regression** | a **number** | **error (MAE/RMSE) + R²** | "price = $340k" |

➡️ This project predicted a **number** (error in km) → it is **regression** → **that is why there is
no "95% accuracy."** *Accuracy* is a classification word; it does not exist in regression. Nothing
was missing — the two types just use different scoreboards.

## 4. The metrics, in plain words

- **Accuracy** (classification): out of 100 guesses, how many were right.
- **MAE** (regression): *"on average, how many units was I off?"*
  This project's model MAE ≈ **23.7 km** = "our guess of the error was, on average, ~24 km from the truth."
- **RMSE** (regression): like MAE, but punishes big misses harder.
- **R²** (regression): *"of all the ups and downs in the real answers, what fraction did the model
  explain?"*

| R² | Meaning |
|---|---|
| 1.0 | explained everything (perfect) |
| 0.98 | explained 98% (excellent) |
| 0.08 | explained 8% (almost nothing) |
| 0.0 | no better than always guessing the average |
| negative | *worse* than guessing the average |

This project's two R² values:
- **Trend R² = 0.98** → the *average* error at each TLE age is highly predictable.
- **Individual R² = 0.08** → any *single* prediction's error is almost unpredictable (it's noise,
  driven by space weather and satellite maneuvers).

That contrast **is** the finding — both numbers are true, they just answer different questions.

## 5. What a "baseline" is (and why it matters)

A **baseline** = the dumbest reasonable guess, kept as a yardstick.
- This project's baseline: *"always just guess the average error"* — no model, no cleverness.
- **Rule of the field:** a model is only worth something if it **beats the baseline.**
- Here the model's MAE (23.7 km) was **worse** than the baseline's (19.8 km) → the dumb guess won →
  the model added nothing for individual predictions. Reporting that honestly is a mature move.

> **Always compare a model to a baseline.** A model with no baseline is an unverified claim.

## 6. Overfitting & the train/test split (why we hold data back)

- We **train** the model on part of the data and **test** it on data it has never seen (here: 80% / 20%).
- If a model looks great on training data but bad on test data, it **overfit** — it memorized noise
  instead of learning the real pattern. The test set is how you catch that.

## 7. This project, mapped to every idea above

| Question | Answer |
|---|---|
| Supervised or unsupervised? | **Supervised** (examples had known answers) |
| Classification or regression? | **Regression** (predicted a number: error in km) |
| Model used | **Linear regression** (a simple supervised model) |
| Baseline | "always guess the average error" |
| Metrics | **MAE** (~24 km) and **R²** (0.98 trend / 0.08 individual) |
| Why no "95% accuracy"? | Accuracy is only for classification; regression uses error + R² |
| The finding | Average is predictable; individuals are noise; **baseline beat the model** |

## 8. The trick that changes the "scoreboard"

Change the **question** from a number to a yes/no —

> *"Will the error be more than 10 km — is this data too old to trust?"* (**yes / no**)

— and the same data becomes a **classification** problem, which **does** give an **accuracy %**
(because you're now predicting a category, not a number). Same data, different question, different
metric.

---

## Mini-glossary

- **Feature** — an input column the model uses (e.g. TLE age).
- **Label / target** — the answer you're predicting (e.g. the error).
- **Model** — the thing that maps features → prediction (e.g. linear regression).
- **Baseline** — the naive comparison a model must beat.
- **MAE** — mean absolute error; average size of the miss, in the target's units.
- **R²** — fraction of the variation the model explains (0 = none, 1 = all).
- **Overfitting** — great on training data, poor on new data.
- **Train/test split** — hold out unseen data to check the model honestly.
