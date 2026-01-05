# Migration Guide - From Old Versions

If you were using v1.0, v1.1, v1.2, or v2.0, here's how to migrate.

## Quick Summary

**Old System**: Choose between 4 separate versions  
**New System**: One unified system with optional flags

## Command Mapping

### v1.0 → Unified System

**Old**:
```bash
cd v1_0_basic_pass_predictor
python src/main.py --tle data/tle.txt --lat 40 --lon -105 --alt 1600
```

**New**:
```bash
python main.py --tle data/tle.txt --lat 40 --lon -105 --alt 1600
```

**What changed**:
- No need to `cd` into version folder
- No need for `src/main.py`
- Same flags work

---

### v1.1 (Visualization) → Unified System

**Old**:
```bash
cd v1_1_visualization
python src/main.py --tle ../data/tle.txt --plots matplotlib
```

**New**:
```bash
python main.py --tle data/tle.txt --plot matplotlib
```

**What changed**:
- Flag renamed: `--plots` → `--plot`
- Values changed: `matplotlib`, `plotly`, `both` (same options)
- Easier file paths

---

### v1.2 (Analysis) → Unified System

**Old**:
```bash
cd v1_2_synthetic_deviation
python src/main.py --tle ../data/tle.txt
```

**New**:
```bash
python main.py --tle data/tle.txt --analyze-deviation
```

**What changed**:
- Add `--analyze-deviation` flag for analysis
- Otherwise same as basic prediction

---

### v2.0 (ML) → Unified System

**Old**:
```bash
cd v2_0_ai_correction
python src/main.py predict --tle ../data/tle.txt --model ../models/residual_model.pt
```

**New**:
```bash
python main.py --tle data/tle.txt --ai-correct --model models/residual_model.pt
```

**What changed**:
- No `predict` subcommand
- `--ai-correct` flag enables ML
- `--model` flag specifies model path

---

## Feature Comparison

| Feature | v1.0 | v1.1 | v1.2 | v2.0 | Unified |
|---------|------|------|------|------|---------|
| Basic prediction | ✓ | ✓ | ✓ | ✓ | ✓ |
| Visualization | ✗ | ✓ | ✗ | ✗ | ✓ (--plot) |
| Analysis | ✗ | ✗ | ✓ | ✗ | ✓ (--analyze-deviation) |
| ML correction | ✗ | ✗ | ✗ | ✓ | ✓ (--ai-correct) |
| Mix features | ✗ | ✗ | ✗ | ✗ | ✓✓✓ |

---

## Migration Examples

### Example 1: Basic User (v1.0)
**Old workflow**:
```bash
cd v1_0_basic_pass_predictor
python src/main.py --tle ../data/tle_leo/AO-91.txt
```

**New workflow**:
```bash
python main.py --tle data/tle_leo/AO-91.txt
```

**Migration effort**: None! Just change command.

---

### Example 2: Visualization User (v1.1)
**Old workflow**:
```bash
cd v1_1_visualization
python src/main.py --tle ../data/tle_leo/AO-91.txt --plots matplotlib
```

**New workflow**:
```bash
python main.py --tle data/tle_leo/AO-91.txt --plot matplotlib
```

**Migration effort**: Change `--plots` to `--plot`, update paths.

---

### Example 3: Advanced User (v2.0)
**Old workflow**:
```bash
cd v2_0_ai_correction
python src/main.py predict --tle ../data/tle_leo/AO-91.txt \
  --model ../models/residual_model.pt --hours 48
```

**New workflow**:
```bash
python main.py --tle data/tle_leo/AO-91.txt \
  --ai-correct --model models/residual_model.pt --hours 48
```

**Migration effort**: Remove `predict`, add `--ai-correct`, update paths.

---

### Example 4: Power User (All Features)
**Old**: Would need to run v1.1 THEN v2.0 separately

**New**: Run once with all flags:
```bash
python main.py --tle data/tle_leo/AO-91.txt \
  --hours 168 \
  --plot both \
  --ai-correct --model models/residual_model.pt \
  --analyze-deviation
```

**Migration benefit**: Now can mix features!

---

## Data Compatibility

### TLE Files
✓ **No changes needed**
- Same format
- Same location
- All old TLE files work

### ML Models
✓ **No changes needed**
- Same format
- Same location
- Old models work as-is

### Output Formats
✓ **Same JSON structure**
- Pass data unchanged
- Can parse old results
- JSON output format compatible

---

## Scripts & Automation

### Bash Scripts
**Old**:
```bash
#!/bin/bash
cd v1_0_basic_pass_predictor
for tle in ../data/tle_leo/*.txt; do
  python src/main.py --tle "$tle"
done
```

**New**:
```bash
#!/bin/bash
for tle in data/tle_leo/*.txt; do
  python main.py --tle "$tle"
done
```

### Python Scripts
**Old**:
```python
import sys
sys.path.insert(0, 'v1_0_basic_pass_predictor/src')
from pass_detector import detect_passes
```

**New**:
```python
from src.core import detect_passes
```

Much cleaner!

---

## Backward Compatibility

### Old Versions Still Available
✓ All old version folders (v1.0-v2.0) remain unchanged  
✓ Can continue using them if needed  
✓ Gradual migration possible

### Keeping Backups
```bash
# Archive old versions if desired
tar -czf versions-old-backup.tar.gz v1_0* v1_1* v1_2* v2_0*
mv versions-old-backup.tar.gz backups/

# Or organize them
mv v1_0* v1_1* v1_2* v2_0* versions-legacy/
```

---

## Common Migration Paths

### Path 1: Simple (v1.0 user)
1. Change command path
2. Done ✓

**Effort**: 1 minute

---

### Path 2: Visualization (v1.1 user)
1. Change command path
2. Change `--plots` to `--plot`
3. Update file paths (if needed)

**Effort**: 5 minutes

---

### Path 3: Advanced (v2.0 user)
1. Change command structure
2. Add `--ai-correct` flag
3. Update file paths
4. Test with existing models

**Effort**: 15 minutes

---

### Path 4: Full Migration
1. Delete old version folders
2. Update all automation scripts
3. Test with real data
4. Archive old code

**Effort**: 30-60 minutes

---

## Testing Your Migration

### Test 1: Basic
```bash
python main.py --tle data/tle_leo/AO-91.txt
```

### Test 2: Visualization
```bash
python main.py --tle data/tle_leo/AO-91.txt --plot matplotlib
```

### Test 3: With Model
```bash
python main.py --tle data/tle_leo/AO-91.txt --ai-correct --model models/residual_model.pt
```

### Test 4: All Features
```bash
python main.py --tle data/tle_leo/AO-91.txt --plot both --ai-correct --model models/residual_model.pt
```

If all pass, you're ready! ✓

---

## Need Help?

- [Quick Start](QUICK_START.md) - Getting started
- [Usage Guide](USAGE_GUIDE.md) - All options
- [About](ABOUT.md) - Project overview

---

**Ready to migrate?** Start with your most-used version and test!
