# Changelog

All notable changes to this project are documented in this file.

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
