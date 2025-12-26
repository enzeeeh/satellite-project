# Legacy Versions

This folder contains the original 4-version system (v1.0-v2.0). These versions are **no longer maintained**.

## Migration Guide

The project has been refactored into a **single unified system** with optional features. If you were using one of these versions, see the migration guide:

→ [Migrate to Unified System](../docs/MIGRATION.md)

## What's Here

```
v1_0_basic_pass_predictor/    ← Basic pass prediction only
v1_1_visualization/           ← Pass prediction + plots
v1_2_synthetic_deviation/     ← Adds TLE accuracy analysis
v2_0_ai_correction/           ← Adds machine learning corrections
```

## Why These Are Legacy

- **90% code duplication** across versions
- **No longer updated** - bugs fixed only in unified system
- **Confusing to maintain** - changes needed in 4 places
- **Hard to combine features** - want both visualization and ML? Use separate tools

## Use Cases for Legacy Code

### Learning
If you want to understand how the system evolved:
1. Start with v1_0 (simplest)
2. See how v1_1 adds visualization
3. Understand v1_2's analysis
4. Learn v2_0's ML integration

### Reference
If you need specific functionality from an old version, you can reference the code here, but **please migrate to the unified system** for:
- Bug fixes
- Performance improvements
- New features
- Community support

## The Better Way

Use the **unified system** in `src/` and `main.py`:

```bash
# Basic prediction
python main.py --tle data/tle.txt

# With visualization
python main.py --tle data/tle.txt --plot matplotlib

# With ML correction
python main.py --tle data/tle.txt --ai-correct --model models/residual_model.pt

# With analysis
python main.py --tle data/tle.txt --analyze-deviation

# All together
python main.py --tle data/tle.txt --plot plotly --ai-correct --model models/residual_model.pt --analyze-deviation
```

See [Quick Start](../docs/QUICK_START.md) for more examples.

---

**Status**: ⚠️ Archived - Do not use for new projects
