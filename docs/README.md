# Documentation Index

Welcome to the Satellite Pass Predictor documentation!

## Start Here

### 📖 New to this project?
**[Quick Start](QUICK_START.md)** (5 min read)
- Installation
- First prediction
- Common tasks
- Troubleshooting

### ❓ What is this project?
**[Root README](../README.md)** (comprehensive landing page)
- Overview and features
- Use cases
- Technology stack
- Limitations

## Learn More

### 🔧 How to use it?
**[Usage Guide](USAGE_GUIDE.md)** (complete reference)
- All command-line options
- Detailed examples
- Quick Reference cheat sheet
- Output formats
- Tips & tricks

### 📊 Visualization
**[Visualization Guide](VISUALIZATION_GUIDE.md)**
- Plotting options (Matplotlib, Plotly)
- Ground tracks and elevation plots
- Customization

## Deep Dive

### 🏗️ Technical Details
**[Architecture](ARCHITECTURE.md)**
- Before/after comparison
- System design
- Dependency graph
- Performance metrics

### 🧮 Mathematical Deep Dive
**[Prediction Pipeline](deep_dive/prediction_pipeline.md)**
- TLE orbital elements
- SGP4 propagation
- Coordinate transformations
- Pass detection algorithm
- ML corrections

### 🚀 What's Next?
**[Roadmap](ROADMAP.md)**
- 14 planned features
- Priority levels & timelines
- Implementation estimates
- Release schedule

## Development

### 🛠️ Contributing
**[Development Guide](DEVELOPMENT.md)**
- Setup instructions
- Testing & code style
- Pull request process

## Archive

### 📚 Legacy Content
**[Migration Guide](archive/MIGRATION.md)**
- From old versions (v1.0-v2.0)
- Command mapping
- Data compatibility

## Documentation Map

```
QUICK_START.md                    ← Start here if new
    ↓
../README.md                      ← Project overview
    ↓
USAGE_GUIDE.md                    ← Complete reference + Quick Reference
VISUALIZATION_GUIDE.md            ← Plotting options
    ↓
ARCHITECTURE.md                   ← System design
deep_dive/prediction_pipeline.md  ← Mathematical details
    ↓
ROADMAP.md                        ← Future features
DEVELOPMENT.md                    ← Contributing guide
archive/MIGRATION.md              ← Legacy version migration
```

## Quick Links

| Need | Read |
|------|------|
| Get running fast | [Quick Start](QUICK_START.md) |
| Understand project | [Root README](../README.md) |
| Command reference | [Usage Guide](USAGE_GUIDE.md) |
| Visual guides | [Visualization Guide](VISUALIZATION_GUIDE.md) |
| Technical details | [Architecture](ARCHITECTURE.md) |
| Math deep dive | [Prediction Pipeline](deep_dive/prediction_pipeline.md) |
| Feature roadmap | [Roadmap](ROADMAP.md) |
| Contributing | [Development](DEVELOPMENT.md) |
| From old version | [Migration](archive/MIGRATION.md) |

## Common Questions

**Q: How do I run this?**  
A: `python main.py --tle data/tle_leo/AO-91.txt` → See [Quick Start](QUICK_START.md)

**Q: What does this project do?**  
A: Predicts when satellites are visible → See [Root README](../README.md)

**Q: What are all the options?**  
A: See [Usage Guide](USAGE_GUIDE.md)

**Q: How does the prediction algorithm work?**  
A: See [Prediction Pipeline](deep_dive/prediction_pipeline.md)

**Q: What features are planned?**  
A: See [Roadmap](ROADMAP.md)

**Q: I used an old version, how do I migrate?**  
A: See [Migration](archive/MIGRATION.md)

---

**New here?** Start with [Quick Start](QUICK_START.md)

**Need help?** Check [Root README](../README.md) or [Usage Guide](USAGE_GUIDE.md)

**Want to contribute?** See [Improvements](IMPROVEMENTS.md)
