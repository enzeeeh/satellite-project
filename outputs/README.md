# 📁 Current Outputs Folder

## Latest Run (2025-12-26 08:25 UTC)

### Files
```
outputs/
├── elevation_mpl_20251226T082503Z.png      (168 KB)
├── ground_track_mpl_20251226T082503Z.png   (212 KB)
└── passes_20251226T082426Z.json            (1.4 KB)
```

### Run Configuration
- **Satellite:** AO-91 (LEO amateur radio satellite)
- **TLE Source:** `data/tle_leo/AO-91.txt`
- **Prediction Window:** 12 hours (08:24 - 20:24 UTC)
- **Ground Station:** 40.0°N, 105.0°W, 1600m (Boulder, CO)
- **Visibility Threshold:** 10° elevation
- **Visualization:** Matplotlib

### Pass Results

**3 passes detected:**

| Pass | Time (UTC) | Duration | Max Elevation | Quality |
|------|-----------|----------|---------------|---------|
| 1 | 08:47 - 08:51 | 3.6 min | 12.6° | Low (near threshold) |
| 2 | 17:46 - 17:50 | 4.1 min | 15.8° | Moderate |
| 3 | 19:18 - 19:23 | 5.2 min | **22.2°** | **Good (best)** |

### Understanding the Images

See [VISUALIZATION_GUIDE.md](../docs/VISUALIZATION_GUIDE.md) for detailed explanations of:
- What each plot shows
- How to interpret ground track and elevation
- Physical meaning of the visualizations
- Practical applications

---

**Note:** Old outputs from previous runs have been cleaned up. Only the latest run is kept for reference.
