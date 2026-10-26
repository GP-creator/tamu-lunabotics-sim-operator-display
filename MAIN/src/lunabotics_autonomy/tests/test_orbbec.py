import unittest
from autonomy.orbbec import camera_topics


class CameraTopicsTests(unittest.TestCase):
    def test_driver_namespace_and_frames(self):
        default = camera_topics()
        self.assertEqual(default.color_image,'/camera/color/image_raw')
        self.assertEqual(default.depth_info,'/camera/depth/camera_info')
        self.assertEqual(default.color_frame,'camera_color_optical_frame')
        other = camera_topics('front_camera')
        self.assertEqual(other.depth_image,'/front_camera/depth/image_raw')
        self.assertEqual(other.color_frame,'front_camera_color_optical_frame')

    def test_rejects_invalid_camera_names(self):
        for name in ('','/camera','front/camera','a b',None):
            with self.subTest(name=name),self.assertRaises(ValueError):
                camera_topics(name)
