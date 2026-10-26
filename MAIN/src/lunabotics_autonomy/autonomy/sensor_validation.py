"""Reject stale frames and invalid TF values before accepting sensor health."""
import math


def fresh_frame(stamp, now, previous=-1e9, timeout=.5):
    return (all(math.isfinite(v) for v in (stamp,now,previous,timeout)) and
            timeout > 0 and previous < stamp and -.1 <= now-stamp <= timeout)


def rigid_components(rotation, translation):
    values = (rotation.x,rotation.y,rotation.z,rotation.w,
              translation.x,translation.y,translation.z)
    if not all(math.isfinite(v) for v in values):
        raise ValueError('nonfinite sensor transform')
    norm = math.hypot(*values[:4])
    if norm < 1e-9:
        raise ValueError('zero sensor quaternion')
    return tuple(v/norm for v in values[:4])
