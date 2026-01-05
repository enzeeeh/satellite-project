# Project Roadmap

Future development plans for the Satellite Pass Predictor, organized by priority and implementation timeline.

## Vision

Transform the satellite pass predictor into a comprehensive, user-friendly orbital mechanics platform suitable for amateur radio operators, astronomers, educators, and mission planners.

## Release Timeline

### v2.1 - Usability Improvements (Q1 2026)
**Focus**: Make the tool easier to use for recurring workflows

**Features**:
- Config file support (YAML/JSON)
- Batch processing for multiple satellites
- Enhanced pass filtering options
- JSON output by default

**Estimated Development**: 2-3 weeks

---

### v2.2 - Data Export & Integration (Q2 2026)
**Focus**: Enable integration with external tools and workflows

**Features**:
- CSV export for spreadsheets
- ICS (iCalendar) export for calendar apps
- Better error handling with helpful suggestions
- Station location presets

**Estimated Development**: 2-3 weeks

---

### v2.3 - Advanced Analysis (Q3 2026)
**Focus**: Add scientific capabilities and real-time features

**Features**:
- Uncertainty quantification
- Real-time pass monitoring with alerts
- TLE auto-update from CelesTrak
- KML export for Google Earth

**Estimated Development**: 3-4 weeks

---

### v3.0 - Web Platform (Q4 2026)
**Focus**: Create accessible web interface

**Features**:
- REST API (FastAPI/Flask)
- Simple web UI for predictions
- Multi-user support
- Cloud TLE management

**Estimated Development**: 6-8 weeks

---

## Feature Details

### Priority 1: Quick Wins (High Impact, Low Effort)

#### 1. Config File Support ⭐⭐⭐⭐⭐
**Status**: Not Started | **Effort**: 30 min | **Impact**: High

**Description**: Load default parameters from YAML/JSON configuration files to eliminate repetitive command-line arguments.

**Example**:
```yaml
# config.yaml
ground_station:
  latitude: 40.0
  longitude: -105.0
  altitude: 1600
  name: "Boulder, CO"

prediction:
  hours: 48
  threshold: 10
  step: 30

output:
  format: json
  plot: matplotlib
  directory: outputs
```

**Usage**:
```bash
python main.py --tle data/tle_leo/AO-91.txt --config config.yaml
```

**Benefits**:
- Eliminates flag fatigue for recurring predictions
- Easy location presets (home, work, observatory)
- Team collaboration (share configs)
- Foundation for batch processing

**Implementation Notes**:
- Use PyYAML for parsing
- Command-line args override config values
- Validate schema on load

---

#### 2. Batch Processing ⭐⭐⭐⭐
**Status**: Not Started | **Effort**: 20 min | **Impact**: High

**Description**: Process multiple TLE files simultaneously with organized output directories.

**Usage**:
```bash
python main.py --tle-dir data/tle_leo/ --plot matplotlib --batch
```

**Output Structure**:
```
outputs/
├── AO-91/
│   ├── passes.json
│   ├── elevation_mpl.png
│   └── ground_track_mpl.png
├── AO-95/
│   ├── passes.json
│   ├── elevation_mpl.png
│   └── ground_track_mpl.png
```

**Benefits**:
- Track entire satellite constellations
- Compare orbital patterns
- Automated surveys

**Implementation Notes**:
- Use glob patterns for file discovery
- Parallel processing with multiprocessing
- Aggregate summary report

---

#### 3. Enhanced Pass Filtering ⭐⭐⭐⭐
**Status**: Partially Implemented | **Effort**: 45 min | **Impact**: High

**Description**: Add advanced filtering options beyond basic elevation threshold.

**New Filters**:
```bash
# Only high-quality passes
python main.py --tle data/tle.txt --min-elevation 45 --min-duration 5

# Future passes only (exclude past)
python main.py --tle data/tle.txt --future-only

# Daytime passes only
python main.py --tle data/tle.txt --daytime-only

# Night passes only
python main.py --tle data/tle.txt --nighttime-only

# Specific time-of-day window
python main.py --tle data/tle.txt --time-window "18:00-22:00"
```

**Benefits**:
- "Show me good passes" is the #1 user request
- Reduce clutter in output
- Mission-specific planning

