"""Gazebo-only ROS adapter: isolated /sim topics, no hardware guard outputs."""
import json
import math
from .simulation_navigation import SimulationNavigator
from .types import Pose
from .ros_mission import yaw_from_quaternion
from .ros_runtime import run_node


def main(args=None):
    from rclpy.node import Node
    from rclpy.qos import qos_profile_sensor_data
    from geometry_msgs.msg import Twist, PoseStamped
    from nav_msgs.msg import Odometry, Path, OccupancyGrid
    from sensor_msgs.msg import LaserScan
    from std_msgs.msg import String
    from std_srvs.srv import Trigger

    class SimulationNode(Node):
        def __init__(self):
            super().__init__('simulation_navigator')
            self.declare_parameter('simulation_only', True)
            self.declare_parameter('goal_x', 6.4)
            self.declare_parameter('goal_y', 3.1)
            if (not self.get_parameter('simulation_only').value
                    or not self.get_parameter('use_sim_time').value):
                raise RuntimeError('simulation_only and use_sim_time must both be true')
            self.core = SimulationNavigator((self.get_parameter('goal_x').value,
                                              self.get_parameter('goal_y').value))
            self.command = self.create_publisher(Twist, '/sim/cmd_vel', 10)
            self.status = self.create_publisher(String, '/sim/status', 10)
            self.path_pub = self.create_publisher(Path, '/sim/planned_path', 10)
            self.grid_pub = self.create_publisher(OccupancyGrid, '/sim/obstacle_grid', 10)
            self.create_subscription(Odometry, '/sim/odom', self.odom,
                                     qos_profile_sensor_data)
            self.create_subscription(LaserScan, '/sim/scan', self.scan,
                                     qos_profile_sensor_data)
            self.create_service(Trigger, '/sim/pause', self.pause)
            self.create_service(Trigger, '/sim/start', self.start)
            self.create_timer(.05, self.step)
            self.last_grid = -1e9

        def odom(self, msg):
            if msg.header.frame_id != 'odom' or msg.child_frame_id != 'base_link':
                return
            p = msg.pose.pose.position
            stamp = msg.header.stamp.sec + msg.header.stamp.nanosec*1e-9
            self.core.odometry(Pose(p.x, p.y,
                              yaw_from_quaternion(msg.pose.pose.orientation)), stamp)

        def scan(self, msg):
            if msg.header.frame_id != 'base_scan':
                return
            stamp = msg.header.stamp.sec + msg.header.stamp.nanosec*1e-9
            self.core.scan(msg.ranges, msg.angle_min, msg.angle_increment,
                           msg.range_min, msg.range_max, stamp)

        def pause(self, request, response):
            self.core.enabled = False
            self.command.publish(Twist())
            response.success, response.message = True, 'Simulation paused'
            return response

        def start(self, request, response):
            self.core.enabled = True
            response.success, response.message = True, 'Simulation navigation enabled'
            return response

        def step(self):
            now = self.get_clock().now()
            t = now.nanoseconds*1e-9
            v, w = self.core.tick(t)
            command = Twist()
            command.linear.x, command.angular.z = v, w
            self.command.publish(command)
            pose = self.core.pose
            self.status.publish(String(data=json.dumps({
                'source': 'gazebo_simulation', 'state': self.core.state,
                'goal': self.core.goal, 'pose': None if pose is None else
                [pose.x, pose.y, pose.yaw], 'simulation_time_s': t,
                'pose_age_s': t-self.core.pose_time,
                'scan_age_s': t-self.core.scan_time})))
            if t-self.last_grid < .5:
                return
            self.last_grid = t
            path = Path()
            path.header.frame_id, path.header.stamp = 'odom', now.to_msg()
            for x, y in self.core.path:
                point = PoseStamped()
                point.header = path.header
                point.pose.position.x, point.pose.position.y = float(x), float(y)
                point.pose.orientation.w = 1.
                path.poses.append(point)
            self.path_pub.publish(path)
            cfg = self.core.cfg
            grid = OccupancyGrid()
            grid.header = path.header
            grid.info.resolution = cfg.cell
            grid.info.width = math.ceil(cfg.width/cfg.cell)
            grid.info.height = math.ceil(cfg.height/cfg.cell)
            grid.info.origin.orientation.w = 1.
            occupied = self.core.memory.cells
            free = self.core.memory.known_free(t)
            grid.data = [100 if (x, y) in occupied else 0 if (x, y) in free else -1
                         for y in range(grid.info.height)
                         for x in range(grid.info.width)]
            self.grid_pub.publish(grid)

        def destroy_node(self):
            self.command.publish(Twist())
            return super().destroy_node()

    run_node(SimulationNode, args)
