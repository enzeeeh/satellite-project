"""
Pass detection utilities (stateful version for streaming updates).
- Maintain state across elevation samples
- Detect passes and interpolate AOS/LOS times
"""
from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import List, Optional


@dataclass
class PassEvent:
    startTime: datetime  # AOS (threshold crossing)
    maxTime: datetime
    endTime: datetime    # LOS (threshold crossing)
    maxElevationDeg: float


class PassDetector:
    """Stateful pass detector for streaming elevation data."""
    
    def __init__(self, threshold_deg: float = 10.0):
        self.threshold_deg = threshold_deg
        self.passes: List[PassEvent] = []
        self.in_pass = False
        self.aos_time: Optional[datetime] = None
        self.max_el = -1e9
        self.max_time: Optional[datetime] = None
        self.prev_time: Optional[datetime] = None
        self.prev_elev = -1e9
    
    def update(self, elev_deg: float, current_time: Optional[datetime] = None):
        """
        Update detector with new elevation sample.
        
        Args:
            elev_deg: Current elevation in degrees
            current_time: Current time (optional, can be None if called sequentially)
        """
        if current_time is None and self.prev_time is not None:
            # Assume 60-second steps if not provided
            current_time = self.prev_time + timedelta(seconds=60)
        
        if self.prev_time is None:
            # First sample
            self.prev_time = current_time
            self.prev_elev = elev_deg
            if elev_deg > self.threshold_deg:
                self.in_pass = True
                self.aos_time = current_time
                self.max_el = elev_deg
                self.max_time = current_time
            return
        
        # Check for upward crossing
        if not self.in_pass and self.prev_elev <= self.threshold_deg < elev_deg:
            self.in_pass = True
            self.aos_time = self._interp_time(
                self.prev_time, current_time, self.prev_elev, elev_deg, self.threshold_deg
            )
            self.max_el = elev_deg
            self.max_time = current_time
        
        # Update max elevation
        if self.in_pass and elev_deg > self.max_el:
            self.max_el = elev_deg
            self.max_time = current_time
        
        # Check for downward crossing
        if self.in_pass and self.prev_elev > self.threshold_deg >= elev_deg:
            los_time = self._interp_time(
                self.prev_time, current_time, self.prev_elev, elev_deg, self.threshold_deg
            )
            self.passes.append(PassEvent(
                startTime=self.aos_time,
                maxTime=self.max_time,
                endTime=los_time,
                maxElevationDeg=self.max_el
            ))
            self.in_pass = False
            self.aos_time = None
            self.max_el = -1e9
            self.max_time = None
        
        self.prev_time = current_time
        self.prev_elev = elev_deg
    
    def finalize(self):
        """Finalize any ongoing pass at end of data stream."""
        if self.in_pass and self.aos_time is not None:
            self.passes.append(PassEvent(
                startTime=self.aos_time,
                maxTime=self.max_time,
                endTime=self.prev_time,
                maxElevationDeg=self.max_el
            ))
            self.in_pass = False
    
    def get_passes(self) -> List[PassEvent]:
        """Get list of detected passes."""
        self.finalize()
        return self.passes
    
    @staticmethod
    def _interp_time(t0: datetime, t1: datetime, y0: float, y1: float, y: float) -> datetime:
        """Linearly interpolate time when y crosses target."""
        if y1 == y0:
            return t0
        frac = (y - y0) / (y1 - y0)
        frac = max(0.0, min(1.0, frac))
        return t0 + (t1 - t0) * frac
