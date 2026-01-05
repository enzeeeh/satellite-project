# Development Guide

Contribute to the satellite project. This guide explains how to extend, test, and improve the system.

---

## Quick Setup for Development

### Prerequisites
- Python 3.10+
- pip (Python package manager)
- git (optional, for version control)

### Installation

```bash
# Clone or extract the project
cd satellite-project

# Install dependencies
pip install -r requirements-test.txt

# Or install incrementally:
pip install -r requirements.txt     # Core + visualization
pip install torch                    # For ML module (optional)
pip install pytest pytest-cov       # For testing
```

### Verify Installation

```bash
# Run tests
pytest tests/ -v

# Test the main pipeline
python main.py --tle data/tle.txt --plot none --analyze-deviation

# Check coverage
pytest tests/ --cov=src --cov-report=html
```

---

## Project Structure for Developers

```
src/
├── __init__.py
├── core/           ← Physics engine (NEVER touch unless you understand orbital mechanics)
│   ├── tle_loader.py        (TLE file parsing)
│   ├── propagator.py        (SGP4 + coordinate transforms)
│   ├── ground_station.py    (Observer geometry)
│   └── pass_detector.py     (Pass detection algorithm)
│
├── visualization/  ← Plotting modules (safe to modify)
│   ├── elevation_plot.py    (matplotlib + plotly elevation)
│   └── ground_track.py      (matplotlib + plotly ground track)
│
└── ml/            ← Machine learning (experimental)
    ├── model.py             (Neural network architecture)
    ├── train.py             (Training pipeline)
    └── predict.py           (Inference/corrections)

tests/
├── test_tle_loader.py
├── test_propagator.py
├── test_ground_station.py
├── test_pass_detector.py
├── test_integration_leo.py
├── test_integration_geo.py
└── conftest.py

main.py           ← Entry point (orchestrator)
data/             ← TLE files for testing
```

---

## Code Organization Philosophy

### Core Physics (src/core/)
**Rule**: These modules compute orbital mechanics. Change only if:
- You have physics expertise
- You have test cases validating the math
- You've checked against references

**Each module is independent**:
- `tle_loader.py` → TLE parsing only
- `propagator.py` → Orbital propagation only
- `ground_station.py` → Geometry calculations only
- `pass_detector.py` → Pass finding only

### Entry Point (main.py)
**Rule**: This is the conductor. Change if:
- Adding new CLI flags
- Changing output format
- Adding new pipeline steps

**Pattern**:
```python
# 1. Parse arguments
args = parser.parse_args()

# 2. Load data
tle = load_tle(args.tle)
gs = GroundStation(args.lat, args.lon, args.elevation)

# 3. Compute core
passes = detect_passes(propagate_orbit(), gs)

# 4. Optional enhancements
if args.plot:
    plot_elevation(passes)
if args.ai_correct:
    correct_with_ml(passes)

# 5. Output
output_results(passes)
```

### Visualization (src/visualization/)
**Rule**: These modules create pretty pictures. Change if:
- Improving plot quality
- Adding new plot types
- Fixing output bugs

**Independence**: Each function is standalone. Can be called independently:
```python
from src.visualization import plot_elevation_matplotlib

plot_elevation_matplotlib(passes, gs, 'output.png')
# Works standalone, no dependencies on main.py
```

### ML (src/ml/)
**Rule**: Experimental. Change freely but:
- Test on validation set first
- Don't break existing API
- Document changes in model.py

---

## Adding New Features

### Feature 1: Export to CSV

**File to create**: `src/output/csv_export.py`

```python
# src/output/csv_export.py
import csv
from datetime import datetime

def export_passes_to_csv(passes, filepath):
    """Export passes to CSV format."""
    with open(filepath, 'w', newline='') as f:
        writer = csv.writer(f)
        
        # Header
        writer.writerow(['Satellite', 'AOS', 'TCA', 'LOS', 'Duration (min)', 'Max Elevation (°)'])
        
        # Rows
        for p in passes:
            duration = (p.los_time - p.aos_time).total_seconds() / 60
            writer.writerow([
                p.sat_name,
                p.aos_time.isoformat(),
                p.tca_time.isoformat(),
                p.los_time.isoformat(),
                f"{duration:.1f}",
                f"{p.max_elevation_deg:.2f}"
            ])
```

**Update main.py**:
```python
# Add to argument parser
parser.add_argument('--export-csv', help='Export passes to CSV file')

# Add to pipeline
if args.export_csv:
    from src.output import export_passes_to_csv
    export_passes_to_csv(passes, args.export_csv)
```

### Feature 2: Add New Pass Filter

**In src/core/pass_detector.py**:
```python
def filter_usable_passes(passes, min_elevation=10, min_duration_seconds=60):
    """Return only passes that meet minimum criteria."""
    return [
        p for p in passes
        if p.max_elevation_deg >= min_elevation
        and (p.los_time - p.aos_time).total_seconds() >= min_duration_seconds
    ]
```

