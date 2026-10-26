import math
import struct
import unittest

from autonomy.lidar import scan_beams
from autonomy.navigation import plan, exploratory_route, segment_clear
from autonomy.navigation import wrap
from autonomy.occupancy import ObstacleMemory
from autonomy.mission import Mission
from autonomy.sitl import SIM_CONFIG
from autonomy.types import Pose,Observation,Phase


class LidarMappingTests(unittest.TestCase):
    def test_float32_range_limit_keeps_real_beams_without_extending_range(self):
        points=[struct.unpack('<fff',struct.pack('<fff',
            8*math.cos(i*2*math.pi/720),8*math.sin(i*2*math.pi/720),-.2))
            for i in range(720)]
        hits,clears,count=scan_beams(points,-.15,.65,8.)
        self.assertEqual(count,720)
        self.assertFalse(hits)
        self.assertTrue(all(math.hypot(x,y)<=8.+1e-12 for x,y in clears))
        self.assertEqual(scan_beams([(8.0001,0.,-.2)],-.15,.65,8.)[2],0)

    def test_ground_ray_clears_until_measured_endpoint(self):
        m = ObstacleMemory(SIM_CONFIG)
        m.update((1.1,2.2),[],1,clear_endpoints=[(6.9,2.2)])
        self.assertIn(m.cell((6.8,2.2)),m.known_free(1))
        self.assertNotIn(m.cell((7.0,2.2)),m.known_free(1))

    def test_hit_wins_and_farther_ground_does_not_clear_it(self):
        hit, clear, valid = scan_beams([(2,0,0.2),(3,0,-0.2)],
                                      -0.15,0.65,8)
        self.assertEqual((hit,clear,valid), ([(2,0)],[],2))
        m = ObstacleMemory(SIM_CONFIG)
        m.update((1.1,2.2),[(3.1,2.2)],1,
                 clear_endpoints=[(4.1,2.2)])
        self.assertNotIn(m.cell((3.1,2.2)),m.known_free(1))

    def test_unobserved_sector_stays_unknown(self):
        hit, clear, _ = scan_beams([(3,0,-0.2)],-.15,.65,8)
        self.assertEqual(hit,[])
        self.assertEqual(clear,[(3,0)])
        m = ObstacleMemory(SIM_CONFIG)
        m.update((1.1,2.2),[],1,clear_endpoints=[(4.1,2.2)])
        self.assertNotIn(m.cell((1.1,3.2)),m.known_free(1))

    def test_measured_rays_outside_arena_are_clipped(self):
        m = ObstacleMemory(SIM_CONFIG)
        m.update((1.1,2.2),[],1,clear_endpoints=[(10,2.2)])
        self.assertIn(m.cell((7.0,2.2)),m.known_free(1))

    def test_full_ground_scan_opens_plan_to_dig(self):
        origin = (1.1,2.2)
        cloud = [(8*math.cos(i*2*math.pi/1440),
                  8*math.sin(i*2*math.pi/1440),-0.2)
                 for i in range(1440)]
        hits,clear,_ = scan_beams(cloud,-.15,.65,8)
        m = ObstacleMemory(SIM_CONFIG)
        m.update(origin,[(origin[0]+x,origin[1]+y) for x,y in hits],1,
                 clear_endpoints=[(origin[0]+x,origin[1]+y) for x,y in clear])
        self.assertTrue(plan(Pose(*origin,0),SIM_CONFIG.dig,[],SIM_CONFIG,
                             m.known_free(1)))

    def test_occlusion_chooses_reachable_near_frontier(self):
        origin = (1.1,2.2)
        obstacles = [(3.9,1.15,.2),(3.9,3.25,.2)]
        cloud = []
        for i in range(720):
            a = 2*math.pi*i/720
            dx,dy = math.cos(a),math.sin(a)
            rng = 8.
            for ox,oy,radius in obstacles:
                along = (ox-origin[0])*dx+(oy-origin[1])*dy
                lateral2 = (ox-origin[0])**2+(oy-origin[1])**2-along**2
                if along > 0 and lateral2 < radius**2:
                    rng = min(rng,along-math.sqrt(max(0,radius**2-lateral2)))
            cloud.append((rng*dx,rng*dy,.2 if rng < 8 else -.2))
        hits,clears,_ = scan_beams(cloud,-.15,.65,8)
        m = ObstacleMemory(SIM_CONFIG)
        m.update(origin,[(origin[0]+x,origin[1]+y) for x,y in hits],1,
                 clear_endpoints=[(origin[0]+x,origin[1]+y) for x,y in clears])
        route,goal = exploratory_route(Pose(*origin,0),SIM_CONFIG.dig,
                                       m.points(1),SIM_CONFIG,m.known_free(1))
        self.assertTrue(route)
        self.assertIsNotNone(goal)
        previous = origin
        for waypoint in route:
            self.assertTrue(segment_clear(previous,waypoint,m.points(1),
                                          SIM_CONFIG,m.known_free(1)))
            previous = waypoint

    def test_closed_loop_mapped_drive_reaches_dig_without_collision(self):
        obstacles = [(3.9,1.15,.2),(3.9,3.25,.2)]
        pose = Pose(1.1,2.2,0.)
        memory = ObstacleMemory(SIM_CONFIG)
        mission = Mission(SIM_CONFIG)
        for step in range(800):
            now = step*.1
            if step%2 == 0:
                returns = []
                for i in range(720):
                    angle = pose.yaw+2*math.pi*i/720
                    dx,dy = math.cos(angle),math.sin(angle)
                    rng = 8.
                    for ox,oy,radius in obstacles:
                        along = (ox-pose.x)*dx+(oy-pose.y)*dy
                        lateral2 = (ox-pose.x)**2+(oy-pose.y)**2-along**2
                        if along > 0 and lateral2 < radius**2:
                            rng = min(rng,along-math.sqrt(max(0,radius**2-lateral2)))
                    relative = 2*math.pi*i/720
                    returns.append((rng*math.cos(relative),
                                    rng*math.sin(relative),.2 if rng < 8 else -.2))
                hits,clears,_ = scan_beams(returns,-.15,.65,8)
                def world(p):
                    c,s = math.cos(pose.yaw),math.sin(pose.yaw)
                    return pose.x+c*p[0]-s*p[1],pose.y+s*p[0]+c*p[1]
                memory.update((pose.x,pose.y),list(map(world,hits)),now,
                              clear_endpoints=list(map(world,clears)))
            obs = Observation(now=now,pose=pose,pose_time=now,camera_time=now,
                lidar_time=now,encoder_time=now,mass_time=now,actuator_time=now,
                battery_time=now,battery_v=25.,mass_kg=0.,pose_sigma=.05,
                actuator='raised',estop_time=now,baseline_ready=True,
                obstacles=memory.points(now),known_free=memory.known_free(now))
            out = mission.start(obs) if step == 0 else mission.tick(obs)
            self.assertNotEqual(out.phase,Phase.FAULT,out.fault)
            if out.phase == Phase.LOWER:
                return
            yaw = wrap(pose.yaw+out.angular*.1)
            pose = Pose(pose.x+out.linear*math.cos(yaw)*.1,
                        pose.y+out.linear*math.sin(yaw)*.1,yaw)
            self.assertTrue(all(math.hypot(pose.x-x,pose.y-y) >=
                SIM_CONFIG.robot_radius+r for x,y,r in obstacles))
        self.fail('mapped drive did not reach excavation goal')


if __name__ == '__main__':
    unittest.main()
