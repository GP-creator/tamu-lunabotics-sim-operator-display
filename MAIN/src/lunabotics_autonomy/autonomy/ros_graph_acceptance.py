"""End-to-end ROS graph acceptance for the isolated synthetic domain only."""
import os
import time
import json
import math


def main(args=None):
    if os.environ.get('ROS_DOMAIN_ID') != '213':
        raise SystemExit('Acceptance may only start the isolated ROS_DOMAIN_ID=213 graph')
    import rclpy
    from rclpy.node import Node
    from std_msgs.msg import Bool, Float32, String
    from nav_msgs.msg import OccupancyGrid, Odometry, Path
    from std_srvs.srv import Trigger

    class Acceptance(Node):
        def __init__(self):
            super().__init__('lunabotics_graph_acceptance')
            self.last_pose = self.last_grid = self.last_estop = -1e9
            self.state = 'disarmed'
            self.state_text = 'disarmed'
            self.cycles = 0
            self.path_seen = False
            self.free_seen = False
            self.volume = 0.
            self.estop = True
            self.last_pose_message = None
            self.last_grid_message = None
            self.create_subscription(Odometry,'/odometry/filtered',self.pose,10)
            self.create_subscription(OccupancyGrid,'/autonomy/obstacle_grid',
                self.grid,10)
            self.create_subscription(Path,'/autonomy/planned_path',
                lambda m:setattr(self,'path_seen',self.path_seen or bool(m.poses)),10)
            self.create_subscription(String,'/autonomy/state',self.status,10)
            self.create_subscription(Bool,'/safety/estop',self.safety,10)
            self.create_subscription(Float32,'/berm/volume_l',
                lambda m:setattr(self,'volume',float(m.data)),10)
            self.client = self.create_client(Trigger,'/autonomy/start')

        def clock(self):
            return self.get_clock().now().nanoseconds*1e-9

        def grid(self,msg):
            self.last_grid = self.clock()
            self.last_grid_message = msg
            self.free_seen |= any(v == 0 for v in msg.data)

        def pose(self,msg):
            self.last_pose,self.last_pose_message = self.clock(),msg

        def diagnostics(self):
            grid,odom = self.last_grid_message,self.last_pose_message
            result={'state':self.state_text,'cycles':self.cycles,'berm_l':self.volume}
            if odom:
                p,q=odom.pose.pose.position,odom.pose.pose.orientation
                result['pose']=[p.x,p.y,2*math.atan2(q.z,q.w)]
            if grid:
                result['grid']={'width':grid.info.width,'height':grid.info.height,
                    'resolution':grid.info.resolution,'data':list(grid.data)}
            return result

        def status(self,msg):
            phase = msg.data.split(':',1)[0]
            if phase == 'verify' and self.state != 'verify':
                self.cycles += 1
            self.state = phase
            self.state_text = msg.data

        def safety(self,msg):
            self.estop,self.last_estop = bool(msg.data),self.clock()

    rclpy.init(args=args)
    node = Acceptance()
    try:
        start = time.monotonic()
        while time.monotonic()-start < 15:
            rclpy.spin_once(node,timeout_sec=.1)
            now = node.clock()
            if (node.state == 'idle' and not node.estop and
                now-node.last_pose < .3 and now-node.last_grid < 1 and
                now-node.last_estop < .3 and node.free_seen):
                break
        else:
            raise RuntimeError('graph prerequisites not ready within 15 s')
        if not node.client.wait_for_service(timeout_sec=3):
            raise RuntimeError('start service missing')
        pending = node.client.call_async(Trigger.Request())
        while not pending.done():
            rclpy.spin_once(node,timeout_sec=.1)
        if not pending.result().success:
            raise RuntimeError('start rejected: '+pending.result().message)
        start = time.monotonic()
        while time.monotonic()-start < 750:
            rclpy.spin_once(node,timeout_sec=.1)
            if node.estop or node.state == 'fault':
                print('GRAPH_FAILURE_SNAPSHOT '+json.dumps(node.diagnostics()),flush=True)
                raise RuntimeError(f'graph fault: {node.state_text}; estop={node.estop}; '
                    f'cycles={node.cycles}; berm_l={node.volume:.2f}')
            if node.state == 'complete':
                if node.cycles < 2 or node.volume < 25 or not node.path_seen:
                    raise RuntimeError('incomplete cycles, berm, or path telemetry')
                print(f'PASS: {node.cycles} cycles, {node.volume:.2f} L berm, '
                      'live localization/grid/path; synthetic ROS graph only')
                return
        raise RuntimeError('graph mission timed out')
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
