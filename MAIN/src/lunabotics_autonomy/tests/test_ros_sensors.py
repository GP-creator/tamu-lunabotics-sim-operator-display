"""Exercise sensor callbacks; fake middleware is not a real ROS integration test."""
import sys
import signal
import types
import unittest
from unittest.mock import Mock, patch
import numpy as np
from autonomy import ros_mission, ros_berm, ros_fiducials, ros_localization
from autonomy.types import Pose


def obj(**kw):return types.SimpleNamespace(**kw)
def stamp(t):return obj(sec=int(t),nanosec=round((t-int(t))*1e9))
def transform():return obj(transform=obj(rotation=obj(x=0.,y=0.,z=0.,w=1.),translation=obj(x=0.,y=0.,z=0.)))


class Node:
    overrides={}
    def __init__(self,*args):self.params={};self.now=10.;self.pubs={}
    def declare_parameter(self,k,v):self.params[k]=self.overrides.get(k,v)
    def get_parameter(self,k):return obj(value=self.params[k])
    def get_clock(self):return obj(now=lambda:obj(nanoseconds=int(self.now*1e9)))
    def get_logger(self):return Mock()
    def create_publisher(self,t,name,*a):
        self.pubs[name]=Mock();return self.pubs[name]
    def create_subscription(self,*a,**kw):pass
    def create_service(self,*a,**kw):pass
    def create_timer(self,*a,**kw):pass
    def destroy_node(self):pass


class SensorAdapterTests(unittest.TestCase):
    def run_node(self,module,scenario,overrides=None,cv=None):
        Node.overrides=overrides or {}
        names=('rclpy','rclpy.node','rclpy.signals','rclpy.qos','rclpy.duration','rclpy.time',
            'std_srvs','std_srvs.srv','std_msgs','std_msgs.msg','nav_msgs','nav_msgs.msg',
            'geometry_msgs','geometry_msgs.msg','sensor_msgs','sensor_msgs.msg',
            'sensor_msgs_py','sensor_msgs_py.point_cloud2','tf2_ros')
        modules={n:types.ModuleType(n) for n in names}
        for group,values in {'std_msgs.msg':'Bool Float32 Int32MultiArray String',
            'nav_msgs.msg':'Odometry OccupancyGrid Path',
            'geometry_msgs.msg':'PoseStamped PoseWithCovarianceStamped Twist TransformStamped',
            'sensor_msgs.msg':'PointCloud2 CameraInfo Image Imu','std_srvs.srv':'Trigger'}.items():
            for value in values.split():setattr(modules[group],value,obj)
        modules['rclpy'].init=lambda **kw:None;modules['rclpy'].shutdown=lambda:None
        def spin_once(node,timeout_sec):
            scenario(node);signal.raise_signal(signal.SIGINT);signal.raise_signal(signal.SIGINT)
        modules['rclpy'].spin_once=spin_once;modules['rclpy'].ok=lambda:True
        modules['rclpy.signals'].SignalHandlerOptions=obj(NO='none')
        modules['rclpy.node'].Node=Node
        modules['rclpy.qos'].qos_profile_sensor_data=object()
        modules['rclpy.duration'].Duration=lambda **kw:obj(**kw)
        modules['rclpy.time'].Time=obj(from_msg=lambda t:t)
        modules['tf2_ros'].Buffer=lambda:Mock(lookup_transform=lambda *a,**kw:transform())
        modules['tf2_ros'].TransformListener=lambda *a:None
        modules['tf2_ros'].TransformBroadcaster=Mock
        modules['sensor_msgs_py.point_cloud2'].read_points=lambda msg,**kw:msg.points
        if cv is not None:modules['cv2']=cv
        with patch.dict(sys.modules,modules):module.main()

    def mission_config(self):return {'hopper_limit_l':16.,'bulk_density_kg_m3':1600.,'require_depth':True}
    def image(self,t=10.,value=1000):
        return obj(header=obj(stamp=stamp(t),frame_id='depth'),width=12,height=12,step=24,
            encoding='16UC1',is_bigendian=False,data=np.full((12,12),value,dtype='<u2').tobytes())
    def info(self):return obj(header=obj(frame_id='depth'),width=12,height=12,k=[10.,0.,6.,0.,10.,6.,0.,0.,1.])

    def test_depth_rejects_empty_replayed_stale_and_invalid_transform(self):
        def scenario(n):
            n.pose_history.append((10.,Pose(1.,2.,0.)));n.depth_calibration(self.info())
            n.depth(self.image(value=0));self.assertEqual(n.obs.depth_time,-1e9)
            n.now+=.2;n.depth(self.image());self.assertEqual(n.obs.depth_time,10.)
            n.now+=.2;n.depth(self.image());self.assertEqual(n.obs.depth_time,10.)
            n.now+=.2;n.pose_history.append((10.6,Pose(1.,2.,0.)))
            bad=transform();bad.transform.translation.x=float('nan')
            n.tf.lookup_transform=lambda *a,**kw:bad
            n.depth(self.image(t=10.6));self.assertEqual(n.obs.depth_time,10.)
        self.run_node(ros_mission,scenario,self.mission_config())

    def test_lidar_requires_fresh_points_and_transform(self):
        def scenario(n):
            n.pose_history.append((10.,Pose(1.,2.,0.)))
            cloud=obj(header=obj(stamp=stamp(10.),frame_id='lidar'),points=[(2.,0.,.2)]*12)
            n.cloud(cloud);self.assertEqual(n.obs.lidar_time,10.)
            n.now+=.2;cloud.header.stamp=stamp(10.2);cloud.points=[];n.cloud(cloud)
            self.assertEqual(n.obs.lidar_time,10.)
            n.now+=.6;cloud.points=[(2.,0.,.2)]*12;n.cloud(cloud)
            self.assertEqual(n.obs.lidar_time,10.)
        self.run_node(ros_mission,scenario,self.mission_config())

    def test_berm_replay_cannot_create_a_new_measurement(self):
        def scenario(n):
            n.estimator=Mock();n.estimator.lower_volume_l.return_value=25.
            n.on_info(self.info());n.phase='verify';n.on_depth(self.image())
            self.assertEqual(n.estimator.observe.call_count,1)
            n.now+=.4;n.on_depth(self.image());self.assertEqual(n.estimator.observe.call_count,1)
            n.now+=.4;n.on_depth(self.image(t=1.));self.assertEqual(n.estimator.observe.call_count,1)
        self.run_node(ros_berm,scenario,{'roi_x_max':1.,'roi_y_max':1.})

    def test_bad_tag_json_or_missing_aruco_inhibits_without_crashing(self):
        for overrides in ({'tag_map_json':'{broken'}, {'tag_map_json':'[]'}, {}):
            self.run_node(ros_fiducials,lambda n:self.assertFalse(n.enabled),overrides,cv=obj())

    def test_localization_rejects_negative_or_nan_tag_covariance(self):
        def scenario(n):
            n.estimator=Mock()
            msg=obj(header=obj(frame_id='map',stamp=stamp(10.)),pose=obj(pose=obj(
                position=obj(x=1.,y=2.),orientation=obj(x=0.,y=0.,z=0.,w=1.)),covariance=[0.]*36))
            for value in (-1.,float('nan')):
                msg.pose.covariance[0]=value;msg.pose.covariance[7]=msg.pose.covariance[35]=.04
                n.tag(msg);n.estimator.accept_tag.assert_not_called()
        self.run_node(ros_localization,scenario)
