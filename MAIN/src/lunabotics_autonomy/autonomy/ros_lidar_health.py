"""Publish validated LiDAR output and one consistent IMU/TF orientation."""
import json
import math
from .lidar_health import FrameGate, finite_cloud, normalized_xyzw


def main(args=None):
    import rclpy
    from rclpy.node import Node
    from rclpy.qos import qos_profile_sensor_data
    from sensor_msgs.msg import PointCloud2, Imu
    from std_msgs.msg import String
    from geometry_msgs.msg import TransformStamped
    from tf2_ros import TransformBroadcaster, StaticTransformBroadcaster

    class LidarHealth(Node):
        def __init__(self):
            super().__init__('vinny_lidar_health')
            self.declare_parameter('quaternion_order', 'xyzw')
            self.order = self.get_parameter('quaternion_order').value
            normalized_xyzw((0., 0., 0., 1.), self.order)
            self.gates = {k: FrameGate() for k in ('cloud', 'imu')}
            self.accepted = dict(cloud=0, imu=0)
            self.rejected = dict(cloud=0, imu=0)
            self.cloud_pub = self.create_publisher(PointCloud2, '/unilidar/cloud', 5)
            self.imu_pub = self.create_publisher(Imu, '/unilidar/imu', 20)
            self.health_pub = self.create_publisher(String, '/unilidar/health', 1)
            self.tf = TransformBroadcaster(self)
            self.static_tf = StaticTransformBroadcaster(self)
            # Factory IMU-to-LiDAR offset, not a measured rover mounting pose.
            t = TransformStamped()
            t.header.stamp = self.get_clock().now().to_msg()
            t.header.frame_id, t.child_frame_id = 'unilidar_imu', 'unilidar_lidar'
            t.transform.translation.x = .007698
            t.transform.translation.y = .014655
            t.transform.translation.z = -.00667
            t.transform.rotation.w = 1.
            self.static_tf.sendTransform(t)
            self.create_subscription(PointCloud2, '/vinny/lidar/raw_cloud',
                                     self.cloud, qos_profile_sensor_data)
            self.create_subscription(Imu, '/vinny/lidar/raw_imu',
                                     self.imu, qos_profile_sensor_data)
            self.create_timer(1., self.health)

        def now(self):
            return self.get_clock().now().nanoseconds * 1e-9

        def accept(self, key, msg, frame):
            s = msg.header.stamp
            valid = (msg.header.frame_id == frame and
                     0 <= s.nanosec < 1000000000 and
                     self.gates[key].accept(s.sec + s.nanosec * 1e-9, self.now()))
            if not valid:
                self.rejected[key] += 1
            return valid

        def cloud(self, msg):
            if not finite_cloud(msg):
                self.rejected['cloud'] += 1
                return
            if self.accept('cloud', msg, 'unilidar_lidar'):
                self.cloud_pub.publish(msg)
                self.accepted['cloud'] += 1

        def imu(self, msg):
            q = msg.orientation
            try:
                values = normalized_xyzw((q.x, q.y, q.z, q.w), self.order)
                v, a = msg.angular_velocity, msg.linear_acceleration
                if not all(math.isfinite(x) for x in (v.x,v.y,v.z,a.x,a.y,a.z)):
                    raise ValueError('nonfinite IMU vectors')
            except ValueError:
                self.rejected['imu'] += 1
                return
            if not self.accept('imu', msg, 'unilidar_imu'):
                return
            q.x, q.y, q.z, q.w = values
            self.imu_pub.publish(msg)
            t = TransformStamped()
            t.header.stamp = msg.header.stamp
            t.header.frame_id = 'unilidar_imu_initial'
            t.child_frame_id = 'unilidar_imu'
            t.transform.rotation = q
            self.tf.sendTransform(t)
            self.accepted['imu'] += 1

        def health(self):
            now = self.now()
            ages = {k:now-v.previous for k,v in self.gates.items()}
            msg = String()
            msg.data = json.dumps({'acquisition_ready':all(
                gate.fresh(now) for gate in self.gates.values()),
                'accepted':self.accepted, 'rejected':self.rejected,
                'age_s':ages, 'quaternion_order':self.order,
                'mounting_calibrated':False})
            self.health_pub.publish(msg)

    from .ros_runtime import run_node
    run_node(LidarHealth, args)


if __name__ == '__main__':
    main()

