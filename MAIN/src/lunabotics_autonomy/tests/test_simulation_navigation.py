import math
import unittest
from autonomy.simulation_navigation import SimulationNavigator
from autonomy.types import Pose


def wall_scan(pose, circles=()):
    values = []
    for index in range(720):
        angle = pose.yaw-math.pi+index*(2*math.pi/719)
        dx, dy = math.cos(angle), math.sin(angle)
        distances = []
        for component, delta, upper in ((pose.x,dx,7.9),(pose.y,dy,4.4)):
            if delta > 1e-10: distances.append((upper-component)/delta)
            elif delta < -1e-10: distances.append(-component/delta)
        for x,y,r in circles:
            ux,uy = pose.x-x,pose.y-y
            b = ux*dx+uy*dy
            disc = b*b-(ux*ux+uy*uy-r*r)
            if disc >= 0 and -b-math.sqrt(disc) > 0:
                distances.append(-b-math.sqrt(disc))
        values.append(min(d for d in distances if d>0))
    return values


class SimulationNavigationTests(unittest.TestCase):
    def feed(self, core, pose, t, circles=()):
        self.assertTrue(core.odometry(pose,t))
        self.assertTrue(core.scan(wall_scan(pose,circles),-math.pi,
                                  2*math.pi/719,.08,12,t))

    def test_invalid_sensor_data_never_enables_motion(self):
        core=SimulationNavigator()
        self.assertEqual(core.tick(0),(0.,0.))
        core.odometry(Pose(1.2,1.2,0),1)
        self.assertFalse(core.scan([float('nan')]*720,-math.pi,.01,.08,12,1))
        self.assertEqual(core.tick(1),(0.,0.))
        self.assertFalse(core.odometry(Pose(float('nan'),1,0),1))

    def test_pause_dropout_and_clock_reset_stop(self):
        core=SimulationNavigator()
        self.feed(core,Pose(1.2,1.2,0),1)
        self.assertGreater(sum(abs(v) for v in core.tick(1)),0)
        self.assertEqual(core.tick(2),(0.,0.))
        self.feed(core,Pose(1.2,1.2,0),3)
        core.enabled=False
        self.assertEqual(core.tick(3),(0.,0.))
        core.enabled=True
        self.assertEqual(core.tick(.1),(0.,0.))
        self.assertIsNone(core.pose)

    def test_arrival_latches_zero_command(self):
        core=SimulationNavigator()
        self.feed(core,Pose(6.4,3.1,0),1)
        self.assertEqual(core.tick(1),(0.,0.))
        self.assertEqual(core.state,'complete')
        self.feed(core,Pose(6.0,3.1,0),2)
        self.assertEqual(core.tick(2),(0.,0.))

    def test_closed_loop_navigation_avoids_obstacles(self):
        core=SimulationNavigator()
        pose=Pose(1.2,1.2,0)
        obstacles=((3.6,2.1,.28),(5.7,1.2,.28))
        dt=.1
        for step in range(1600):
            t=step*dt
            self.feed(core,pose,t,obstacles)
            v,w=core.tick(t)
            self.assertLessEqual(abs(v),.35)
            self.assertLessEqual(abs(w),1.)
            for x,y,r in obstacles:
                self.assertGreater(math.hypot(pose.x-x,pose.y-y),r+.35)
            if core.complete:break
            pose=Pose(pose.x+v*math.cos(pose.yaw)*dt,
                      pose.y+v*math.sin(pose.yaw)*dt,
                      pose.yaw+w*dt)
        self.assertTrue(core.complete,(core.state,pose))


if __name__=='__main__':unittest.main()
