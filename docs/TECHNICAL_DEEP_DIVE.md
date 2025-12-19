# Satellite Pass Predictor — Detailed Technical Deep-Dive

This document explains **every step** of how the code calculates satellite passes: from TLE parsing to elevation angle to pass detection.

---

## Table of Contents
1. [Data Flow Overview](#data-flow-overview)
2. [Step 1: Load TLE](#step-1-load-tle)
3. [Step 2: Create Time Grid](#step-2-create-time-grid)
4. [Step 3: SGP4 Propagation (TEME)](#step-3-sgp4-propagation-teme)
5. [Step 4: Convert TEME to ECEF](#step-4-convert-teme-to-ecef)
6. [Step 5: Ground Station Position](#step-5-ground-station-position)
7. [Step 6: Topocentric Elevation](#step-6-topocentric-elevation)
8. [Step 7: Pass Detection](#step-7-pass-detection)
9. [Example Walkthrough](#example-walkthrough)

---

## Data Flow Overview

```
TLE File (3 lines)
    ↓
[Parse] → Satellite name, Line1, Line2
    ↓
[SGP4 Init] → Satrec object (orbital parameters)
    ↓
For each timestamp t in [t0, t0+Δt, t0+2Δt, ..., t_end]:
    ├─ [SGP4 Propagation] → TEME position (x_teme, y_teme, z_teme) in km
    ├─ [GMST Calculation] → GMST angle θ (radians)
    ├─ [TEME→ECEF Rotation] → ECEF position (x_ecef, y_ecef, z_ecef) in km
    ├─ [Ground Station] → Station position in ECEF
    ├─ [Topocentric ENU] → Relative position (east, north, up)
    └─ [Elevation Angle] → el_deg (degrees)
    ↓
[Collect all elevations]
    ↓
[Pass Detection] → Find regions where el_deg > threshold
    ↓
[Output JSON] → Pass times and max elevation

[Optional Visualization]
├─ Ground track: ECEF → geodetic lat/lon
└─ Elevation plot: time vs elevation with pass bands
```

---

## Step 1: Load TLE

### What is a TLE?
A **Two-Line Element** (TLE) is a compact text format encoding a satellite's orbit. Example:

```
ISS (ZARYA)
1 25544U 98067A   25353.12345678  .00007068  00000-0  12345-3 0  9999
2 25544  51.6418 118.4219 0005821 276.5210  83.5890 15.54485425428976
```

**Line 0:** Satellite name
**Line 1:** Catalog number, epoch, drag terms, etc.
**Line 2:** Inclination, RAAN, eccentricity, argument of perigee, mean anomaly, mean motion

### Code: `tle_loader.py`
```python
def load_tle(path: str) -> Tuple[str, str, str]:
    with open(path, "r", encoding="utf-8") as f:
        lines = [ln.strip() for ln in f.readlines()]
    content = [ln for ln in lines if ln and not ln.startswith("#")]
    name, line1, line2 = content[0], content[1], content[2]
    return name, line1, line2
```

**Steps:**
1. Read file, strip whitespace from each line.
2. Filter out blank lines and comments (lines starting with `#`).
3. Extract first three non-empty lines as name, line1, line2.

### Example Output
```
name = "ISS (ZARYA)"
line1 = "1 25544U 98067A   25353.12345678  .00007068  00000-0  12345-3 0  9999"
line2 = "2 25544  51.6418 118.4219 0005821 276.5210  83.5890 15.54485425428976"
```

---

## Step 2: Create Time Grid

### Purpose
Generate a sequence of timestamps at regular intervals over the prediction horizon.

### Code: `main.py`
```python
def datetime_range(start: datetime, end: datetime, step_seconds: float) -> List[datetime]:
    times: List[datetime] = []
    t = start
    step = timedelta(seconds=step_seconds)
    while t <= end:
        times.append(t)
        t += step
    return times

# Usage
start_utc = datetime.now(timezone.utc)  # or provided via --start-utc
end_utc = start_utc + timedelta(hours=args.hours)  # default 48 hours
times = datetime_range(start_utc, end_utc, args.step)  # default step=30s
```

### Example (1 hour, 30s step)
```
times = [
  2025-12-19T04:00:00Z,
  2025-12-19T04:00:30Z,
  2025-12-19T04:01:00Z,
  ...
  2025-12-19T05:00:00Z
]
# Total: 121 timestamps
```

---

## Step 3: SGP4 Propagation (TEME)

### What is SGP4?
**SGP4** (Simplified General Perturbations 4) is an orbital propagation model that predicts satellite position given:
- Orbital elements (encoded in TLE)
- A target date/time

It accounts for Earth's oblateness (J2 perturbation), atmospheric drag, and solar/lunar effects.

### What is TEME?
**TEME** (True Equator, Mean Equinox) is an inertial coordinate frame:
- **True Equator:** Uses Earth's actual (instantaneous) equatorial plane.
- **Mean Equinox:** Uses a mean (averaged) vernal equinox direction.
- **Inertial:** Doesn't rotate with Earth; fixed relative to distant stars.

SGP4 outputs position in TEME because it's the frame defined by the TLE epoch.

### Code: `propagator.py`
```python
def satrec_from_tle(line1: str, line2: str) -> Satrec:
    return Satrec.twoline2rv(line1, line2)  # SGP4 library parses TLE

def propagate_teme(sat: Satrec, dt: datetime) -> TemEci:
    # Convert UTC datetime to Julian Date (two-part for precision)
    jd, fr = jday(dt.year, dt.month, dt.day, dt.hour, dt.minute, 
                  dt.second + dt.microsecond / 1e6)
    
    # Call SGP4 propagation
    error_code, r, v = sat.sgp4(jd, fr)
    
    if error_code != 0:
        raise RuntimeError(f"SGP4 error code {error_code}")
    
    return TemEci(dt=dt, r_km=(r[0], r[1], r[2]), v_km_s=(v[0], v[1], v[2]))
```

### Detailed Breakdown

#### 3a. Convert UTC to Julian Date
```python
jd, fr = jday(dt.year, dt.month, dt.day, dt.hour, dt.minute, 
              dt.second + dt.microsecond / 1e6)
```

**What is Julian Date (JD)?**
Number of days since noon UT on January 1, 4713 BC. Astronomers use it because it's unambiguous and easy to do arithmetic on.

**Why two-part (jd + fr)?**
- `jd`: Integer part (Julian day number).
- `fr`: Fractional part (0 to 1, representing the day fraction).
- Splitting them maintains floating-point precision over large time spans.

**Example:**
```
Input:  2025-12-19T04:30:00Z
Output: jd = 2460682, fr = 0.6875
        (day 2460682 + 0.6875 days = ~4:30 AM)
```

#### 3b. SGP4 Propagation
```python
error_code, r, v = sat.sgp4(jd, fr)
```

**Input:**
- `jd, fr`: Target Julian date
- Orbital parameters from TLE (encoded in `sat`)

**Output:**
- `r = (x_teme, y_teme, z_teme)`: Position in TEME, **in km**
- `v = (vx_teme, vy_teme, vz_teme)`: Velocity in TEME, **in km/s**
- `error_code`: 0 = success, non-zero = error (e.g., satellite decayed)

**Physics inside SGP4 (simplified):**
```
1. Use orbital elements from TLE to compute mean anomaly at epoch.
2. Apply Kepler's equation to convert mean anomaly → true anomaly.
3. Compute position in orbital plane (perifocal coordinates).
4. Apply coordinate rotations (RAAN, inclination, argument of perigee).
5. Apply perturbations (J2, drag, solar/lunar effects).
6. Output: TEME position and velocity.
```

**Example Output:**
```
r_teme = (1234.567, -5678.901, 3456.789)  # km
v_teme = (7.234, 2.456, -1.892)           # km/s
```

---

## Step 4: Convert TEME to ECEF

### Why Convert?
- SGP4 outputs **TEME** (inertial, doesn't rotate with Earth).
- Ground stations are fixed on **ECEF** (Earth-Centered, Earth-Fixed).
- To compare satellite and ground station, both must be in the same frame: **ECEF**.

### The Conversion: Z-Rotation by GMST

The transformation is a simple **rotation around Earth's Z-axis** by the **Greenwich Mean Sidereal Time (GMST)** angle:

$$\begin{pmatrix} x_{ecef} \\ y_{ecef} \\ z_{ecef} \end{pmatrix} = \begin{pmatrix} \cos(\theta_{gmst}) & \sin(\theta_{gmst}) & 0 \\ -\sin(\theta_{gmst}) & \cos(\theta_{gmst}) & 0 \\ 0 & 0 & 1 \end{pmatrix} \begin{pmatrix} x_{teme} \\ y_{teme} \\ z_{teme} \end{pmatrix}$$

where $\theta_{gmst}$ is the GMST angle in radians.

### Code: `propagator.py`

#### 4a. Calculate GMST
```python
def gmst_angle(dt: datetime) -> float:
    # Convert UTC datetime to Julian date
    jd, fr = jday(dt.year, dt.month, dt.day, dt.hour, dt.minute, 
                  dt.second + dt.microsecond / 1e6)
    jd_ut1 = jd + fr
    
    # Days since J2000.0 epoch (Jan 1, 2000 12:00 UT)
    t_ut1 = (jd_ut1 - 2451545.0) / 36525.0
    
    # IAU 1982 GMST formula (in seconds)
    gmst_sec = 67310.54841 + (876600.0 * 3600.0 + 8640184.812866) * t_ut1 \
               + 0.093104 * t_ut1**2 - 6.2e-6 * t_ut1**3
    
    # Convert seconds → radians
    gmst_rad = math.fmod(gmst_sec * (2.0 * math.pi / 86400.0), 2.0 * math.pi)
    
    # Ensure [0, 2π)
    if gmst_rad < 0:
        gmst_rad += 2.0 * math.pi
    
    return gmst_rad
```

**Breakdown:**

| Step | Formula | Purpose |
|------|---------|---------|
| 1 | `jd_ut1 = jd + fr` | Combine Julian day parts |
| 2 | `t_ut1 = (jd_ut1 - 2451545.0) / 36525.0` | Convert to centuries since J2000.0 |
| 3 | `gmst_sec = 67310.54841 + ...` | IAU 1982 polynomial (output in seconds) |
| 4 | `gmst_rad = gmst_sec * (2π/86400)` | Convert seconds → radians (86400 sec/day) |
| 5 | `gmst_rad % 2π` | Normalize to [0, 2π) |

**Why This Polynomial?**
The IAU 1982 GMST formula accounts for:
- Earth's rotation (primary term ≈ 360° per sidereal day).
- Precession (slow drift over centuries).
- Nutation (periodic wobbles).

**Example Calculation (2025-12-19T04:30:00Z):**
```
jd_ut1 ≈ 2460682.6875
t_ut1 ≈ 0.258 centuries since J2000.0
gmst_sec ≈ 67310 + 2.26e10 * 0.258 + ... ≈ 82500 seconds
gmst_rad ≈ 82500 * (2π/86400) ≈ 5.987 radians ≈ 342.8°
```

This means at this UTC time, the Prime Meridian (0° longitude) has rotated 342.8° eastward relative to the inertial frame.

#### 4b. Rotate TEME to ECEF
```python
def teme_to_ecef(r_teme_km: Tuple[float, float, float], gmst_rad: float) -> Tuple[float, float, float]:
    x, y, z = r_teme_km
    cg = math.cos(gmst_rad)
    sg = math.sin(gmst_rad)
    
    x_e = cg * x + sg * y
    y_e = -sg * x + cg * y
    z_e = z  # Z unchanged in rotation
    
    return (x_e, y_e, z_e)
```

**Example:**
```
Input:  r_teme = (1234.567, -5678.901, 3456.789) km
        gmst_rad = 5.987 rad
        cos(5.987) ≈ 0.2370, sin(5.987) ≈ -0.9716

Output: x_e = 0.2370 * 1234.567 + (-0.9716) * (-5678.901) ≈ 5790.2 km
        y_e = -(-0.9716) * 1234.567 + 0.2370 * (-5678.901) ≈ 640.8 km
        z_e = 3456.789 km

r_ecef ≈ (5790.2, 640.8, 3456.789) km
```

---

## Step 5: Ground Station Position

### Purpose
Compute the ground station's location in ECEF so we can compute relative vectors.

### WGS84 Ellipsoid
Earth isn't a perfect sphere — it bulges at the equator. **WGS84** (World Geodetic System 1984) models Earth as an ellipsoid:
- Semi-major axis (equatorial radius): $a = 6378.137$ km
- Flattening: $f = 1/298.257223563$ (≈ 0.00335)
- Eccentricity squared: $e^2 = f(2-f) ≈ 0.00669$

### Code: `ground_station.py`
```python
@dataclass
class GroundStation:
    lat_deg: float    # Geodetic latitude (-90 to 90)
    lon_deg: float    # Longitude (-180 to 180)
    alt_m: float      # Altitude above ellipsoid (meters)

    def ecef_km(self) -> Tuple[float, float, float]:
        """Convert geodetic (lat, lon, alt) to ECEF (km)"""
        lat = math.radians(self.lat_deg)
        lon = math.radians(self.lon_deg)
        
        sin_lat = math.sin(lat)
        cos_lat = math.cos(lat)
        
        # Radius of curvature in prime vertical
        N = _A / math.sqrt(1.0 - _E2 * sin_lat**2)
        
        # ECEF coordinates
        x = (N + self.alt_km) * cos_lat * math.cos(lon)
        y = (N + self.alt_km) * cos_lat * math.sin(lon)
        z = (N * (1 - _E2) + self.alt_km) * sin_lat
        
        return (x, y, z)
```

### Detailed Breakdown

#### 5a. Radius of Curvature (N)
$$N = \frac{a}{\sqrt{1 - e^2 \sin^2(\text{lat})}}$$

This is the **distance from Earth's center to a point on the surface** (at the given latitude), measured perpendicular to the ellipsoid.

- At equator (lat=0): $N = a = 6378.137$ km
- At poles (lat=90°): $N = a(1-e^2) = 6356.752$ km (smaller because ellipsoid is flattened)

#### 5b. ECEF Coordinates
$$x = (N + h) \cos(\text{lat}) \cos(\text{lon})$$
$$y = (N + h) \cos(\text{lat}) \sin(\text{lon})$$
$$z = (N(1 - e^2) + h) \sin(\text{lat})$$

where $h$ is altitude in km.

**Intuition:**
- Project onto XY plane: $(N+h) \cos(\text{lat})$
- Apply lon rotation: multiply by $\cos(\text{lon}), \sin(\text{lon})$
- Z axis: use flattened radius $N(1-e^2)$ to account for ellipsoid shape

#### 5c. Example: Boulder, Colorado
```
Input:  lat_deg = 40.0°, lon_deg = -105.0°, alt_m = 1600 m
        alt_km = 1.6 km

Compute:
N = 6378.137 / sqrt(1 - 0.00669 * sin²(40°))
  ≈ 6378.137 / sqrt(1 - 0.00669 * 0.4132)
  ≈ 6378.137 / 0.9973
  ≈ 6388.6 km

lat_rad = 40° * π/180 ≈ 0.6981 rad
lon_rad = -105° * π/180 ≈ -1.833 rad

x = (6388.6 + 1.6) * cos(0.6981) * cos(-1.833)
  ≈ 6390.2 * 0.766 * (-0.226)
  ≈ -1109.8 km

y = (6388.6 + 1.6) * cos(0.6981) * sin(-1.833)
  ≈ 6390.2 * 0.766 * (-0.974)
  ≈ -4761.2 km

z = (6388.6 * (1 - 0.00669) + 1.6) * sin(0.6981)
  ≈ (6356.0 + 1.6) * 0.6428
  ≈ 4084.4 km

Output: r_station ≈ (-1109.8, -4761.2, 4084.4) km
```

---

## Step 6: Topocentric Elevation

### Purpose
Calculate the angle above the horizon from the ground station to the satellite.

### Two Substeps
1. **ENU Conversion:** Satellite position relative to station in local East-North-Up frame.
2. **Elevation Calculation:** Convert ENU to elevation angle (degrees).

### Code: `ground_station.py`

#### 6a. Compute ENU
```python
def enu_from_ecef(self, sat_ecef_km: Tuple[float, float, float]) -> Tuple[float, float, float]:
    """Convert satellite ECEF to station-centered ENU"""
    x_e, y_e, z_e = sat_ecef_km
    xs, ys, zs = self.ecef_km()
    
    # Relative position (ECEF)
    dx, dy, dz = x_e - xs, y_e - ys, z_e - zs
    
    # Station orientation angles
    lat = self.lat_rad
    lon = self.lon_rad
    sin_lat = math.sin(lat)
    cos_lat = math.cos(lat)
    sin_lon = math.sin(lon)
    cos_lon = math.cos(lon)
    
    # Rotation matrix: ECEF → ENU
    # ENU is a local geodetic frame: E (east), N (north), U (up)
    e = -sin_lon * dx + cos_lon * dy
    n = -sin_lat * cos_lon * dx - sin_lat * sin_lon * dy + cos_lat * dz
    u = cos_lat * cos_lon * dx + cos_lat * sin_lon * dy + sin_lat * dz
    
    return (e, n, u)
```

**Coordinate Frame ENU:**
- **East (E):** Tangent to surface, pointing eastward
- **North (N):** Tangent to surface, pointing northward
- **Up (U):** Perpendicular to ellipsoid (zenith)

**Rotation Matrix (ECEF → ENU):**
$$\begin{pmatrix} e \\ n \\ u \end{pmatrix} = \begin{pmatrix} -\sin(\text{lon}) & \cos(\text{lon}) & 0 \\ -\sin(\text{lat})\cos(\text{lon}) & -\sin(\text{lat})\sin(\text{lon}) & \cos(\text{lat}) \\ \cos(\text{lat})\cos(\text{lon}) & \cos(\text{lat})\sin(\text{lon}) & \sin(\text{lat}) \end{pmatrix} \begin{pmatrix} \Delta x \\ \Delta y \\ \Delta z \end{pmatrix}$$

#### 6b. Compute Elevation Angle
```python
def elevation_deg(self, sat_ecef_km: Tuple[float, float, float]) -> float:
    """Compute elevation angle in degrees"""
    e, n, u = self.enu_from_ecef(sat_ecef_km)
    
    # Horizontal distance
    horiz = math.hypot(e, n)
    
    # Elevation angle
    el = math.degrees(math.atan2(u, horiz))
    
    return el
```

**Formula:**
$$\text{elevation} = \arctan\left(\frac{u}{\sqrt{e^2 + n^2}}\right)$$

**Interpretation:**
- $u > 0$: Satellite above horizon (positive elevation)
- $u < 0$: Satellite below horizon (negative elevation)
- $u = 0$: Satellite on horizon (elevation = 0°)

#### 6c. Example
```
Satellite ECEF:  sat = (5790.2, 640.8, 3456.789) km
Station ECEF:    station ≈ (-1109.8, -4761.2, 4084.4) km

Relative ECEF:   Δr = (5790.2 - (-1109.8), 640.8 - (-4761.2), 3456.789 - 4084.4)
                     = (6900.0, 5402.0, -627.6) km

ENU conversion (lat=40°, lon=-105°):
e ≈ -sin(-105°) * 6900 + cos(-105°) * 5402
  ≈ 0.966 * 6900 - 0.259 * 5402
  ≈ 6665.4 - 1399.1
  ≈ 5266.3 km (eastward)

n ≈ -sin(40°) * cos(-105°) * 6900 - sin(40°) * sin(-105°) * 5402 + cos(40°) * (-627.6)
  ≈ -(-0.643) * (-0.259) * 6900 - (-0.643) * 0.966 * 5402 + 0.766 * (-627.6)
  ≈ -1148.8 + 3369.3 - 481.0
  ≈ 1739.5 km (northward)

u ≈ cos(40°) * cos(-105°) * 6900 + cos(40°) * sin(-105°) * 5402 + sin(40°) * (-627.6)
  ≈ 0.766 * (-0.259) * 6900 + 0.766 * 0.966 * 5402 + 0.643 * (-627.6)
  ≈ -1367.3 + 4014.5 - 403.5
  ≈ 2243.7 km (upward)

Elevation:
horiz = sqrt(5266.3² + 1739.5²) ≈ 5556.8 km
el = atan2(2243.7, 5556.8) * 180/π ≈ 21.97°
```

**Meaning:** The satellite appears ~22° above the horizon from the ground station.

---

## Step 7: Pass Detection

### Purpose
Scan the elevation time series and identify "passes" — continuous intervals where elevation exceeds a threshold.

### Code: `pass_detector.py`

```python
def detect_passes(times: Sequence[datetime], elev_deg: Sequence[float], 
                  threshold_deg: float = 10.0) -> List[PassEvent]:
    """Find passes where elevation > threshold"""
    passes: List[PassEvent] = []
    
    in_pass = False
    aos_time = None           # Acquisition of Signal
    max_el = -1e9
    max_time = None
    
    # Iterate through consecutive pairs
    for i in range(1, len(times)):
        t0, t1 = times[i - 1], times[i]
        e0, e1 = elev_deg[i - 1], elev_deg[i]
        
        if not in_pass:
            # Check for upward crossing of threshold
            if e0 <= threshold_deg and e1 > threshold_deg:
                # Linearly interpolate exact crossing time
                aos_time = _interp_time(t0, t1, e0, e1, threshold_deg)
                in_pass = True
                max_el = e1
                max_time = t1
            elif e1 > threshold_deg and e0 > threshold_deg and aos_time is None:
                # Already above threshold at start of window
                aos_time = t0
                in_pass = True
                max_el = max(e0, e1)
                max_time = t0 if e0 >= e1 else t1
        
        else:  # in_pass
            # Update max elevation within pass
            if e1 > max_el:
                max_el = e1
                max_time = t1
            
            # Check for downward crossing
            if e0 > threshold_deg and e1 <= threshold_deg:
                los_time = _interp_time(t0, t1, e0, e1, threshold_deg)
                passes.append(PassEvent(start_time=aos_time, max_time=max_time, 
                                       end_time=los_time, max_elevation_deg=max_el))
                in_pass = False
                aos_time = None
                max_el = -1e9
                max_time = None
    
    # Handle pass that continues past final sample
    if in_pass and aos_time is not None:
        passes.append(PassEvent(start_time=aos_time, max_time=max_time, 
                               end_time=times[-1], max_elevation_deg=max_el))
    
    return passes
```

### Detailed Breakdown

#### 7a. State Machine Logic
The algorithm uses a **finite state machine** with two states:

**State 1: `in_pass = False` (Not in a pass)**
- Look for elevation crossing **upward** through threshold.
- When found: Record AOS (Acquisition of Signal) time, switch to `in_pass = True`.
- Special case: If prediction window starts already above threshold, mark t0 as AOS.

**State 2: `in_pass = True` (Currently in a pass)**
- Track maximum elevation and its time.
- Look for elevation crossing **downward** through threshold.
- When found: Record LOS (Loss of Signal) time, create PassEvent, switch to `in_pass = False`.

#### 7b. Linear Interpolation for Threshold Crossings
```python
def _interp_time(t0: datetime, t1: datetime, y0: float, y1: float, y: float) -> datetime:
    """Linearly interpolate time when y crosses threshold between t0 and t1"""
    if y1 == y0:
        return t0
    frac = (y - y0) / (y1 - y0)
    frac = max(0.0, min(1.0, frac))  # Clamp to [0, 1]
    return t0 + (t1 - t0) * frac
```

**Example (AOS):**
```
Samples:
  t0 = 04:27:00Z,  e0 = 9.5° (below 10° threshold)
  t1 = 04:27:30Z,  e1 = 10.8° (above 10° threshold)

Threshold crossing:
frac = (10.0 - 9.5) / (10.8 - 9.5)
     = 0.5 / 1.3
     ≈ 0.3846

AOS = 04:27:00Z + 0.3846 * 30s
    ≈ 04:27:11.5Z
```

#### 7c. PassEvent Output
```python
@dataclass
class PassEvent:
    start_time: datetime        # AOS (exact, interpolated)
    max_time: datetime          # Time of max elevation (sample)
    end_time: datetime          # LOS (exact, interpolated)
    max_elevation_deg: float    # Peak elevation
```

#### 7d. Example Walkthrough
```
Input:
times = [04:25Z, 04:25:30Z, 04:26Z, 04:26:30Z, 04:27Z, 04:27:30Z, 04:28Z, ...]
elev  = [7.2°,   8.5°,      9.1°,   10.3°,    12.5°,  15.3°,     12.1°,  ...]
threshold = 10°

Iteration 1: (04:25Z, 7.2°) vs (04:25:30Z, 8.5°) → 8.5° < 10°, not in pass
Iteration 2: (04:25:30Z, 8.5°) vs (04:26Z, 9.1°) → 9.1° < 10°, not in pass
Iteration 3: (04:26Z, 9.1°) vs (04:26:30Z, 10.3°) → 9.1° ≤ 10° and 10.3° > 10°
            → Threshold crossing detected (upward)
            → AOS = interpolated(04:26Z, 04:26:30Z, 9.1°, 10.3°, 10°) ≈ 04:26:20Z
            → in_pass = True, max_el = 10.3°, max_time = 04:26:30Z

Iteration 4: (04:26:30Z, 10.3°) vs (04:27Z, 12.5°) → Both > 10°
            → Update max: max_el = 12.5°, max_time = 04:27Z

Iteration 5: (04:27Z, 12.5°) vs (04:27:30Z, 15.3°) → Both > 10°
            → Update max: max_el = 15.3°, max_time = 04:27:30Z

Iteration 6: (04:27:30Z, 15.3°) vs (04:28Z, 12.1°) → Both > 10°
            → No update to max

Iteration 7 (if exists): (04:28Z, 12.1°) vs (04:28:30Z, 8.6°) → 12.1° > 10° and 8.6° ≤ 10°
            → Threshold crossing (downward)
            → LOS = interpolated(04:28Z, 04:28:30Z, 12.1°, 8.6°, 10°) ≈ 04:28:12Z
            → PassEvent created:
               {start: 04:26:20Z, max: 04:27:30Z, end: 04:28:12Z, max_el: 15.3°}
            → in_pass = False

Output:
[PassEvent(start_time=2025-12-19T04:26:20Z, 
           max_time=2025-12-19T04:27:30Z, 
           end_time=2025-12-19T04:28:12Z, 
           max_elevation_deg=15.3)]
```

---

## Step 8: Visualization (v1.1)

### 8a. Ground Track Plot
**Goal:** Show satellite's ground track (sub-satellite point: latitude/longitude).

**Calculation:** For each ECEF position, convert to geodetic lat/lon.

```python
def ecef_to_geodetic_latlon(ecef_km: Tuple[float, float, float]) -> Tuple[float, float]:
    """Convert ECEF (km) to geodetic (lat, lon) in degrees"""
    x, y, z = ecef_km
    lon = math.degrees(math.atan2(y, x))
    
    # Iterative latitude computation
    r = math.hypot(x, y)
    lat = math.atan2(z, r)
    
    for _ in range(5):
        sin_lat = math.sin(lat)
        N = _A / math.sqrt(1.0 - _E2 * sin_lat**2)
        lat = math.atan2(z + N * _E2 * sin_lat, r)
    
    return (math.degrees(lat), lon)
```

**Output:** Plot (time vs lon/lat) or (lon vs lat) map.

### 8b. Elevation Plot
**Goal:** Show elevation angle vs time with pass windows highlighted.

**Features:**
- Line: elevation curve for entire prediction window
- Green bands: regions where elevation > threshold (pass windows)
- Red dashes: times of maximum elevation

---

## Example Walkthrough

### Setup
```
TLE:      ISS (ZARYA) from data/tle.txt
Station:  Boulder, CO (40.0°N, -105.0°W, 1600 m)
Threshold: 10°
Horizon:  48 hours (2025-12-19T00:00Z to 2025-12-21T00:00Z)
Step:     30 seconds
```

### Timeline
1. **Load TLE:** Parse satellite name and orbital elements.
2. **Create time grid:** [2025-12-19T00:00Z, 2025-12-19T00:00:30Z, ..., 2025-12-21T00:00Z] (5761 samples)
3. **For each timestamp:**
   - **SGP4 propagation:** Compute TEME position (x_teme, y_teme, z_teme)
   - **GMST calculation:** Compute Earth's rotation angle
   - **TEME→ECEF:** Rotate satellite position to Earth-fixed frame
   - **ENU conversion:** Compute relative position from ground station
   - **Elevation angle:** Calculate el_deg
4. **Collect elevations:** Array of 5761 elevation values
5. **Pass detection:** Scan for regions > 10° threshold
6. **Output:** JSON with pass times and peaks

### Example Pass
```json
{
  "startTime": "2025-12-19T04:27:51.392348Z",
  "maxTime": "2025-12-19T04:30:34.468757Z",
  "endTime": "2025-12-19T04:32:41.721574Z",
  "maxElevationDeg": 15.31
}
```

**Meaning:**
- ISS rises above 10° at 04:27:51Z (AOS)
- Reaches peak elevation of 15.31° at 04:30:34Z
- Sets below 10° at 04:32:41Z (LOS)
- **Total pass duration:** ~4 min 50 sec

---

## Summary of Data Types

| Variable | Type | Unit | Example |
|----------|------|------|---------|
| `lat_deg` | float | degrees | 40.0 |
| `lon_deg` | float | degrees | -105.0 |
| `alt_m` | float | meters | 1600 |
| `r_teme` | tuple(3) | km | (1234.567, -5678.901, 3456.789) |
| `gmst_rad` | float | radians | 5.987 |
| `r_ecef` | tuple(3) | km | (5790.2, 640.8, 3456.789) |
| `el_deg` | float | degrees | 15.31 |
| `times` | list[datetime] | UTC | [2025-12-19T00:00Z, ...] |
| `elevations` | list[float] | degrees | [1.2, 2.5, 3.1, ...] |

---

## Key Physics Constants

| Constant | Value | Note |
|----------|-------|------|
| Earth radius (equator) | 6378.137 km | WGS84 semi-major axis |
| Earth radius (pole) | 6356.752 km | WGS84 semi-minor axis |
| Flattening | 1/298.257223563 | WGS84 |
| J2000.0 epoch | JD 2451545.0 | Jan 1, 2000 12:00 UT |
| Seconds per day | 86400 | 24 × 60 × 60 |
| Degrees per radian | 180/π ≈ 57.2958 | Conversion factor |

---

## Common Pitfalls

1. **Forgetting timezone:** Always use UTC; naive datetimes are treated as UTC.
2. **GMST precision:** Use double-precision floats; GMST changes ~15° per hour.
3. **TLE staleness:** TLEs decay over time; update them weekly for best accuracy.
4. **Interpolation at boundaries:** Passes starting/ending at grid edges may be inaccurate; use fine `--step`.
5. **Coordinate frame confusion:** TEME ≠ ECEF ≠ ENU. Know which frame each variable is in.

---

## References

- **SGP4 Library:** https://pypi.org/project/sgp4/
- **Two-Line Elements:** https://celestrak.com/NORAD/documentation/
- **GMST Formula:** https://en.wikipedia.org/wiki/Greenwich_mean_sidereal_time
- **WGS84 Ellipsoid:** https://en.wikipedia.org/wiki/World_Geodetic_System
- **Orbital Mechanics:** Curtis, H. D. *Orbital Mechanics for Engineering Students*, 4th ed.