**Implementation Notes**:
- Add solar position calculation for day/night filtering
- Time window parsing with dateutil
- Duration calculation already available

---

#### 4. JSON Output by Default ⭐⭐⭐⭐
**Status**: Not Started | **Effort**: 15 min | **Impact**: High

**Description**: Always generate JSON output (currently requires `--json-output` flag).

**Benefits**:
- Machine-readable by default
- Enables automation and scripting
- Consistent output format
- Foundation for API development

**Implementation Notes**:
- Keep console output for human readability
- JSON file always written to outputs/
- No breaking changes (just remove flag requirement)

---

### Priority 2: Integration Features (Medium Effort)

#### 5. CSV Export ⭐⭐⭐
**Status**: Not Started | **Effort**: 1 hour | **Impact**: High

**Description**: Export pass predictions as CSV for spreadsheet analysis.

**Usage**:
```bash
python main.py --tle data/tle.txt --format csv --output passes.csv
```

**Output**:
```csv
satellite,aos_time,tca_time,los_time,max_elevation_deg,duration_min,azimuth_aos,azimuth_los
AO-91,2025-12-26T12:30:00Z,2025-12-26T12:35:00Z,2025-12-26T12:40:00Z,45.2,10.0,45,315
AO-95,2025-12-26T15:20:00Z,2025-12-26T15:28:00Z,2025-12-26T15:36:00Z,78.5,16.0,90,270
```

**Benefits**:
- Import to Excel, Google Sheets
- Database ingestion
- Statistical analysis
- Report generation

**Implementation Notes**:
- Use Python csv module
- Include all pass metadata
- Optional: add azimuth/range columns

---

#### 6. ICS (iCalendar) Export ⭐⭐⭐
**Status**: Not Started | **Effort**: 2 hours | **Impact**: Medium

**Description**: Generate calendar events for satellite passes.

**Usage**:
```bash
python main.py --tle data/tle.txt --format ics --output passes.ics
```

**Event Structure**:
```
BEGIN:VEVENT
SUMMARY:AO-91 Pass (45° max elevation)
DTSTART:20251226T123000Z
DTEND:20251226T124000Z
DESCRIPTION:Rise: 12:30 UTC @ 10°\nPeak: 12:35 UTC @ 45°\nSet: 12:40 UTC @ 5°
LOCATION:Boulder, CO (40.0°N, 105.0°W)
END:VEVENT
```

**Benefits**:
- Google Calendar, Outlook, Apple Calendar integration
- Native reminders and notifications
- Share pass schedules with team
- Automatic timezone conversion

**Implementation Notes**:
- Use icalendar library
- Add alarms (e.g., 15 min before AOS)
- Include ground station coordinates
- Optional: add max elevation to summary

---

#### 7. Better Error Handling ⭐⭐
**Status**: Not Started | **Effort**: 1.5 hours | **Impact**: Medium

**Description**: Improve error messages with actionable suggestions.

**Current**:
```
FileNotFoundError: [Errno 2] No such file or directory: 'data/tle.txt'
```

**Improved**:
```
❌ Error: TLE file not found: data/tle.txt

Suggestions:
  • Check file path spelling
  • Available TLE files:
    - data/tle_leo/AO-91.txt
    - data/tle_leo/AO-95.txt
  • Download fresh TLEs from: https://celestrak.org/

For help: python main.py --help
```

**Benefits**:
- Better user experience for beginners
- Faster debugging
- Self-documenting errors

**Implementation Notes**:
- Wrap common exceptions (FileNotFoundError, ValueError, etc.)
- List available files on missing file errors
- Validate inputs before processing
- Use rich or colorama for formatting

---

### Priority 3: Advanced Features (Higher Effort)

#### 8. Real-Time Pass Monitoring ⭐⭐⭐
**Status**: Not Started | **Effort**: 3 hours | **Impact**: Medium

**Description**: Monitor satellite position in real-time with live updates and alerts.

**Usage**:
```bash
python main.py --tle data/tle.txt --watch --alert-elevation 10
```

**Output**:
```
🛰️ AO-91 Real-Time Tracker
Current Time: 2025-12-26 12:28:00 UTC
Status: Pre-pass (2 min until AOS)
Next AOS: 12:30:00 UTC @ 10° elevation

[Updates every 10 seconds]

🔔 ALERT: AO-91 rising! AOS @ 10° elevation
🔔 ALERT: Peak elevation (45°) in 5 minutes
🔔 ALERT: AO-91 setting @ 5° elevation
```

