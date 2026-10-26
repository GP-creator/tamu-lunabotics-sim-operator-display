"""Single TF authority for wheel odometry and fiducial map correction."""
import math
from .localization import WheelTagEstimator
from .ros_mission import yaw_from_quaternion, _stamp
from .types import Pose


def main(args=None):
    import rclpy
    from rclpy.node import Node
    from std_msgs.msg import Int32MultiArray
    from sensor_msgs.msg import Imu
    from geometry_msgs.msg import TransformStamped
    from geometry_msgs.msg import PoseWithCovarianceStamped
    from nav_msgs.msg import Odometry
    from tf2_ros import TransformBroadcaster

    class LocalizationNode(Node):
        def __init__(self):
            super().__init__('lunabotics_localization')
            for name,default in (('wheel_radius_m',0.),('wheel_track_m',0.),
                    ('ticks_per_revolution',0.),('max_wheel_speed_mps',0.),
                    ('arena_width',7.9),('arena_height',4.4),
                    ('require_imu',False),('imu_topic','/imu/data')):
                self.declare_parameter(name,default)
            p = lambda n:self.get_parameter(n).value
            self.estimator = None
            try:
                self.estimator = WheelTagEstimator(float(p('wheel_radius_m')),
                    float(p('wheel_track_m')),float(p('ticks_per_revolution')),
                    float(p('max_wheel_speed_mps')),float(p('arena_width')),
                    float(p('arena_height')))
            except ValueError as exc:
                self.get_logger().error(f'Localization inhibited: {exc}')
            self.require_imu = bool(p('require_imu'))
            self.imu_rate,self.imu_time = None,-1e9
            self.pub = self.create_publisher(Odometry,'/odometry/filtered',10)
            self.tf = TransformBroadcaster(self)
            self.create_subscription(Int32MultiArray,'/drive/encoders',self.encoders,10)
            self.create_subscription(PoseWithCovarianceStamped,'/camera/pose',self.tag,10)
            self.create_subscription(Imu,str(p('imu_topic')),self.imu,10)

        def clock(self):
            return self.get_clock().now().nanoseconds*1e-9

        def imu(self,msg):
            z = float(msg.angular_velocity.z)
            variance = msg.angular_velocity_covariance[8]
            stamp = _stamp(msg.header.stamp)
            if (math.isfinite(z) and math.isfinite(variance) and
                0 < variance <= .25 and abs(self.clock()-stamp) <= .2):
                self.imu_rate,self.imu_time = z,stamp

        def encoders(self,msg):
            if not self.estimator or len(msg.data) != 2:
                return
            now = self.clock()
            if not self.estimator.accept_counts(int(msg.data[0]),
                                                int(msg.data[1]),now):
                return
            if self.require_imu and (now-self.imu_time > .2 or
                    self.imu_rate is None or
                    abs(self.estimator.angular-self.imu_rate) > .6):
                self.estimator.fault = 'imu_wheel_disagreement_or_timeout'
                return
            self.publish(now)

        def tag(self,msg):
            if not self.estimator or msg.header.frame_id != 'map':
                return
            q,p = msg.pose.pose.orientation,msg.pose.pose.position
            cov = msg.pose.covariance
            if not all(math.isfinite(v) and 0 < v <= .09 for v in (cov[0],cov[7],cov[35])):
                return
            pose = Pose(float(p.x),float(p.y),yaw_from_quaternion(q))
            if self.estimator.accept_tag(pose,max(cov[0],cov[7]),cov[35],
                                         _stamp(msg.header.stamp),self.clock()):
                self.publish(self.clock())

        def publish(self,now):
            e = self.estimator
            if not e or e.fault or e.counts is None:
                return
            stamp = self.get_clock().now().to_msg()

            def transform(parent,child,pose):
                t = TransformStamped()
                t.header.stamp,t.header.frame_id,t.child_frame_id = stamp,parent,child
                t.transform.translation.x,t.transform.translation.y = pose.x,pose.y
                t.transform.rotation.z = math.sin(pose.yaw/2)
                t.transform.rotation.w = math.cos(pose.yaw/2)
                return t

            # This node is the sole owner of both links. No other odometry node
            # or camera detector may broadcast either transform.
            self.tf.sendTransform(transform('odom','base_link',e.odom))
            pose = e.pose
            if pose is None:
                return
            self.tf.sendTransform(transform('map','odom',e.alignment))
            xy_sigma,yaw_sigma = e.uncertainty
            msg = Odometry()
            msg.header.stamp,msg.header.frame_id,msg.child_frame_id = stamp,'map','base_link'
            msg.pose.pose.position.x,msg.pose.pose.position.y = pose.x,pose.y
            msg.pose.pose.orientation.z = math.sin(pose.yaw/2)
            msg.pose.pose.orientation.w = math.cos(pose.yaw/2)
            msg.pose.covariance[0] = msg.pose.covariance[7] = xy_sigma**2
            msg.pose.covariance[35] = yaw_sigma**2
            msg.twist.twist.linear.x,msg.twist.twist.angular.z = e.linear,e.angular
            msg.twist.covariance[0] = msg.twist.covariance[35] = .05**2
            self.pub.publish(msg)

    from .ros_runtime import run_node
    run_node(LocalizationNode,args)


if __name__ == '__main__':
    main()
