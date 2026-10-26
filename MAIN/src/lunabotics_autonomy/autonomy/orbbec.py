"""Topic and frame names from the recovered Orbbec camera launch/source."""
from dataclasses import dataclass
import re


@dataclass(frozen=True)
class CameraTopics:
    color_image: str
    color_info: str
    color_frame: str
    depth_image: str
    depth_info: str


def camera_topics(camera_name='camera'):
    if not isinstance(camera_name, str) or not re.fullmatch(r'[A-Za-z][A-Za-z0-9_]*', camera_name):
        raise ValueError('camera_name must be a single ROS name')
    return CameraTopics(
        f'/{camera_name}/color/image_raw',
        f'/{camera_name}/color/camera_info',
        f'{camera_name}_color_optical_frame',
        f'/{camera_name}/depth/image_raw',
        f'/{camera_name}/depth/camera_info',
    )
