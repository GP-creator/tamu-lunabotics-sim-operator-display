"""Depth survey of construction area. Requires surveyed map/camera TF and ROI."""
import math
from .berm import BermEstimator
from .depth import depth_points
from .orbbec import camera_topics
from .sensor_validation import fresh_frame, rigid_components
from .ros_mission import _stamp


def main(args=None):
    import rclpy
    from rclpy.node import Node
    from rclpy.duration import Duration
    from rclpy.time import Time
    from rclpy.qos import qos_profile_sensor_data
    from sensor_msgs.msg import CameraInfo, Image
    from std_msgs.msg import Bool, Float32, String
    from tf2_ros import Buffer, TransformListener

    class BermNode(Node):
        def __init__(self):
            super().__init__('lunabotics_berm_survey')
            for name, value in (('roi_x_min', 0.0), ('roi_y_min', 0.0),
                ('roi_x_max', 0.0), ('roi_y_max', 0.0), ('cell_m', 0.05),
                ('min_coverage', 0.8), ('vertical_error_m', 0.01),
                ('camera_name', 'camera')):
                self.declare_parameter(name,value)
            p = lambda name: self.get_parameter(name).value
            topics = camera_topics(p('camera_name'))
            self.estimator = None
            try:
                self.estimator = BermEstimator((float(p('roi_x_min')),
                    float(p('roi_y_min')),float(p('roi_x_max')),
                    float(p('roi_y_max'))),cell=float(p('cell_m')),
                    min_coverage=float(p('min_coverage')),
                    vertical_error_m=float(p('vertical_error_m')))
            except ValueError as exc:
                self.get_logger().error(f'Berm survey inhibited: {exc}')
            self.tf = Buffer()
            self.tf_listener = TransformListener(self.tf,self)
            self.phase = 'disarmed'
            self.info = None
            self.last_attempt = -1e9
            self.last_stamp = -1e9
            self.baseline_pub = self.create_publisher(Bool,'/berm/baseline_ready',10)
            self.volume_pub = self.create_publisher(Float32,'/berm/volume_l',10)
            self.create_subscription(String,'/autonomy/state',self.on_phase,10)
            self.create_subscription(CameraInfo,topics.depth_info,
                                     self.on_info,qos_profile_sensor_data)
            self.create_subscription(Image,topics.depth_image,
                                     self.on_depth,qos_profile_sensor_data)
            self.create_timer(.2,self.publish_ready)

        def clock(self):
            return self.get_clock().now().nanoseconds*1e-9

        def on_phase(self,msg):
            new_phase = msg.data.split(':',1)[0]
            if new_phase == 'verify' and self.phase != 'verify' and self.estimator:
                self.estimator.new_survey()
            self.phase = new_phase

        def on_info(self,msg):
            self.info = msg

        def on_depth(self,msg):
            if (not self.estimator or self.info is None or
                self.clock()-self.last_attempt < .4 or
                self.info.header.frame_id != msg.header.frame_id or
                (self.info.width,self.info.height) != (msg.width,msg.height) or
                self.phase not in ('disarmed','idle','verify')):
                return
            self.last_attempt = self.clock()
            try:
                stamp = _stamp(msg.header.stamp)
                if not fresh_frame(stamp,self.clock(),self.last_stamp):
                    return
                tf = self.tf.lookup_transform('map',msg.header.frame_id,
                    Time.from_msg(msg.header.stamp),timeout=Duration(seconds=.03))
                q,o = tf.transform.rotation,tf.transform.translation
                xx,yy,zz,ww = rigid_components(q,o)
                measured = []
                for x,y,z in depth_points(msg.data,msg.width,msg.height,msg.step,
                    msg.encoding,msg.is_bigendian,self.info.k,sample=4,
                    near=.15,far=4.0):
                    tx,ty,tz = 2*(yy*z-zz*y),2*(zz*x-xx*z),2*(xx*y-yy*x)
                    measured.append((x+ww*tx+(yy*tz-zz*ty)+o.x,
                                     y+ww*ty+(zz*tx-xx*tz)+o.y,
                                     z+ww*tz+(xx*ty-yy*tx)+o.z))
                if not measured:
                    return
                self.last_stamp = stamp
                self.estimator.observe(measured,empty=self.phase in ('disarmed','idle'))
                volume = self.estimator.lower_volume_l() if self.phase == 'verify' else None
                if volume is not None:
                    msg_out = Float32()
                    msg_out.data = float(volume)
                    self.volume_pub.publish(msg_out)
            except Exception as exc:
                self.get_logger().warn(f'Berm depth/TF rejected: {exc}',
                                       throttle_duration_sec=3.0)

        def publish_ready(self):
            out = Bool()
            out.data = bool(self.estimator and self.estimator.baseline_ready)
            self.baseline_pub.publish(out)

    from .ros_runtime import run_node
    run_node(BermNode,args)


if __name__ == '__main__':
    main()
