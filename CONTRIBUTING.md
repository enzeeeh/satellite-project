# Contributing

Thank you for your interest in improving the satellite project! This guide explains how to contribute.

---

## Before You Start

1. **Read the docs** - Familiarize yourself with the project
2. **Check existing issues** - Don't duplicate work
3. **Join discussions** - Talk about major changes first

---

## Ways to Contribute

### 1. Report Bugs
Found an issue? Help us fix it:

```bash
# Try to reproduce
python main.py --tle data/tle.txt

# Provide details
- What command did you run?
- What error did you get?
- What did you expect to happen?
- What actually happened?
- Python version, OS, etc.
```

### 2. Suggest Features
Have an idea? Share it:

- Check [IMPROVEMENTS.md](IMPROVEMENTS.md) first
- Describe the use case
- Explain why it matters
- Link to related issues

### 3. Improve Documentation
Documentation needs work:

- Fix typos and grammar
- Add examples
- Clarify confusing sections
- Translate to other languages

### 4. Write Tests
Help us catch bugs:

```bash
# See existing tests
ls tests/

# Add new tests
pytest tests/test_my_feature.py -v
```

### 5. Improve Code
Optimize, refactor, or extend:

- Fix performance issues
- Clean up code
- Add features from [IMPROVEMENTS.md](IMPROVEMENTS.md)
- Port to other languages

---

## Getting Started

### Setup Development Environment

```bash
# Clone the repository
git clone <repo-url>
cd satellite-project

# Install dependencies
pip install -r requirements-test.txt

# Install ML dependencies (optional)
pip install torch

# Verify setup
pytest tests/ -v
```

### Understand the Code

1. Read [ARCHITECTURE.md](ARCHITECTURE.md) - System design
2. Read [DEVELOPMENT.md](DEVELOPMENT.md) - How to code
3. Run the tests - See how it works
4. Run examples - See it in action

```bash
# Run basic example
python main.py --tle data/tle.txt

# Run with all features
python main.py --tle data/tle.txt --plot matplotlib --ai-correct --analyze-deviation
```

---

## Development Workflow

### 1. Create a Branch

```bash
# For a feature
git checkout -b feature/my-feature

# For a bug fix
git checkout -b fix/my-bug

# For documentation
git checkout -b docs/improve-guide
```

### 2. Make Changes

```bash
# Edit files
# Add tests if needed
# Update documentation if needed

# Run tests
pytest tests/ -v

# Check code style
# (Optional: flake8, black, mypy)
```

### 3. Commit Changes

```bash
# Add changes
git add src/

# Commit with clear message
git commit -m "Add feature: CSV export"

# Or multiple commits for clarity
git commit -m "Add CSV export function"
git commit -m "Add CSV export to CLI"
git commit -m "Add tests for CSV export"
```

### 4. Push and Create PR

```bash
# Push to your fork
git push origin feature/my-feature

# Create pull request on GitHub
# - Describe what changed
# - Reference related issues
# - Explain why change is needed
```

---

## Code Guidelines

### What Gets Merged?

✅ **YES**
- Code that follows [DEVELOPMENT.md](DEVELOPMENT.md) style guide
- Changes with tests
- Documentation updates
- Performance improvements with benchmarks
- Bug fixes with test cases

❌ **NO**
- Code without tests
- Breaking changes without discussion
- Incomplete features
- Code that duplicates existing functionality
- Changes to core physics without validation

### Code Review Checklist

Before submitting PR, make sure:

- [ ] Tests pass: `pytest tests/ -v`
- [ ] No duplicate code
- [ ] Docstrings added/updated
- [ ] Type hints added (optional but appreciated)
- [ ] No breaking changes
- [ ] Backward compatible (if possible)

---

## Types of Contributions

### 🐛 Bug Fix

Example: Fix elevation angle calculation off-by-one error

```bash
git checkout -b fix/elevation-calculation
# ... make fix ...
pytest tests/test_ground_station.py -v  # Verify fix
git commit -m "Fix elevation angle off-by-one error"
```

