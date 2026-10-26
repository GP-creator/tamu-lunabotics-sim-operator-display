"""Integrated synthetic mission; no ROS, serial ports, or physical rover."""
import math,struct,unittest
from collections import deque
from autonomy.types import Pose,Observation,Phase
from autonomy.sitl import SIM_CONFIG as cfg
from autonomy.mission import Mission
from autonomy.occupancy import ObstacleMemory
from autonomy.lidar import scan_beams
from autonomy.navigation import wrap, observed_footprint

def run(layout=1.15):
 obstacles=[(3.9,layout,.2),(3.9,4.4-layout,.2)];pose=Pose(1.1,2.2,0.);memory=ObstacleMemory(cfg);m=Mission(cfg)
 mass=berm=0.;actuator='raised';tool='stop';elapsed=0.;feedback=deque(['raised']);previous=None;trace=[]
 for tick in range(8000):
  now=tick*.1
  if tick%3==0:
   points=[]
   for i in range(720):
    a=pose.yaw+2*math.pi*i/720;dx,dy=math.cos(a),math.sin(a);r=8.
    for ox,oy,rad in obstacles:
     along=(ox-pose.x)*dx+(oy-pose.y)*dy;lat=(ox-pose.x)**2+(oy-pose.y)**2-along**2
     if along>0 and lat<rad**2:r=min(r,along-math.sqrt(max(0.,rad**2-lat)))
    b=2*math.pi*i/720;points.append(struct.unpack('<fff',struct.pack('<fff',r*math.cos(b),r*math.sin(b),.2 if r<8 else -.2)))
   h,cl,count=scan_beams(points,-.15,.65,8.)
   co,si=math.cos(pose.yaw),math.sin(pose.yaw)
   def world(p):return (pose.x+co*p[0]-si*p[1],pose.y+si*p[0]+co*p[1])
   memory.update((pose.x,pose.y),list(map(world,h)),now,clear_endpoints=list(map(world,cl)))
  feedback.append(actuator);reported=feedback.popleft()
  o=Observation(now=now,pose=pose,pose_time=now,camera_time=now,lidar_time=now,encoder_time=now,mass_time=now,actuator_time=now,battery_time=now,battery_v=25.,mass_kg=mass,pose_sigma=.05,actuator=reported,estop_time=now,baseline_ready=True,obstacles=memory.points(now),known_free=memory.known_free(now),berm_volume_l=berm,berm_time=now)
  out=m.start(o) if tick==0 else m.tick(o)
  if out.phase!=previous:trace.append(out.phase.value);previous=out.phase
  if out.phase in (Phase.COMPLETE,Phase.FAULT):return {'phase':out.phase,'fault':out.fault,'cycles':m.cycles,'berm_l':berm,'trace':trace,'seconds':now}
  if out.tool!=tool:elapsed=0.;tool=out.tool
  elapsed+=.1
  if tool=='stop':
   if actuator not in ('raised','lowered'):actuator='lowered' if actuator in ('lowering','digging') else 'raised'
  elif tool in ('lower','raise'):actuator=('lowering' if tool=='lower' else 'raising') if elapsed<2. else ('lowered' if tool=='lower' else 'raised')
  elif tool=='dig':actuator='digging';mass=min(25.6,mass+.2)
  elif tool=='dump':
   actuator='dumping';removed=min(mass,.4);mass-=removed;berm+=removed/1.6
  assert abs(out.linear)<=cfg.max_linear and abs(out.angular)<=cfg.max_angular
  yaw=wrap(pose.yaw+out.angular*.1);pose=Pose(pose.x+out.linear*math.cos(yaw)*.1,pose.y+out.linear*math.sin(yaw)*.1,yaw)
  assert all(math.hypot(pose.x-x,pose.y-y)>=cfg.robot_radius+r for x,y,r in obstacles)
 raise RuntimeError('not terminated')
class FullMappedMissionTests(unittest.TestCase):
 def test_two_cycles_with_float32_clouds_map_expiry_and_delayed_tools(self):
  result=run()
  self.assertEqual(result['phase'],Phase.COMPLETE,result)
  self.assertEqual(result['cycles'],2)
  self.assertGreaterEqual(result['berm_l'],25.)
  self.assertEqual(result['trace'].count('dig'),2)
  self.assertEqual(result['trace'].count('dump'),2)

if __name__=='__main__':unittest.main()
