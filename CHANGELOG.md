# Changelog

All notable changes to this project are documented in this file.

---

## ML Training Run Log

Tracks every Colab training run for the ML residual-correction models.  
All MAE figures are on the held-out **test set** (last 15% by time, ~31k windows).

### Run 4 — Planned (STALE_DAYS = 7)

**Status:** Not yet executed

#### What changed
| Component | Change | Reason |
|---|---|---|
| `NB01` — Config cell | `STALE_DAYS: 3 → 7` | At 3 days, SGP4 error is only ~2–6 km (near-noise). At 7 days, LEO drift grows to ~15–50 km — large enough for ML to learn a meaningful correction. |

#### How to run
1. Open `notebooks/01_data_exploration.ipynb` on Colab (GPU not needed for NB01).
2. Run all cells → regenerates `positions_*.csv` with `sgp4_stale_age ≥ 7 days` → download `collected_positions.zip`.
3. Run `notebooks/02_feature_engineering.ipynb` (upload new zip) → download `dataset.zip`.
4. Run `notebooks/03_model_training.ipynb` (upload dataset zip, **enable T4 GPU**) → download `.pt` files.
5. Copy `.pt` files to `data/collected/`, then run `notebooks/04_evaluation.ipynb` locally.

#### Expected improvement
- SGP4 stale baseline MAE will be ~15–50 km (was 2–6 km).
- Residuals are large and structured → LSTM/Transformer should beat the baseline.
- Target: corrected MAE < 10 km at T+60 min.

---

### Run 3 — Completed 2026-06-03 (LSTM hidden_dropout + weight_decay fix)

**Commit:** `be2363e`

#### What changed
| Component | Change | Reason |
|---|---|---|
| `NB03` — `LSTMOrbit` | Added explicit `self.hidden_dropout = nn.Dropout(dropout)` on concatenated hidden states | PyTorch disables internal LSTM dropout when `lstm_layers=1` → no regularisation → overfit instantly |
| `NB03` — `train_model` | `weight_decay: 1e-4 → 1e-3` | Stronger L2 regularisation |
| `NB03` — `train_model` | `best_state = deepcopy(model.state_dict())` initialised before loop | Was `None` → `TypeError` crash if no epoch improved val loss |

#### Training results (3rd Colab run)
| Model | Best Val Loss | Stopped at Epoch |
|---|---|---|
| MLP | 0.1507 | 27 (early stop) |
| LSTM | 0.1349 | 65 (early stop) |
| Transformer | 0.1334 | 70 (early stop) |

#### Evaluation results — MAE (km)
| Model | T+10 | T+30 | T+60 | T+120 |
|---|---|---|---|---|
| SGP4 stale (3-day) | **6.3** | **6.3** | **6.3** | **6.3** |
| LSTM | 11.8 | 11.6 | 16.8 | 14.5 |
| Transformer | 19.5 | 26.7 | 26.8 | 24.7 |
| MLP | 41.2 | 43.9 | 46.2 | 48.3 |

#### Root-cause analysis
LSTM improved massively (was 115 km, now 11–16 km) but all models still worse than SGP4.  
Root cause: `STALE_DAYS=3` → stale baseline only 3 days old → SGP4 errors are 2–6 km (mostly noise). ML has no meaningful residual to learn. Fix scheduled for Run 4.

**TLE-age breakdown at T+60 min:**
| TLE Age | LSTM | SGP4 stale |
|---|---|---|
| < 1 day | 17.0 km | 6.4 km |
| 1–3 days | 7.0 km | 2.9 km |
| 3–7 days | — (no data) | — |
| > 7 days | — (no data) | — |

---

### Run 2 — Completed ~2026-06-02 (NaN filter + residual learning)

#### What changed
- Switched NB03 from absolute-position targets to residual targets (`y_true − y_SGP4_stale`).
- Added `valid_mask()` NaN filter in NB02 for windows without a stale baseline.
- `train_model`: `weight_decay = 1e-4` (too low), `best_state = None` (bug).

#### Evaluation results — MAE at T+60 min
| Model | MAE |
|---|---|
| SGP4 stale | 6.3 km |
| LSTM | 115 km ← broken (best val at epoch 1, zero hidden_dropout) |
| MLP | ~37 km |
| Transformer | 9–21 km |

---

### Run 1 — Crashed ~2026-06-01 (NaN loss)

**Error:** `TypeError: Expected state_dict to be dict-like, got NoneType`  
**Cause:** Rows with no stale baseline had NaN residuals → NaN loss → `best_state` never set → crash.  
**Fix applied in Run 2:** `valid_mask()` NaN filter + `best_state = deepcopy(model.state_dict())` initialisation.

---

## [3.0.0] - December 26, 2025

### 🎉 Major Changes

#### Unified System Architecture
- **BREAKING**: Consolidated 4 separate versions (v1.0-v2.0) into a single unified system
- Single entry point ([main.py](main.py)) with feature flags instead of choosing between 4 folders
- Eliminated 90% code duplication through modular design

#### Import Path Migration
- **BREAKING**: Changed from `from satcore import ...` to `from src.core import ...`
- All tests, examples, and scripts updated to use new unified package
- Old `satcore/` package still available for backward compatibility (will be removed in v4.0)

#### New Modular Structure
- `src/core/` - Physics engine (always used)
- `src/visualization/` - Optional matplotlib/plotly plotting
- `src/ml/` - Optional PyTorch ML corrections

