"""Observed obstacle and free-cell memory; all unseen cells remain unknown."""
import math
from .types import Config


def ray_cells(a, b):
    """Integer grid ray including both endpoints (Bresenham)."""
    x0, y0 = a
    x1, y1 = b
    dx, dy = abs(x1-x0), abs(y1-y0)
    sx, sy = (1 if x0 < x1 else -1), (1 if y0 < y1 else -1)
    error = dx - dy
    while True:
        yield x0, y0
        if (x0, y0) == (x1, y1):
            break
        twice = 2*error
        if twice > -dy:
            error -= dy
            x0 += sx
        if twice < dx:
            error += dx
            y0 += sy


class ObstacleMemory:
    def __init__(self, cfg: Config, ttl=3.0, free_ttl=30.0):
        if not all(math.isfinite(v) and v > 0 for v in (ttl,free_ttl)):
            raise ValueError('positive observation TTL required')
        self.cfg, self.ttl, self.free_ttl = cfg, ttl, free_ttl
        self.cells = {}  # cell -> timestamp of most recent hit
        self.free = {}   # cell -> timestamp observed clear along an actual beam
        self.misses = {} # hit cell -> independent clear scans, not beams

    def cell(self, xy):
        return int(xy[0] / self.cfg.cell), int(xy[1] / self.cfg.cell)

    def _inside(self, xy):
        return 0 <= xy[0] < self.cfg.width and 0 <= xy[1] < self.cfg.height

    def _clip_clear(self, origin, endpoint):
        """Keep only the measured portion of a ray inside the known arena."""
        if not self._inside(origin):
            return None
        if self._inside(endpoint):
            return endpoint
        dx,dy = endpoint[0]-origin[0],endpoint[1]-origin[1]
        scale = 1.0
        for component,delta,upper in ((origin[0],dx,self.cfg.width),
                                      (origin[1],dy,self.cfg.height)):
            if delta > 0:
                scale = min(scale,(upper-1e-6-component)/delta)
            elif delta < 0:
                scale = min(scale,-component/delta)
        if scale <= 0:
            return None
        return origin[0]+scale*dx,origin[1]+scale*dy

    def update(self, origin, points, now, clear_endpoints=()):
        """Integrate measured hit and no-hit beams from one scan.

        A clear endpoint is a measured ground/range return, never an invented
        maximum-range ray. All current hits win over clearing in this scan.
        """
        if not all(math.isfinite(v) for v in (*origin, now)) or not self._inside(origin):
            return
        source = self.cell(origin)
        # Clear old returns along measured beams, then mark *all* endpoints.
        # A distant return must not erase a nearer return in this same frame.
        endpoints = []
        clear = []
        for p in points:
            if not all(math.isfinite(v) for v in p):
                continue
            if not self._inside(p):
                clipped = self._clip_clear(origin,p)
                if clipped is not None:
                    clear.append(self.cell(clipped))
                continue
            endpoints.append(self.cell(p))
        current_hits = set(endpoints)
        for p in clear_endpoints:
            if all(math.isfinite(v) for v in p):
                clipped = self._clip_clear(origin,p)
                if clipped is not None:
                    clear.append(self.cell(clipped))
        scanned_clear = set()
        for end in endpoints + clear:
            for cell in ray_cells(source, end):
                if cell not in current_hits:
                    scanned_clear.add(cell)
        for cell in scanned_clear:
            if cell in self.cells:
                self.misses[cell] = self.misses.get(cell,0)+1
                if self.misses[cell] < 3:
                    continue
                self.cells.pop(cell,None)
                self.misses.pop(cell,None)
            self.free[cell] = now
        for end in current_hits:
            self.cells[end] = now
            self.free.pop(end, None)
            self.misses.pop(end,None)
        self.prune(now)

    def prune(self, now):
        self.cells = {key: t for key, t in self.cells.items()
                      if 0 <= now-t <= self.ttl}
        self.misses = {key:count for key,count in self.misses.items()
                       if key in self.cells}
        self.free = {key: t for key, t in self.free.items()
                     if 0 <= now-t <= self.free_ttl}

    def points(self, now):
        self.prune(now)
        return [((i+0.5)*self.cfg.cell, (j+0.5)*self.cfg.cell)
                for i, j in self.cells]

    def known_free(self, now):
        self.prune(now)
        return set(self.free).difference(self.cells)
