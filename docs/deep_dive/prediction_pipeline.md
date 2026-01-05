# Satellite Pass Prediction: How It Works

A practical, detailed walkthrough of how the project turns 3 lines of TLE text plus a ground station location into predicted satellite passes, with optional machine-learning residual corrections.

This document explains every step of the process in plain language with mathematical details, so you can understand exactly how we determine when a satellite will be visible from your location on Earth.

## What Are We Trying to Solve?

**The Core Question:** Given a satellite orbiting Earth, when will it be visible from my location?

To answer this, we need to:
1. Know **where** the satellite is at each moment in time
2. Know **where** our ground station is
3. Calculate the **angle** between us and the satellite
4. Determine if that angle means we can see it

## Inputs: What Information Do We Need?

### 1. Two-Line Element (TLE) Set (3 Lines)
A TLE is a compact text format containing the complete orbital description of a satellite. Example:

```
AO-91 (FUJI-OSCAR 29)
1 25544U 98067A   23340.53507435  .00016717  00000+0  29797-3 0  9005
2 25544  51.6423 247.4627 0001144   94.9090 265.2059 15.50183050429505
```

**What each line means:**
- **Line 0:** Satellite name
- **Line 1:** Orbital epoch (when this data is valid), decay rate, drag coefficient
- **Line 2:** Inclination, RAAN, eccentricity, perigee angle, mean anomaly, mean motion

### 2. Ground Station Location
Your observation point on Earth, described by:
- **Latitude (lat):** North-South position (-90° to +90°)
- **Longitude (lon):** East-West position (-180° to +180°)
- **Altitude (alt_m):** Height above sea level in meters

### 3. Time Window and Step Size
- **Time window:** How far ahead to predict (e.g., 48 hours)
- **Step size:** Time between calculations (e.g., 30 seconds) - smaller = more precise

## Pipeline at a Glance
1. Parse TLE → extract orbital elements
2. Propagate with SGP4 → calculate satellite position at each time step
3. Rotate TEME → ECEF → convert from space-fixed to Earth-fixed coordinates
4. Convert ground station WGS84 → ECEF → align coordinate systems
5. Relative geometry: ECEF → ENU → calculate elevation/azimuth angles
6. Detect passes → find when elevation crosses the visibility threshold
7. (Optional) Apply ML residual correction → improve accuracy using machine learning
8. Output pass list, plots, and JSON data

---

## Part 1 — TLE: Understanding the 3-Line Orbital Blueprint

### What is a TLE?

A TLE (Two-Line Element set) is like a "snapshot in time" of a satellite's orbit. It contains just enough information for a computer to reconstruct the satellite's position anywhere within its validity period (typically a few days to weeks).

### The Six Classical Orbital Elements Decoded

Every orbit can be uniquely described by 6 parameters (called Keplerian elements):

| Element | Symbol | What It Means | Example |
|---------|--------|---------------|---------|
| **Inclination (i)** | i | Angle of orbit relative to Earth's equator (0°=equatorial, 90°=polar) | 51.6° |
| **Right Ascension of Ascending Node (RAAN/Ω)** | Ω | Where the orbit crosses the equator (compass direction) | 247.5° |
| **Eccentricity (e)** | e | How oval-shaped the orbit is (0=perfect circle, 1=escape) | 0.0001 |
| **Argument of Perigee (ω)** | ω | Rotation of the oval within the orbit plane | 94.9° |
| **Mean Anomaly (M)** | M | Position along the orbit at the epoch time | 265.2° |
| **Mean Motion (n)** | n | How many times satellite orbits Earth per day | 15.5 orbits/day |

### Why These 6 Numbers Are Enough

These 6 elements define:
- **The shape** of the orbit (inclination, eccentricity, RAAN, argument of perigee)
- **The size** of the orbit (mean motion tells us the orbital radius)
- **The position** at a specific time (mean anomaly)

Once we know these, we can calculate the satellite's position at *any* future time using physics equations (Kepler's laws).

### The TLE also includes perturbation factors:
- **Drag coefficient (B*):** How much air friction slows the satellite
- **Mean motion decay rate:** How quickly the orbit is decaying
- **Epoch:** The exact date/time these elements are valid for

These account for real-world effects like atmospheric drag and Earth's oblateness.

---

## Part 2 — SGP4 Propagation: Where Is the Satellite Right Now?

### The Propagation Problem

The TLE tells us the orbit's shape and the satellite's position at one specific time (the epoch). But **we need to know where it is at many different times** in the future.

To do this, we use **SGP4** (Simplified General Perturbations 4), a physics model developed by NORAD that:
1. Takes the initial orbital elements at time $t_0$ (epoch)
2. Applies Newton's laws of motion over small time steps
3. Accounts for real-world perturbations that affect the orbit
4. Outputs the satellite's position and velocity at any future time $t$