**Update main.py**:
```python
parser.add_argument('--min-elevation', type=float, default=0,
                    help='Minimum elevation in degrees')
parser.add_argument('--min-duration', type=float, default=0,
                    help='Minimum pass duration in seconds')

# In pipeline
if args.min_elevation or args.min_duration:
    passes = filter_usable_passes(passes, args.min_elevation, args.min_duration)
```

### Feature 3: Add New Visualization

**Create src/visualization/sky_chart.py**:
```python
import matplotlib.pyplot as plt
import numpy as np

def plot_sky_chart(passes, gs, save_path=None):
    """Plot satellite positions on a polar coordinate sky chart."""
    fig = plt.figure(figsize=(10, 10), subplot_kw=dict(projection='polar'))
    ax = fig.add_subplot(111, projection='polar')
    
    for pass_event in passes:
        # Calculate azimuth and elevation for each moment
        times = np.linspace(pass_event.aos_time, pass_event.los_time, 100)
        azimuths = []
        elevations = []
        
        for t in times:
            # (This is pseudocode - real implementation uses propagator)
            az, el = gs.get_azimuth_elevation(sat_position, t)
            azimuths.append(np.radians(az))
            elevations.append(90 - el)  # Convert to polar radius
        
        ax.plot(azimuths, elevations, label=f'Pass {pass_event.tca_time}')
    
    ax.set_theta_zero_location('N')
    ax.set_theta_direction(-1)
    ax.set_ylim(0, 90)
    ax.set_title('Satellite Sky Chart')
    ax.legend()
    
    if save_path:
        plt.savefig(save_path, dpi=100, bbox_inches='tight')
    plt.show()
```

---

## Testing

### Running Tests

```bash
# All tests
pytest tests/

# Specific module
pytest tests/test_tle_loader.py -v

# With coverage
pytest tests/ --cov=src --cov-report=term-missing

# Specific test
pytest tests/test_pass_detector.py::test_aos_los_calculation -v
```

### Writing Tests

**Pattern**: Create test files in `tests/` matching modules

```python
# tests/test_my_feature.py
import pytest
from src.core.my_module import my_function

def test_my_function_basic():
    """Test basic functionality."""
    result = my_function(1, 2)
    assert result == 3

def test_my_function_edge_case():
    """Test edge case."""
    result = my_function(0, 0)
    assert result == 0

@pytest.mark.parametrize("input,expected", [
    (1, 1),
    (2, 4),
    (3, 9),
])
def test_my_function_parametrized(input, expected):
    """Test with multiple inputs."""
    assert my_function_squared(input) == expected
```

### Testing Physics Code

**Important**: For orbital mechanics, validate against known values

```python
# Example: Test propagator against known ephemeris
def test_propagator_known_position():
    """Verify SGP4 against published ephemeris."""
    from src.core import tle_loader, propagator
    
    tle = tle_loader.load_tle('data/AO-91.txt')
    sat = tle.satnum
    
    # Propagate to known time
    from datetime import datetime
    t = datetime(2024, 1, 1, 12, 0, 0)
    
    pos_teme = propagator.propagate_teme(tle, t)
    
    # Compare to reference ephemeris (if available)
    assert abs(pos_teme[0] - REF_X) < 1000  # Within 1 km
    assert abs(pos_teme[1] - REF_Y) < 1000
    assert abs(pos_teme[2] - REF_Z) < 1000
```

---

## Debugging

### Print Debug Info

```python
# In any module
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def some_function():
    logger.debug(f"Processing satellite at {datetime.now()}")
    logger.info(f"Found {len(passes)} passes")
```

### Run with Debug Output

```bash
# Verbose mode
python main.py --tle data/tle.txt -v

# With Python debugger
python -m pdb main.py --tle data/tle.txt
```

### Validate Intermediate Steps

```python
# In main.py, add checkpoints
tle = load_tle(args.tle)
print(f"TLE: {tle}")  # Verify TLE loaded correctly

gs = GroundStation(args.lat, args.lon, args.elevation)
print(f"Ground station ECEF: {gs.to_ecef()}")  # Verify coordinates

positions = propagate_orbit(tle, gs)
print(f"Position[0]: {positions[0]}")  # First position

passes = detect_passes(positions, gs)
print(f"Found {len(passes)} passes")  # Verify detection
```

---

## Performance Optimization

### Profiling

```python
# Add to main.py
import cProfile
import pstats

# Wrap main computation
profiler = cProfile.Profile()
profiler.enable()

passes = detect_passes(propagate_orbit(tle, gs), gs)

profiler.disable()
stats = pstats.Stats(profiler)
stats.sort_stats('cumulative')
stats.print_stats(20)  # Top 20 functions
```

### Common Bottlenecks
1. **TLE loading** - Parsing and validation (~1 ms)
2. **Propagation loop** - SGP4 calls (~0.1 ms each, ×thousands)
3. **Visualization** - File I/O (~seconds)
4. **ML inference** - Neural network forward pass (~1 ms per batch)

