# TLE Datasets

This folder contains unified Two-Line Element (TLE) sets organized by orbit type.

## Folder Structure

### `tle_leo/` – Low Earth Orbit (LEO) Satellites

Used by **v1.0, v1.1, v1.2** for amateur radio satellite pass prediction.

- **AO-91.txt** – FUNCUBE-1A (AO-91)
  - Satellite ID: 43017 (NORAD)
  - Type: LEO amateur radio transponder
  - Orbit: ~97.7° inclination, ~500 km altitude
  - Orbital Period: ~94 minutes (~15.3 revolutions/day)
  - Use case: Pass prediction for amateur radio operators
  - Contains: 400+ TLE snapshots spanning ~7 years (2017–2024)

- **AO-95.txt** – FUNCUBE-2 (AO-95)  
  - Satellite ID: 43770 (NORAD)
  - Type: LEO amateur radio transponder
  - Orbit: ~97.7° inclination, ~400 km altitude
  - Orbital Period: ~94 minutes (~14.9 revolutions/day)
  - Use case: Secondary LEO test satellite
  - Contains: 350+ TLE snapshots spanning ~6 years (2018–2024)

### `tle_geo/` – Geostationary Orbit (GEO) Satellites

Used by **v2.0** for ML-corrected pass prediction and training.

- **tle.txt** – Multiple GEO satellites
  - Contains: TDRS, FLTSATCOM, SKYNET and other geostationary satellites
  - Orbit: ~13° inclination, ~35,786 km altitude (geostationary)
  - Orbital Period: ~23h 56m (~1.0 revolutions/day)
  - Use case: Testing propagation on different orbit types, ML training
  - Note: These are **not stationary** (inclination ≠ 0°), so they drift

---

## Updating TLEs

### Adding New LEO TLE Data

```bash
# Append new TLE entries to the file (keep historical data)
cat new_tle_snapshot.txt >> data/tle_leo/AO-91.txt
```

### Adding New GEO Satellites

```bash
# Create new file or append to existing
echo "SATELLITE_NAME" >> data/tle_geo/satellite_name.txt
echo "1 12345U 00000A   ..." >> data/tle_geo/satellite_name.txt
echo "2 12345  13.0000 0.0000  ..." >> data/tle_geo/satellite_name.txt
```

---

## TLE Format Reference

Each TLE set consists of 3 lines:

```
NAME
1 NORAD_ID INTL_DESIGNATOR EPOCH ... MEAN_MOTION ...
2 NORAD_ID INCLINATION RAAN ECCENTRICITY ARG_PERIGEE MEAN_ANOMALY MEAN_MOTION ...
```

**Key Fields:**
- **NORAD_ID**: Satellite catalog number
- **EPOCH**: Launch date (YY DDD.DDDDD format)
- **MEAN_MOTION**: Revolutions per day (determines orbital period)
- **INCLINATION**: Orbit angle relative to equator (° 0-180)

---

## Using TLEs in Tests & Code

```python
from satcore import load_tle

# Load LEO satellite
name, line1, line2 = load_tle("data/tle_leo/AO-91.txt")

# Load GEO satellite
name, line1, line2 = load_tle("data/tle_geo/tle.txt")
```

---

## Data Sources

- **LEO (AO-91, AO-95)**: NORAD Two-Line Element Set
  - Last updated: December 2024
  - Historical snapshots for regression testing

- **GEO (TDRS, FLTSATCOM)**: NORAD Two-Line Element Set
  - Last updated: January 2025
  - Used for ML training and GEO propagation validation

---

## Notes

- All TLEs are in **UTC time**
- TLE accuracy degrades ~1-3 weeks after epoch
- For real-time predictions, refresh TLEs regularly from [CelesTrak](https://celestrak.com/) or [Space-Track.org](https://www.space-track.org/)
- Historical TLEs in these files are preserved for **regression testing and benchmarking**