### What Is Propagation?

Propagation means "calculating forward in time." Think of it like:
- **Without propagation:** You know where a train is *right now*
- **With propagation:** You calculate where the train will be in 1 hour, 2 hours, 10 hours

For satellites, we use physics equations to "propagate" the position forward.

### The Forces Acting on a Satellite

SGP4 accounts for all major forces:

$$F_{\text{total}} = F_{\text{gravity}} + F_{\text{drag}} + F_{\text{J2}} + F_{\text{lunar}} + F_{\text{solar}}$$

Where:
- **$F_{\text{gravity}}$** - Earth's pull (dominant force)
- **$F_{\text{J2}}$** - Effect of Earth's oblateness (Earth is slightly flattened at poles)
- **$F_{\text{drag}}$** - Air resistance from upper atmosphere
- **$F_{\text{lunar}}$** - Moon's gravitational pull (weak but real)
- **$F_{\text{solar}}$** - Sun's gravity and radiation pressure (very small)

### The Propagation Equations

At each time step $\Delta t$ (typically 30 seconds), we calculate:

**Position update:**
$$\vec{r}(t + \Delta t) = \vec{r}(t) + \vec{v}(t) \cdot \Delta t + \frac{1}{2}\vec{a}(t) \cdot (\Delta t)^2$$

**Velocity update:**
$$\vec{v}(t + \Delta t) = \vec{v}(t) + \vec{a}(t) \cdot \Delta t$$

Where:
- $\vec{r}(t)$ = position at time $t$ (in kilometers)
- $\vec{v}(t)$ = velocity at time $t$ (in km/second)
- $\vec{a}(t)$ = acceleration at time $t$ (from the forces above)

### Outputs From SGP4

For each time step, SGP4 gives us:
- **Position vector** $\vec{r}$ = (x, y, z) in kilometers, in **TEME** coordinates
- **Velocity vector** $\vec{v}$ = (vx, vy, vz) in km/second

### What Is TEME Coordinates?

