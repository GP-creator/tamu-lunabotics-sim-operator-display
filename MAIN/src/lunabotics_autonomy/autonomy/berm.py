"""Conservative registered-depth volume above a surveyed empty surface."""
import math
from collections import defaultdict, deque
from statistics import median


class BermEstimator:
    def __init__(self, bounds, cell=0.05, min_coverage=0.8,
                 vertical_error_m=0.01, min_samples=2):
        x0,y0,x1,y1 = bounds
        if (not all(math.isfinite(v) for v in (*bounds,cell,min_coverage,vertical_error_m)) or
            type(min_samples) is not int or x1 <= x0 or y1 <= y0 or cell <= 0 or
            not 0 < min_coverage <= 1 or vertical_error_m < 0 or min_samples < 1):
            raise ValueError('measured berm ROI and survey resolution required')
        self.bounds = tuple(bounds)
        self.cell, self.coverage, self.error = cell,min_coverage,vertical_error_m
        self.min_samples = min_samples
        self.nx = math.ceil((x1-x0)/cell)
        self.ny = math.ceil((y1-y0)/cell)
        self.base = defaultdict(lambda: deque(maxlen=16))
        self.current = defaultdict(lambda: deque(maxlen=16))
        self.baseline = None

    def _cell(self, x, y):
        x0,y0,x1,y1 = self.bounds
        if not (x0 <= x < x1 and y0 <= y < y1):
            return None
        return (int((x-x0)/self.cell),int((y-y0)/self.cell))

    def observe(self, points, empty=False):
        target = self.base if empty and self.baseline is None else self.current
        if empty and self.baseline is not None:
            return
        for x,y,z in points:
            if not all(math.isfinite(v) for v in (x,y,z)):
                continue
            key = self._cell(x,y)
            if key is not None:
                target[key].append(z)
        if empty and self.baseline is None:
            qualifying = {k:median(v) for k,v in self.base.items()
                          if len(v) >= self.min_samples}
            if len(qualifying)/(self.nx*self.ny) >= self.coverage:
                self.baseline = qualifying

    @property
    def baseline_ready(self):
        return self.baseline is not None

    def new_survey(self):
        self.current.clear()

    def lower_volume_l(self):
        if not self.baseline_ready:
            return None
        measured = {k:median(v) for k,v in self.current.items()
                    if len(v) >= self.min_samples and k in self.baseline}
        if len(measured)/(self.nx*self.ny) < self.coverage:
            return None
        x0,y0,x1,y1 = self.bounds
        # Edge cells can cover less than cell**2; never count unobserved area.
        return 1000*sum(
            min(self.cell,x1-x0-key[0]*self.cell) *
            min(self.cell,y1-y0-key[1]*self.cell) *
            max(0.0,z-self.baseline[key]-self.error)
            for key,z in measured.items())
