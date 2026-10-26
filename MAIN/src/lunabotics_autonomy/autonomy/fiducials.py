"""Camera marker geometry, isolated for deterministic tests."""
import math
import numpy as np


def valid_transform(value):
    t = np.asarray(value, dtype=float).reshape((4, 4))
    if (not np.isfinite(t).all() or
        not np.allclose(t[3], [0, 0, 0, 1], atol=1e-5) or
        not np.allclose(t[:3, :3].T @ t[:3, :3], np.eye(3), atol=1e-2) or
        np.linalg.det(t[:3, :3]) < 0.99):
        raise ValueError('invalid rigid transform')
    return t


def world_base_pose(world_tag, camera_tag, base_camera):
    """T_map_base = T_map_tag * inverse(T_camera_tag) * inverse(T_base_camera)."""
    transforms = [valid_transform(t) for t in (world_tag, camera_tag, base_camera)]
    a, b, c = transforms
    result = a @ np.linalg.inv(b) @ np.linalg.inv(c)
    rot = result[:3, :3]
    roll = math.atan2(rot[2, 1], rot[2, 2])
    pitch = math.atan2(-rot[2, 0], math.hypot(rot[2, 1], rot[2, 2]))
    if abs(roll) > 0.25 or abs(pitch) > 0.25:
        raise ValueError('nonplanar base estimate')
    return (float(result[0, 3]), float(result[1, 3]),
            math.atan2(rot[1, 0], rot[0, 0]))


def tag_object_corners(size_m):
    if not math.isfinite(size_m) or size_m <= 0:
        raise ValueError('measured marker side length required')
    s = size_m / 2
    # Corner order for OpenCV IPPE_SQUARE: top-left, top-right, bottom-right, bottom-left.
    return np.array([[-s, s, 0], [s, s, 0], [s, -s, 0], [-s, -s, 0]],
                    dtype=np.float32)


def estimate_camera_tag(objects,corners,camera_matrix,distortion,max_error):
    """Choose a finite, front-facing pose only after reprojection validation.

    OpenCV 4.5's square solver can return a high-error pose for an exactly
    frontal square. The iterative solver is checked by the same quality gate.
    """
    import cv2
    if not math.isfinite(max_error) or max_error <= 0:
        raise ValueError('positive finite reprojection limit required')
    best=None
    for flag in (cv2.SOLVEPNP_IPPE_SQUARE,cv2.SOLVEPNP_ITERATIVE):
        try:
            ok,rvec,tvec=cv2.solvePnP(objects,corners,camera_matrix,distortion,flags=flag)
            if not ok or not np.isfinite(rvec).all() or not np.isfinite(tvec).all() or tvec[2,0]<=0:
                continue
            predicted,_=cv2.projectPoints(objects,rvec,tvec,camera_matrix,distortion)
            error=float(np.sqrt(np.mean((predicted.reshape(4,2)-corners.reshape(4,2))**2)))
            if not math.isfinite(error) or error>max_error:
                continue
            transform=np.eye(4)
            transform[:3,:3]=cv2.Rodrigues(rvec)[0]
            transform[:3,3]=tvec.flatten()
            valid_transform(transform)
            if best is None or error<best[0]:best=(error,transform)
        except (cv2.error,ValueError,TypeError):
            continue
    return best
