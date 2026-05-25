# Documentation

## Guides

- [Architecture](ARCHITECTURE.md) — Module layout, data flow, system design
- [Prediction Pipeline](deep_dive/prediction_pipeline.md) — SGP4 math, coordinate transforms, ML corrections
- [FAQ](FAQ.md) — Physics, data sources, ML, and testing questions
- [Development Guide](DEVELOPMENT.md) — Contributing, running tests, code style
- [Roadmap](ROADMAP.md) — Planned features and priorities

## Starting Point

For a general overview, installation steps, and how to run the dashboard, see the [root README](../README.md).


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
