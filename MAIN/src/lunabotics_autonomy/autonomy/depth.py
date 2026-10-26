"""Depth-image parsing and conservative obstacle projection."""
import numpy as np


def depth_points(data, width, height, step, encoding, big_endian, k,
                 sample=12, near=0.15, far=3.0):
    """Return finite optical-frame XYZ points; caller must transform to base/map."""
    if encoding == '16UC1':
        dtype, scale = np.dtype('>u2' if big_endian else '<u2'), .001
    elif encoding == '32FC1':
        dtype, scale = np.dtype('>f4' if big_endian else '<f4'), 1.0
    else:
        raise ValueError('unsupported depth encoding')
    if (any(type(v) is not int or v <= 0 for v in (width,height,step,sample)) or
        not all(np.isfinite(v) for v in (near,far)) or not 0 < near < far or
        step < width * dtype.itemsize or len(data) < step*height):
        raise ValueError('truncated depth image')
    if len(k) != 9 or not all(np.isfinite(v) for v in k):
        raise ValueError('uncalibrated depth camera')
    fx, fy, cx, cy = float(k[0]), float(k[4]), float(k[2]), float(k[5])
    if fx <= 0 or fy <= 0:
        raise ValueError('uncalibrated depth camera')
    values = np.ndarray((height, width), dtype=dtype, buffer=bytes(data),
                        strides=(step, dtype.itemsize))
    out = []
    for v in range(sample//2, height, sample):
        for u in range(sample//2, width, sample):
            z = float(values[v, u]) * scale
            if np.isfinite(z) and near <= z <= far:
                out.append(((u-cx)*z/fx, (v-cy)*z/fy, z))
    return out