TEME = "True Equator Mean Equinox" — a coordinate system where:
- **Origin:** Center of Earth
- **Z-axis:** Points toward Earth's North Pole
- **X-axis:** Points toward a fixed point in space (doesn't rotate with Earth)

Think of it like: if you stood at Earth's center and froze the universe, TEME doesn't rotate with Earth. This is why we need to convert it later.

---

## Part 3 — Coordinate Transforms: Converting Between Reference Frames

### Why We Need Multiple Coordinate Systems

The problem: **SGP4 gives us satellite position in TEME (space-fixed), but we live on Earth (which rotates).**

Imagine trying to give someone directions:
- **TEME frame:** "The satellite is 3000 km north, 2000 km east" (from a fixed point in space)
- **What we need:** "The satellite is above this city right now" (from a point on rotating Earth)

We need to account for **Earth's rotation** to align the frames.

### Step 1: Calculate GMST (Earth's Rotation Angle)

GMST = Greenwich Mean Sidereal Time — the angle Earth has rotated since midnight.

**Simpler way to think about it:**
- Earth rotates 360° every 24 hours
- Earth rotates 15° every hour (360° / 24h = 15°/h)
- At time $t$, we calculate how many degrees it has rotated since a reference point
- This angle $\theta_{GMST}$ tells us the Earth's current orientation

### Step 2: Apply Z-Rotation to Convert TEME → ECEF

Now we rotate the satellite position by $\theta_{GMST}$ around Earth's Z-axis (North Pole).

**The rotation matrix:**
$$\begin{bmatrix}x_{ECEF}\\y_{ECEF}\\z_{ECEF}\end{bmatrix} = \begin{bmatrix}\cos\theta_{GMST} & -\sin\theta_{GMST} & 0\\\sin\theta_{GMST} & \cos\theta_{GMST} & 0\\0 & 0 & 1\end{bmatrix} \begin{bmatrix}x_{TEME}\\y_{TEME}\\z_{TEME}\end{bmatrix}$$

**What this does:**
- The rotation "undoes" Earth's spin since the TLE epoch
- Now both satellite and ground station are in the **same rotating frame**
- ECEF = "Earth-Centered Earth-Fixed" — rotates with Earth

**Analogy:** Imagine Earth is a spinning record. TEME freezes the record, but ECEF rotates with it. This rotation makes the coordinates "stick" to Earth's surface.

### Step 3: Convert Ground Station from WGS84 (Lat/Lon) to ECEF

Your ground station location is given in **geodetic coordinates** (latitude, longitude, altitude):
- Lat/Lon are angles measured from the equator and prime meridian
- Altitude is height above the surface

But we need it in **Cartesian coordinates** (x, y, z) to do geometry.

**The conversion formula:**

$$x = \left(N(\phi) + h\right) \cos(\phi) \cos(\lambda)$$

$$y = \left(N(\phi) + h\right) \cos(\phi) \sin(\lambda)$$

$$z = \left(N(\phi)(1 - e^2) + h\right) \sin(\phi)$$

Where:
- $\phi$ = latitude (in radians)
- $\lambda$ = longitude (in radians)
- $h$ = altitude in kilometers
- $N(\phi) = \frac{a}{\sqrt{1 - e^2 \sin^2(\phi)}}$ = radius of curvature (accounts for Earth's oblateness)
- $a = 6378.137$ km (Earth's equatorial radius)
- $e = 0.0818$ (Earth's eccentricity — how flattened it is)

**What this means:**
- We convert your location from "latitude/longitude" to "x,y,z distances from Earth's center"
- Now ground station and satellite are in the same coordinate system!

### Step 4: Calculate Relative Position (Vector from Station to Satellite)

$$\vec{\Delta} = \vec{r}_{sat,ECEF} - \vec{r}_{gs,ECEF} = \begin{bmatrix}\Delta x\\\Delta y\\\Delta z\end{bmatrix}$$

This vector $\vec{\Delta}$ points from your ground station **toward** the satellite, with magnitude equal to the distance between them.

### Step 5: Rotate ECEF → ENU and Calculate Elevation/Azimuth

Now we need angles we can actually understand: **elevation** (how high in the sky) and **azimuth** (compass direction).

**First, convert ECEF to ENU** (East-North-Up — local horizon frame):

$$\begin{bmatrix}e\\n\\u\end{bmatrix} = \begin{bmatrix}-\sin(\lambda) & \cos(\lambda) & 0\\-\sin(\phi)\cos(\lambda) & -\sin(\phi)\sin(\lambda) & \cos(\phi)\\\cos(\phi)\cos(\lambda) & \cos(\phi)\sin(\lambda) & \sin(\phi)\end{bmatrix} \begin{bmatrix}\Delta x\\\Delta y\\\Delta z\end{bmatrix}$$

Where the components mean:
- $e$ = how far east (+) or west (-) is the satellite
- $n$ = how far north (+) or south (-) is the satellite
- $u$ = how far up (+) or down (-) is the satellite

**Then calculate elevation and azimuth:**

$$\text{elevation} = \arctan2(u, \sqrt{e^2 + n^2}) \times \frac{180}{\pi}$$

$$\text{azimuth} = \arctan2(e, n) \times \frac{180}{\pi}$$

**What this means:**
- **Elevation:** Angle above the horizon (0° = horizon, 90° = directly overhead)
- **Azimuth:** Compass direction (0° = North, 90° = East, 180° = South, 270° = West)

This is what you would measure if you stood outside with a compass and a protractor!

---

## Part 4 — Pass Detection: When Is the Satellite Visible?

### The Visibility Question

A "pass" is a time period when a satellite is **visible** from your location. But what does "visible" mean?

**Real-world visibility requires:**
1. **Above the horizon** — The satellite is above the horizon line (elevation > 0°)
2. **High enough to see** — The satellite is typically at least 10° above horizon (accounts for buildings, hills, atmospheric distortion)
3. **Line of sight exists** — Nothing blocks the path between you and the satellite

### The Threshold-Based State Machine

We detect passes using a **state machine** with two states:

```
State: NOT_IN_PASS
    |
    | elevation rises above 10°
    ↓
State: IN_PASS
    |
    | elevation falls below 10°
    ↓
State: NOT_IN_PASS
```

### Algorithm: Step-by-Step Pass Detection

**Input:** Elevation values every 30 seconds for 48 hours

**Process:**

```
For each time t:
    elevation[t] = calculate elevation at time t
    
    If state == NOT_IN_PASS AND elevation[t] > 10°:
        # Pass is starting!
        state = IN_PASS
        pass_start_time = t (interpolated for precision)
        pass_max_elevation = elevation[t]
        
    Else if state == IN_PASS AND elevation[t] < 10°:
        # Pass is ending!
        state = NOT_IN_PASS
        pass_end_time = t (interpolated for precision)
        Record: (pass_start, pass_max, pass_end)
        
    Else if state == IN_PASS:
        # Still in pass, track maximum elevation
        if elevation[t] > pass_max_elevation:
            pass_max_elevation = elevation[t]
            pass_max_time = t
```

### Linear Interpolation for Precision

Since we only sample every 30 seconds, we miss the exact moment of crossing. We use **linear interpolation** to find it:

If at time $t_1$: elevation = 8° (below threshold)
And at time $t_2$: elevation = 12° (above threshold)

**The crossing time is:**
$$t_{\text{cross}} = t_1 + (t_2 - t_1) \cdot \frac{\text{threshold} - \text{elev}(t_1)}{\text{elev}(t_2) - \text{elev}(t_1)}$$

$$t_{\text{cross}} = t_1 + (30\text{ sec}) \cdot \frac{10 - 8}{12 - 8} = t_1 + 15\text{ sec}$$

This gives us **precise AOS/LOS times** rather than just "sometime in the next 30 seconds."

### Outputs Per Pass

For each detected pass, we record:
- **AOS (Acquisition of Signal):** When satellite rises above 10°
- **Rise azimuth:** Compass direction where it appears
- **Peak time:** When elevation is maximum
- **Peak elevation:** Maximum angle above horizon
- **Peak azimuth:** Compass direction at peak
- **LOS (Loss of Signal):** When satellite falls below 10°
- **Set azimuth:** Compass direction where it disappears
- **Duration:** How long the pass lasts (typically 5-15 minutes)

### Why This Method?

**Advantages:**
- **Simple:** Easy to understand and implement
- **Robust:** Only depends on sign changes (handles noisy data well)
- **Fast:** $O(N)$ time complexity — processes 48 hours in milliseconds
- **Transparent:** Easy to tune the threshold for different equipment
- **Flexible:** 5° threshold for radio, 10° for visual observation, 15° for clear line-of-sight

### How Can We Know Full Trajectory from 3 Lines?

This is a key insight: **The TLE doesn't tell us 3 sparse sample points. It describes the entire orbit.**

- **TLE = orbital parameters** (shape, size, position)
- **SGP4 = integrator** (applies physics forward in time)
- **Result = complete trajectory** within validity window

---

## Part 5 — ML Residual Correction: Improving Accuracy with Machine Learning

### The Problem: TLE Aging

Over time, TLEs become less accurate because:
- **Atmospheric drag** is unpredictable (depends on solar activity, not in the TLE)
- **Perturbations** accumulate (tidal forces, solar radiation pressure)
- **Orbit decay** is modeled as linear in TLE, but is actually non-linear

**Result:** A TLE that's 1 week old might have position errors of 1-5 km along the satellite's track.

### What Is a "Residual"?

A **residual** is the difference between:
- **Predicted position** from SGP4 using the old TLE
- **Actual position** from real tracking data

$$\text{residual} = \text{position}_{\text{actual}} - \text{position}_{\text{predicted}}$$

### Why Use Machine Learning?

Instead of updating the TLE (which requires ground observation), we train a neural network to **predict how wrong SGP4 will be** based on:
- How old the TLE is
- The orbital characteristics (eccentricity, inclination)
- The satellite's motion parameters (mean motion)

### Our FCN Architecture

Fully-Connected Network with:
```
Input layer (4 features)
    ↓
Hidden layer 1 (64 neurons)
    ↓
Hidden layer 2 (32 neurons)
    ↓
Hidden layer 3 (16 neurons)
    ↓
Output layer (1 neuron = predicted error in km)
```

**Why FCN?**
- Small feature set (only 4 numbers)
- Fast inference (real-time capable)
- Smooth output (residuals vary smoothly)
- Easy to train

---

## Part 6 — Outputs: What We Produce

For each successful prediction run, we generate:

### 1. Pass List

JSON format with:
- AOS time (Acquisition of Signal) — when satellite rises
- Peak elevation and time — highest point in sky
- LOS time (Loss of Signal) — when satellite sets
- Duration and azimuth angles

### 2. Elevation Plot

Graph showing elevation angle over time with the 10° visibility threshold marked.

### 3. Ground Track Plot

Map showing the satellite's ground path with your location and visible portions highlighted.

### 4. Statistics

- Total number of passes
- Best (highest elevation) pass
- TLE quality metric
- Coverage percentage

---

## Practical Notes: Making It All Work

### Accuracy Expectations

| Factor | Impact |
|--------|--------|
| TLE age | Most important — errors grow ~0.5 km/day |
| Ground station altitude | Minor — usually < 1% error |
| Step size | 30 sec adequate for ±2 min timing |

### Threshold Selection

- **5°:** Professional radio
- **10°:** Standard ham radio, visual with binoculars
- **15°:** Casual observation
- **20°:** Very conservative (buildings/terrain blocking)

### Updating Your TLE

- **Weekly minimum:** For basic predictions
- **Every 3-4 days:** For hobby observations  
- **Daily:** For critical operations

Get fresh TLEs from:
- [Celestrak](https://celestrak.org/)
- [Space-Track](https://www.space-track.org/)
- [N2YO](https://www.n2yo.com/)

---

## Summary

This entire pipeline calculates satellite positions using physics, transforms between coordinate systems, detects visibility windows, and optionally improves accuracy using machine learning — all in **seconds** for 48 hours of predictions.
