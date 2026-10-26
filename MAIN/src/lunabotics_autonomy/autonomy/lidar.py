"""Turn a 3-D cloud into conservative, measured planar hit/clear beams."""
import math


def scan_beams(points, min_z, max_z, max_range, ground_margin=0.25,
               bins=720):
    """Accept base-frame XYZ returns; ground returns clear only to their range.

    A nearer obstacle wins over a ground return in its angular sector. Returns
    above the obstacle band provide no evidence that the ground is traversable.
    """
    if not (all(math.isfinite(v) for v in (min_z,max_z,max_range,ground_margin)) and
            min_z < max_z and max_range > 0 and ground_margin > 0 and
            type(bins) is int and bins > 0):
        raise ValueError('invalid LiDAR filtering configuration')
    sectors = {}
    valid = 0
    for x, y, z in points:
        if not all(math.isfinite(v) for v in (x, y, z)):
            continue
        r = math.hypot(x, y)
        if r <= .08 or (r > max_range and not math.isclose(
                r,max_range,rel_tol=2e-7,abs_tol=1e-8)):
            continue
        if r > max_range:
            # PointCloud2 stores float32. Quantization at an exact range limit
            # must not discard half a scan; clamp the tiny excess to the limit.
            x,y = x*max_range/r,y*max_range/r
            r = max_range
        valid += 1
        sector = int(((math.atan2(y, x) + math.pi) / (2*math.pi)) * bins) % bins
        hit, ground = sectors.get(sector, (None, None))
        if min_z <= z <= max_z and (hit is None or r < hit[0]):
            hit = (r, x, y)
        elif min_z-ground_margin <= z < min_z and (ground is None or r > ground[0]):
            ground = (r, x, y)
        sectors[sector] = hit, ground
    hits, clears = [], []
    for hit, ground in sectors.values():
        if hit is not None:
            hits.append(hit[1:])
        if ground is not None and (hit is None or ground[0] < hit[0]):
            clears.append(ground[1:])
    return hits, clears, valid