**Benefits**:
- Live tracking for photography/observation
- Sound notifications for AOS/LOS
- No manual timing required

**Implementation Notes**:
- Use time.sleep() for update loop
- Terminal UI with curses or rich
- Sound alerts with playsound
- Ctrl+C to exit gracefully

---

#### 9. Uncertainty Quantification ⭐⭐⭐
**Status**: Not Started | **Effort**: 2 hours | **Impact**: Medium

**Description**: Calculate and display prediction uncertainty based on TLE age and orbit characteristics.

**Output**:
```json
{
  "aos_time": "2025-12-26T12:30:00Z",
  "aos_uncertainty_seconds": 180,
  "tca_time": "2025-12-26T12:35:22Z",
  "tca_uncertainty_seconds": 90,
  "max_elevation_deg": 45.2,
  "max_elevation_uncertainty_deg": 2.1,
  "tle_age_days": 3.5,
  "confidence_level": "high"
}
```

**Uncertainty Model**:
- LEO: ±30 seconds per day of TLE age
- GEO: ±5 seconds per day of TLE age
- Elevation: ±0.5° per day of TLE age

**Benefits**:
- Scientific rigor
- Mission planning confidence
- TLE freshness awareness

**Implementation Notes**:
- Calculate TLE epoch age
- Apply empirical uncertainty models
- Display confidence intervals
- Color-code by confidence level

---

#### 10. Station Location Presets ⭐⭐
**Status**: Not Started | **Effort**: 30 min | **Impact**: Low

**Description**: Built-in database of famous ground stations and observatories.

**Usage**:
```bash
python main.py --tle data/tle.txt --station jpl
python main.py --tle data/tle.txt --station goddard
python main.py --tle data/tle.txt --station arecibo
```

**Presets**:
```python
STATIONS = {
    "jpl": {"lat": 34.2, "lon": -118.2, "alt": 230, "name": "JPL Pasadena"},
    "goddard": {"lat": 38.8, "lon": -77.0, "alt": 20, "name": "Goddard SFC"},
    "arecibo": {"lat": 18.3, "lon": -66.7, "alt": 305, "name": "Arecibo Observatory"},
    "vla": {"lat": 34.1, "lon": -107.6, "alt": 2124, "name": "Very Large Array"},
    "gse": {"lat": 51.9, "lon": 5.8, "alt": 70, "name": "ESA Redu"},
}
```

**Benefits**:
- Quick setup for famous locations
- Educational value (learn about ground stations)
- No coordinate lookup required

**Implementation Notes**:
- Store in JSON config file
- Allow user-defined station additions
- List all with --list-stations

---

#### 11. TLE Auto-Update ⭐⭐
**Status**: Not Started | **Effort**: 1 hour | **Impact**: Medium

**Description**: Automatically download fresh TLEs from CelesTrak before predictions.

**Usage**:
```bash
# Auto-update before prediction
python main.py --tle data/tle_leo/AO-91.txt --auto-update

# Update all TLEs in directory
python main.py --update-all-tles --tle-dir data/tle_leo/
```

**Benefits**:
- Always fresh TLE data
- No manual downloads
- Improved accuracy

**Implementation Notes**:
- Use requests library
- Parse CelesTrak catalog
- Cache with timestamp
- Fallback to local TLE if download fails

---

#### 12. KML Export ⭐⭐
**Status**: Not Started | **Effort**: 1.5 hours | **Impact**: Low

**Description**: Export ground tracks and passes as KML for Google Earth visualization.

**Usage**:
```bash
python main.py --tle data/tle.txt --format kml --output pass.kml
```

**KML Features**:
- Ground track path
- Pass visibility cones
- Ground station placemark
- Time animation

**Benefits**:
- Stunning 3D visualization
- Terrain analysis
- Public sharing

**Implementation Notes**:
- Use simplekml library
- Add time spans for animation
- Color-code by elevation
- Include altitude profile

---

### Priority 4: Infrastructure (Long-Term)

#### 13. Web Interface & REST API ⭐⭐
**Status**: Not Started | **Effort**: 6 hours | **Impact**: High