### Optimization Ideas
1. Vectorize propagation with NumPy (3-5× speedup)
2. Cache GMST calculations (small impact)
3. Use smaller time step only for actual pass windows (10× speedup)
4. GPU acceleration for ML (100× speedup for large batches)

---

## Code Style

### Python Style Guide (PEP 8)

```python
# Good
def calculate_elevation_angle(position, observer):
    """Calculate elevation angle in degrees."""
    return math.asin(dot_product / magnitude)

# Bad
def calc(p,o):  # Unclear names
    return math.asin(p.dot(o) / len(p))  # Poor readability
```

### Module Docstrings

```python
"""Module for TLE file loading and validation.

This module provides functions to:
- Load TLE files
- Validate TLE format
- Extract satellite information

Classes:
    TLE: Represents a Two-Line Element set

Functions:
    load_tle: Load a TLE file
    validate_tle: Validate TLE format
"""
```

### Function Docstrings

```python
def propagate_teme(tle, time):
    """Propagate satellite orbit to given time using SGP4 model.
    
    Args:
        tle (TLE): Two-Line Element object
        time (datetime): Time to propagate to
        
    Returns:
        tuple: (x, y, z) TEME position in km
        
    Raises:
        ValueError: If SGP4 propagation fails
        
    Example:
        >>> from datetime import datetime
        >>> pos = propagate_teme(tle, datetime.now())
        >>> print(f"X={pos[0]:.1f} km")
    """
```

### Type Hints (Optional, Recommended)

```python
from datetime import datetime
from typing import List, Tuple

def propagate_teme(tle: TLE, time: datetime) -> Tuple[float, float, float]:
    """Propagate satellite orbit."""
    pass

def detect_passes(positions: List[Tuple], gs: GroundStation) -> List[PassEvent]:
    """Detect passes from positions."""
    pass
```

---

## Version Control (Git)

### Commit Messages

```bash
# Good
git commit -m "Add CSV export feature"
git commit -m "Fix elevation calculation off-by-one error"

# Bad
git commit -m "fix stuff"
git commit -m "WIP"
```

### Branching Strategy

```bash
# Feature development
git checkout -b feature/csv-export
# ... make changes ...
git commit -m "Add CSV export"
git push origin feature/csv-export
# Create pull request

# Bug fixes
git checkout -b fix/elevation-bug
# ... fix ...
git commit -m "Fix elevation angle calculation"
git push origin fix/elevation-bug
```

---

## Documentation

### When to Update Docs

1. **After adding a feature**: Update [ROADMAP.md](ROADMAP.md)
2. **After changing API**: Update [USAGE_GUIDE.md](USAGE_GUIDE.md)
3. **After major refactor**: Update [ARCHITECTURE.md](ARCHITECTURE.md)
4. **New examples**: Update [QUICK_START.md](QUICK_START.md)

### Doc Format

Use Markdown with:
- Clear headings (#, ##, ###)
- Code blocks with language (```python)
- Examples with expected output
- Links to related docs

---

## Getting Help

### Understand the Physics

- [ARCHITECTURE.md](ARCHITECTURE.md) - System design
- [Orbital mechanics basics](https://en.wikipedia.org/wiki/Orbital_mechanics)
- SGP4 paper: Vallado et al. (2006)

### Debug Code Issues

1. Read the docstring
2. Check tests for examples
3. Print/log intermediate values
4. Use Python debugger (pdb)

### Ask for Help

- Check existing issues/PRs
- Review test cases for similar problems
- Compare with v1.0-v1.2 versions (versions-legacy/)

---

## Common Tasks

### Add a new CLI flag

```python
# In main.py, update argparse
parser.add_argument('--my-flag', type=str, help='What this does')
args = parser.parse_args()

# Use in pipeline
if args.my_flag:
    result = do_something(args.my_flag)
```

### Import from another module

```python
# Correct (relative to root)
from src.core import propagator
from src.visualization import elevation_plot

# In src/core/file.py (relative imports OK)
from .tle_loader import load_tle
```

### Access TLE data

```python
from src.core import tle_loader

tle = tle_loader.load_tle('data/AO-91.txt')
print(tle.satnum)     # Satellite number
print(tle.satname)    # Satellite name
print(tle.epoch)      # Epoch time
```

### Run specific test

```bash
pytest tests/test_pass_detector.py::test_aos_los_calculation -v
```

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Import errors | Ensure you're in project root. Run `python main.py` not `python src/main.py` |
| SGP4 errors | Check TLE format with `tle_loader.validate_tle()` |
| Plot not saving | Ensure output directory exists |
| Tests fail | Run `pip install -r requirements-test.txt` first |
| ML errors | Ensure torch installed: `pip install torch` |

---

**Next**: See [ROADMAP.md](ROADMAP.md) for planned features to work on