#### Documentation Reorganization
- Created comprehensive `/docs` folder with 9 guides
- Clear information hierarchy: quick start → detailed guides → reference
- Added contribution guidelines ([CONTRIBUTING.md](CONTRIBUTING.md))
- Added development guide ([docs/DEVELOPMENT.md](docs/DEVELOPMENT.md))
- All legacy version documentation archived in `versions-legacy/`

### ✨ New Features

- **Unified Entry Point**: Single `main.py` replaces 4 version-specific scripts
- **Feature Flags**:
  - `--plot {none|matplotlib|plotly|both}` - Visualization control
  - `--ai-correct --model PATH` - ML residual corrections
  - `--analyze-deviation` - TLE accuracy analysis
- **Better CLI**: Consistent argument parsing across all operations
- **Optional ML**: PyTorch no longer required for core functionality (torch import lazily loaded)

### 🔄 Migration Guide

#### For Users of v1.0-v1.2

**Old way (v1.0 basic)**:
```bash
cd v1_0_basic_pass_predictor
python src/main.py
```

**New way**:
```bash
python main.py --tle data/tle.txt
```

**Old way (v1.1 with plots)**:
```bash
cd v1_1_visualization
python src/main.py
```

**New way**:
```bash
python main.py --tle data/tle.txt --plot matplotlib
```

**Old way (v2.0 with ML)**:
```bash
cd v2_0_ai_correction
python src/main.py
```

**New way**:
```bash
python main.py --tle data/tle.txt --ai-correct --model models/residual_model.pt
```

#### For Developers

**Old imports**:
```python
from satcore import load_tle, GroundStation, detect_passes, propagate_satellite
```

**New imports**:
```python
from src.core import load_tle, GroundStation, detect_passes, propagate_satellite
```

See [docs/MIGRATION.md](docs/MIGRATION.md) for detailed migration steps.

### 📊 Code Quality

- **Duplication**: 90% → 0% (from 2,850 lines to 400 lines)
- **Test Coverage**: 41 tests, all passing ✅
- **Python Support**: 3.10, 3.11, 3.12
- **Build Time**: No change (tests still < 1 second)

### 🗂️ Project Structure

**Before**:
```
v1_0_basic_pass_predictor/
v1_1_visualization/
v1_2_synthetic_deviation/
v2_0_ai_correction/
satcore/
docs/ (mixed content)
(9+ root-level docs)
```

**After**:
```
src/core/          (unified physics)
src/visualization/ (optional plots)
src/ml/            (optional ML)
docs/              (organized guides)
versions-legacy/   (archived old versions)
main.py            (single entry point)
```

### 📝 Documentation

**New docs in `/docs`**:
- `README.md` - Documentation index
- `ABOUT.md` - Project overview
- `QUICK_START.md` - 5-minute tutorial
- `USAGE_GUIDE.md` - Complete command reference
- `QUICK_REFERENCE.md` - Cheat sheet
- `ARCHITECTURE.md` - Technical details
- `DEVELOPMENT.md` - Developer guide
- `IMPROVEMENTS.md` - Future roadmap
- `MIGRATION.md` - Upgrading from v1/v2

**New project files**:
- [CONTRIBUTING.md](CONTRIBUTING.md) - Contribution guidelines
- [REORGANIZATION_COMPLETE.md](REORGANIZATION_COMPLETE.md) - Refactoring details
- [FINAL_STATUS.md](FINAL_STATUS.md) - Project status report

### 🔧 Configuration Changes

**CI/CD**: Updated GitHub Actions workflow to use `src` for coverage reporting

**Package**: Removed eager torch import to keep tests fast (ml module loaded on-demand)

### ⚠️ Deprecations

- `satcore/` package - Use `src.core` instead (will be removed in v4.0)
- Old import paths `from satcore import ...` - Use `from src.core import ...` (will be removed in v4.0)
- v1.0-v1.2 folders - Moved to `versions-legacy/` for reference

### 🚀 Performance

- **No regression**: Same execution speed
- **Smaller footprint**: Single codebase instead of 4
- **Faster development**: Changes in one place

### 🔍 Testing

```bash
# Run all tests
pytest tests -v

# Run specific test file
pytest tests/test_pass_detector.py -v

# Run with coverage
pytest tests --cov=src --cov-report=html
```

**Result**: ✅ 41 tests passing (0.89s)

### 🎯 Next Steps

1. ✅ Unified system working
2. ✅ Tests passing
3. ✅ Documentation complete
4. ⏳ Deprecate satcore/ in v4.0
5. ⏳ Consider feature additions (see [docs/IMPROVEMENTS.md](docs/IMPROVEMENTS.md))

### 📚 Resources

- **Quick Start**: [docs/QUICK_START.md](docs/QUICK_START.md)
- **Migration Guide**: [docs/MIGRATION.md](docs/MIGRATION.md)
- **Development**: [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md)
- **Architecture**: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)
- **Contributing**: [CONTRIBUTING.md](CONTRIBUTING.md)

---

## [2.0.0] - Previous Release

See `versions-legacy/v2_0_ai_correction/` for archived v2.0 code.

## [1.2.0] - Previous Release

See `versions-legacy/v1_2_synthetic_deviation/` for archived v1.2 code.

## [1.1.0] - Previous Release

See `versions-legacy/v1_1_visualization/` for archived v1.1 code.

## [1.0.0] - Previous Release

See `versions-legacy/v1_0_basic_pass_predictor/` for archived v1.0 code.
