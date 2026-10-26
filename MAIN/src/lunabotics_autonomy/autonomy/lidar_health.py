"""Validation for the Unitree SDK2 output; no device or ROS imports."""
import math
import numpy as np


def normalized_xyzw(values, order='xyzw'):
    """Use the SDK's documented xyzw contract unless explicitly configured."""
    if order not in ('xyzw', 'wxyz') or len(values) != 4:
        raise ValueError('quaternion order must be xyzw or wxyz')
    q = tuple(float(v) for v in values)
    if not all(math.isfinite(v) for v in q):
        raise ValueError('nonfinite orientation')
    if order == 'wxyz':
        q = q[1:] + q[:1]
    norm = math.hypot(*q)
    if not .5 <= norm <= 1.5:
        raise ValueError('invalid orientation norm')
    return tuple(v / norm for v in q)


class FrameGate:
    def __init__(self, timeout=.5):
        if not math.isfinite(timeout) or not 0 < timeout <= 2:
            raise ValueError('invalid sensor timeout')
        self.timeout, self.previous, self.last_now = timeout, 0., None

    def accept(self, stamp, now):
        if not math.isfinite(now):
            return False
        previous_now, self.last_now = self.last_now, now
        if previous_now is not None and now < previous_now:
            # Reject the reset event, then require a new frame in the new clock.
            self.previous = 0.
            return False
        if not (math.isfinite(stamp) and math.isfinite(now) and
                stamp > 0 and stamp > self.previous and
                -.05 <= now - stamp <= self.timeout):
            return False
        self.previous = stamp
        return True

    def fresh(self, now):
        return (self.previous > 0 and math.isfinite(now) and
                0 <= now - self.previous <= self.timeout)


def finite_cloud(msg):
    """Check every XYZ value, respecting endian, row padding and field offsets."""
    if not (msg.width > 0 and msg.height > 0 and msg.point_step > 0 and
            msg.row_step >= msg.width * msg.point_step and
            len(msg.data) == msg.row_step * msg.height):
        return False
    endian = '>' if msg.is_bigendian else '<'
    for name in ('x', 'y', 'z'):
        fields = [f for f in msg.fields if f.name == name]
        if len(fields) != 1:
            return False
        f = fields[0]
        size = {7: 4, 8: 8}.get(f.datatype)
        if (f.count != 1 or size is None or f.offset < 0 or
                f.offset + size > msg.point_step):
            return False
        a = np.ndarray((msg.height, msg.width), dtype=endian + 'f' + str(size),
                       buffer=msg.data, offset=f.offset,
                       strides=(msg.row_step, msg.point_step))
        if not np.isfinite(a).all():
            return False
    return True

