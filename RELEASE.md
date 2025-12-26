# Release Guide (Simple)

This keeps releases easy and avoids clutter. Use these two things:

- CHANGELOG: [CHANGELOG.md](CHANGELOG.md)
- Steps: this file (RELEASE.md)

## How to create a release

Option A — Git tags (fastest)

```bash
# Set version and tag it
git tag -a v3.0.0 -m "v3.0.0: Unified system"

# Push the tag
git push origin v3.0.0
```

Option B — GitHub Release (optional)

- Go to GitHub → Releases → "Draft a new release"
- Tag: `v3.0.0`
- Title: "v3.0.0: Unified System"
- Description: Paste the top section from [CHANGELOG.md](CHANGELOG.md)
- Publish

That’s it. No extra files.

## What to include in a release note

- One sentence: what changed (e.g., "Unified system; use src.core imports")
- Link to migration guide: [docs/MIGRATION.md](docs/MIGRATION.md)
- Link to quick start: [docs/QUICK_START.md](docs/QUICK_START.md)

## After releasing (optional)

- Run tests once: `pytest tests -v`
- Announce: share the release link
- Collect feedback and fix if needed

## Why so simple?

- Fewer markdown files; keep only CHANGELOG.md and RELEASE.md
- Clear steps you can do in 30 seconds
- Easy for anyone to follow