**Checklist**:
- [ ] Root cause identified
- [ ] Fix implemented
- [ ] Test added to prevent regression
- [ ] Existing tests still pass

### ✨ Feature

Example: Add CSV export capability

**Planning**:
1. Check [IMPROVEMENTS.md](IMPROVEMENTS.md) - Is this already planned?
2. Create issue - Discuss approach
3. Get approval - Before spending time

**Implementation**:
```bash
git checkout -b feature/csv-export

# 1. Write test first (TDD)
# 2. Implement feature
# 3. Verify tests pass
# 4. Update documentation
# 5. Commit

pytest tests/ -v
git commit -m "Add CSV export feature"
```

**Checklist**:
- [ ] Feature works as designed
- [ ] Tests written and passing
- [ ] Documentation updated
- [ ] No breaking changes
- [ ] Performance acceptable

### 📚 Documentation

Example: Improve QUICK_START guide

```bash
git checkout -b docs/improve-quick-start

# Edit docs/QUICK_START.md
# Check formatting: `# Heading`, `## Subheading`
# Test any code examples

git commit -m "Improve QUICK_START with examples"
```

**Checklist**:
- [ ] Clear and concise
- [ ] Examples actually work
- [ ] Links are correct
- [ ] Proper Markdown formatting

### ⚡ Performance

Example: Vectorize propagation loop

```bash
git checkout -b perf/vectorize-propagation

# Make changes
# Run benchmarks before/after
python -m cProfile main.py --tle data/tle.txt

git commit -m "Vectorize propagation: 5x speedup"
```

**Checklist**:
- [ ] Benchmarks show improvement
- [ ] Results still correct
- [ ] Tests pass
- [ ] Code is still readable

---

## Common Questions

### Q: How do I add a new CLI flag?
**A**: See [DEVELOPMENT.md - Adding New Features](DEVELOPMENT.md#adding-new-features)

### Q: How do I modify the neural network?
**A**: See `src/ml/model.py` and [DEVELOPMENT.md - ML](DEVELOPMENT.md)

### Q: Can I change the output format?
**A**: Discuss in an issue first - affects backward compatibility

### Q: How do I test the ML module?
**A**: See `tests/test_ml_*.py` for examples

### Q: What if my change breaks existing tests?
**A**: Either:
1. Fix the code (it's wrong)
2. Fix the test (requirements changed)
3. Add version deprecation notice

---

## Getting Help

### Documentation
- [ARCHITECTURE.md](ARCHITECTURE.md) - System design
- [DEVELOPMENT.md](DEVELOPMENT.md) - Code guidelines
- [QUICK_START.md](QUICK_START.md) - Examples
- [IMPROVEMENTS.md](IMPROVEMENTS.md) - Planned features

### Community
- Check existing issues
- Look at pull requests
- Read test files (great examples)

### Debugging
- Add print statements
- Use Python debugger: `python -m pdb main.py --tle data/tle.txt`
- Run pytest with verbose: `pytest tests/ -vv`

---

## Review Process

### What Happens After You Submit a PR?

1. **Automated checks**
   - Tests run
   - Code style checked

2. **Code review**
   - Maintainer reviews changes
   - May request modifications
   - May ask clarifying questions

3. **Feedback**
   - Positive feedback = approval
   - Requested changes = update PR
   - Disagreements = discussion in comments

4. **Merge**
   - Once approved, code is merged
   - You're credited in CHANGELOG
   - Your contribution is live!

### Response Times
- Bug fixes: Response in 1-3 days
- Features: Discussion may take a week
- Documentation: Usually quick (1-2 days)

---

## License

By contributing, you agree that your changes are licensed under the same license as the project (see LICENSE file).

---

## Recognition

Contributors are recognized in:
- Project README
- CHANGELOG
- GitHub contributors page

---

Thank you for contributing! 🎉
