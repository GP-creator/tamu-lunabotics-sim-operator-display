"""ROS graph smoke-test world. Synthetic sensors; never a rover driver."""
import math
from collections import deque
from .navigation import wrap


def main(args=None):
    import rclpy
    from rclpy.node import Node
    from geometry_msgs.msg import PoseWithCovarianceStamped, TransformStamped, Twist
    from std_msgs.msg import Bool, Float32, Int32MultiArray, String
    from sensor_msgs.msg import PointCloud2
    from sensor_msgs_py import point_cloud2
    from std_msgs.msg import Header
    from tf2_ros import StaticTransformBroadcaster

    class GraphSITL(Node):
        def __init__(self):
            super().__init__('lunabotics_graph_sitl')
            self.declare_parameter('feedback_delay_steps',0)
            self.feedback_delay = self.get_parameter('feedback_delay_steps').value
            if type(self.feedback_delay) is not int or not 0 <= self.feedback_delay <= 5:
                raise ValueError('synthetic feedback delay must be in 0..5 ticks')
            self.feedback = deque()
            self.x,self.y,self.yaw = 1.1,2.2,0.
            self.left,self.right = 0.,0.
            self.mass,self.berm = 0.,0.
            self.tool,self.actuator = 'stop','raised'
            self.tool_elapsed = 0.
            self.cmd = Twist()
            self.cmd_time = -1e9
            self.estop = False
            self.phase = ''
            self.last_tick = self.clock()
            self.last_cloud = self.last_tag = -1e9
            self.obstacles = [(3.9,1.15,.2),(3.9,3.25,.2)]
            self.count_pub = self.create_publisher(Int32MultiArray,'/drive/encoders',10)
            self.cloud_pub = self.create_publisher(PointCloud2,'/unilidar/cloud',10)
            self.tag_pub = self.create_publisher(PoseWithCovarianceStamped,'/camera/pose',10)
            self.mass_pub = self.create_publisher(Float32,'/hopper/mass_kg',10)
            self.battery_pub = self.create_publisher(Float32,'/battery/voltage',10)
            self.estop_pub = self.create_publisher(Bool,'/safety/estop',10)
            self.actuator_pub = self.create_publisher(String,'/actuator/status',10)
            self.baseline_pub = self.create_publisher(Bool,'/berm/baseline_ready',10)
            self.berm_pub = self.create_publisher(Float32,'/berm/volume_l',10)
            self.create_subscription(Twist,'/autonomy/cmd_vel',self.drive,10)
            self.create_subscription(String,'/autonomy/tool_command',self.tool_cmd,10)
            self.create_subscription(String,'/autonomy/state',self.state,10)
            self.broadcaster = StaticTransformBroadcaster(self)
            tf = TransformStamped()
            tf.header.stamp = self.get_clock().now().to_msg()
            tf.header.frame_id,tf.child_frame_id = 'base_link','sim_lidar'
            tf.transform.rotation.w = 1.
            self.broadcaster.sendTransform(tf)
            self.create_timer(.05,self.step)

        def clock(self):
            return self.get_clock().now().nanoseconds*1e-9

        def drive(self,msg):
            self.cmd,self.cmd_time = msg,self.clock()

        def tool_cmd(self,msg):
            if msg.data != self.tool:
                self.tool_elapsed = 0.
            self.tool = msg.data

        def state(self,msg):
            self.phase = msg.data.split(':',1)[0]

        def scalar(self,publisher,type_,value):
            msg = type_()
            msg.data = value
            publisher.publish(msg)

        def scan(self,stamp):
            points = []
            for i in range(720):
                a = self.yaw+2*math.pi*i/720
                dx,dy = math.cos(a),math.sin(a)
                distance = 8.
                for ox,oy,radius in self.obstacles:
                    along = (ox-self.x)*dx+(oy-self.y)*dy
                    lateral2 = (ox-self.x)**2+(oy-self.y)**2-along**2
                    if along > 0 and lateral2 < radius**2:
                        intercept = along-math.sqrt(max(0.,radius**2-lateral2))
                        distance = min(distance,intercept)
                z = .2 if distance < 8. else -.2
                # Points are in base-aligned sensor frame, not map frame.
                relative = 2*math.pi*i/720
                points.append((distance*math.cos(relative),
                               distance*math.sin(relative),z))
            header = Header()
            header.stamp,header.frame_id = stamp,'sim_lidar'
            self.cloud_pub.publish(point_cloud2.create_cloud_xyz32(header,points))

        def step(self):
            now = self.clock()
            dt = max(0.,min(.1,now-self.last_tick))
            self.last_tick = now
            v,w = 0.,0.
            if not self.estop and now-self.cmd_time <= .25:
                v,w = self.cmd.linear.x,self.cmd.angular.z
            if not all(math.isfinite(x) for x in (v,w)) or abs(v) > .3 or abs(w) > 1.:
                self.estop = True
                v,w = 0.,0.
            self.yaw = wrap(self.yaw+w*dt)
            self.x += v*math.cos(self.yaw)*dt
            self.y += v*math.sin(self.yaw)*dt
            if (not .5 < self.x < 7.4 or not .5 < self.y < 3.9 or
                any(math.hypot(self.x-x,self.y-y) < .48+r
                    for x,y,r in self.obstacles)):
                self.estop = True
            self.left += (v-w*.25)*dt/(.2*math.pi)*1000
            self.right += (v+w*.25)*dt/(.2*math.pi)*1000
            counts = Int32MultiArray()
            counts.data = [round(self.left),round(self.right)]
            self.count_pub.publish(counts)
            self.tool_elapsed += dt
            if self.estop or self.tool == 'stop':
                if self.actuator not in ('raised','lowered'):
                    self.actuator = 'lowered' if self.actuator in ('lowering','digging') else 'raised'
            elif self.tool in ('lower','raise'):
                self.actuator = ('lowering' if self.tool == 'lower' else 'raising') \
                    if self.tool_elapsed < 2 else (
                    'lowered' if self.tool == 'lower' else 'raised')
            elif self.tool == 'dig':
                self.actuator = 'digging'
                # Accelerated synthetic material flow keeps the CI graph test
                # short; neither rate represents a measured rover mechanism.
                self.mass = min(25.6,self.mass+2.0*dt)
            elif self.tool == 'dump':
                self.actuator = 'dumping'
                removed = min(self.mass,4.0*dt)
                self.mass -= removed
                self.berm += removed/1.6
            stamp = self.get_clock().now().to_msg()
            self.scalar(self.mass_pub,Float32,float(self.mass))
            self.scalar(self.battery_pub,Float32,25.)
            self.scalar(self.estop_pub,Bool,self.estop)
            self.feedback.append(self.actuator)
            if len(self.feedback) > self.feedback_delay:
                self.scalar(self.actuator_pub,String,self.feedback.popleft())
            self.scalar(self.baseline_pub,Bool,True)
            if self.phase == 'verify':
                self.scalar(self.berm_pub,Float32,float(self.berm))
            if now-self.last_tag >= .5:
                msg = PoseWithCovarianceStamped()
                msg.header.stamp,msg.header.frame_id = stamp,'map'
                msg.pose.pose.position.x,msg.pose.pose.position.y = self.x,self.y
                msg.pose.pose.orientation.z = math.sin(self.yaw/2)
                msg.pose.pose.orientation.w = math.cos(self.yaw/2)
                msg.pose.covariance[0] = msg.pose.covariance[7] = .05**2
                msg.pose.covariance[35] = .05**2
                self.tag_pub.publish(msg)
                self.last_tag = now
            if now-self.last_cloud >= .25:
                self.scan(stamp)
                self.last_cloud = now
            if self.estop:
                self.get_logger().error('Synthetic collision/geofence/input fault',
                                        throttle_duration_sec=3.)

    rclpy.init(args=args)
    node = GraphSITL()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