**Description**: Deploy as web service with REST API and browser UI.

**Architecture**:
```
Frontend (React/Vue)
    ↓
REST API (FastAPI)
    ↓
Core Engine (src/)
```

**API Endpoints**:
```
POST /api/predict
GET /api/satellites
GET /api/stations
GET /api/passes/{satellite_id}
```

**Web UI Features**:
- Interactive map with ground tracks
- Pass list with filtering
- Station selector
- Export buttons (JSON/CSV/ICS)

**Benefits**:
- No Python installation required
- Mobile-friendly
- Multi-user support
- Cloud deployment

**Implementation Notes**:
- Use FastAPI for backend
- React or Vue for frontend
- Deploy to Heroku/Railway
- Caching layer (Redis)

---

#### 14. Comprehensive Unit Tests ⭐⭐
**Status**: Partially Implemented | **Effort**: 2 hours | **Impact**: High

**Description**: Full test coverage for CLI features and edge cases.

**Test Areas**:
- Config file parsing
- Batch processing
- Export formats (CSV, ICS, KML)
- Error handling
- Real-time monitoring

**Benefits**:
- Confidence in refactoring
- Catch regressions early
- Documentation via tests

**Implementation Notes**:
- Use pytest fixtures
- Mock external dependencies (CelesTrak API)
- Integration tests for CLI
- Target 90%+ coverage

---

## Implementation Strategy

### Phase 1: Usability (Weeks 1-2)
**Goal**: Make tool easier to use for daily workflows

**Tasks**:
1. Config file support (30 min)
2. Batch processing (20 min)
3. Enhanced pass filtering (45 min)
4. JSON output by default (15 min)

**Total Effort**: ~2 hours  
**Expected Outcome**: Dramatically improved UX for recurring predictions

---

### Phase 2: Integration (Weeks 3-4)
**Goal**: Enable external tool integration

**Tasks**:
1. CSV export (1 hour)
2. Better error handling (1.5 hours)
3. ICS export (2 hours)
4. Station presets (30 min)

**Total Effort**: ~5 hours  
**Expected Outcome**: Calendar integration, spreadsheet analysis

---

### Phase 3: Advanced (Weeks 5-8)
**Goal**: Add scientific and real-time capabilities

**Tasks**:
1. Uncertainty quantification (2 hours)
2. Real-time monitoring (3 hours)
3. TLE auto-update (1 hour)
4. KML export (1.5 hours)

**Total Effort**: ~7.5 hours  
**Expected Outcome**: Professional-grade analysis tools

---

### Phase 4: Web Platform (Weeks 9-16)
**Goal**: Deploy as accessible web service

**Tasks**:
1. REST API (3 hours)
2. Web UI (3 hours)
3. Deployment setup (2 hours)
4. Comprehensive testing (2 hours)

**Total Effort**: ~10 hours  
**Expected Outcome**: Production-ready web platform

---

## Total Development Estimate

**Total Features**: 14  
**Total Development Time**: ~25 hours  
**Timeline**: 16 weeks (part-time, 2-3 hrs/week)

---

## Decision Framework

Choose features based on your primary use case:

### For Amateur Radio Operators:
Priority: Config files → Batch processing → ICS export → Station presets

### For Astronomers:
Priority: Real-time monitoring → Uncertainty quantification → CSV export → KML export

### For Educators:
Priority: Better error handling → Station presets → Web interface → Config files

### For Mission Planners:
Priority: Batch processing → CSV export → Uncertainty quantification → API

### For Developers:
Priority: Unit tests → Config files → REST API → Better error handling

---

## Contributing

Interested in implementing a feature? See [DEVELOPMENT.md](DEVELOPMENT.md) for:
- Development environment setup
- Code style guidelines
- Testing requirements
- Pull request process

Start with Priority 1 features (quick wins) to familiarize yourself with the codebase.

---

## Questions & Feedback

Have suggestions for the roadmap? Open an issue on GitHub with:
- Feature description
- Use case explanation
- Priority justification
- Implementation ideas (if any)

---

**Ready to contribute?** Pick a feature and let's build! 🚀

See [Architecture](ARCHITECTURE.md) for technical details and [Usage Guide](USAGE_GUIDE.md) for current capabilities.
