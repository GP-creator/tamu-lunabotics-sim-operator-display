import dataclasses
import unittest
from autonomy.mission import Mission
from autonomy.sitl import SIM_CONFIG, scenario
from autonomy.types import Phase
from test_core import healthy


class TransitionTests(unittest.TestCase):
    def in_phase(self,phase):
        m=Mission(SIM_CONFIG);m.start(healthy(10.));m.phase=phase;m.phase_time=10.
        return m

    def test_delayed_digging_status_waits_stopped_then_raises(self):
        m=self.in_phase(Phase.RAISE)
        for t in (10.05,10.2,10.49):
            out=m.tick(healthy(t,actuator='digging'))
            self.assertEqual((out.phase,out.linear,out.angular,out.tool),(Phase.RAISE,0.,0.,'stop'))
        self.assertEqual(m.tick(healthy(10.5,actuator='lowered')).tool,'raise')
        self.assertEqual(m.tick(healthy(10.6,actuator='raising')).phase,Phase.RAISE)

    def test_wait_deadline_is_not_extended_by_fresh_old_feedback(self):
        m=self.in_phase(Phase.RAISE)
        for t in (10.1,10.3,10.49):m.tick(healthy(t,actuator='digging'))
        out=m.tick(healthy(10.51,actuator='digging'))
        self.assertEqual(out.fault,'wrong_raise_feedback');self.assertEqual(out.tool,'stop')

    def test_other_incompatible_feedback_still_faults_immediately(self):
        out=self.in_phase(Phase.RAISE).tick(healthy(10.05,actuator='dumping'))
        self.assertEqual(out.fault,'wrong_raise_feedback')

    def test_delayed_dump_stop_never_enables_driving(self):
        m=self.in_phase(Phase.TO_DIG)
        for t in (10.1,10.3,10.49):
            out=m.tick(healthy(t,actuator='dumping'))
            self.assertEqual((out.phase,out.linear,out.angular,out.tool),(Phase.TO_DIG,0.,0.,'stop'))
        self.assertEqual(m.tick(healthy(10.51,actuator='dumping')).fault,'tool_not_raised_for_travel')

    def test_invalid_transition_timeout_rejected(self):
        for bad in (0.,-1.,float('nan'),float('inf')):
            with self.assertRaises(ValueError):Mission(dataclasses.replace(SIM_CONFIG,actuator_transition_timeout=bad))

    def test_full_mission_with_delayed_feedback(self):
        self.assertEqual(scenario(feedback_delay_steps=2)['phase'],'complete')

    def test_excessive_feedback_delay_faults_stopped(self):
        result=scenario(feedback_delay_steps=8)
        self.assertEqual(result['phase'],'fault')
        self.assertEqual(result['fault'],'wrong_raise_feedback')
