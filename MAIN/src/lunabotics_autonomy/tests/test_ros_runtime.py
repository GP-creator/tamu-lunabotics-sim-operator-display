import signal
import sys
import types
import unittest
from unittest.mock import Mock,patch
from autonomy.ros_runtime import run_node


class RuntimeTests(unittest.TestCase):
    def test_repeated_interrupt_during_destroy_keeps_cleanup_running(self):
        ros=types.ModuleType('rclpy');signals=types.ModuleType('rclpy.signals')
        signals.SignalHandlerOptions=types.SimpleNamespace(NO='none')
        ros.init=Mock();ros.ok=lambda:True;ros.shutdown=Mock();node=Mock()
        def stop(*a,**kw):signal.raise_signal(signal.SIGINT);signal.raise_signal(signal.SIGINT)
        ros.spin_once=stop;node.destroy_node.side_effect=stop
        previous=signal.getsignal(signal.SIGINT)
        with patch.dict(sys.modules,{'rclpy':ros,'rclpy.signals':signals}):run_node(lambda:node)
        node.destroy_node.assert_called_once();ros.shutdown.assert_called_once()
        self.assertEqual(signal.getsignal(signal.SIGINT),previous)

    def test_constructor_failure_still_shuts_down_and_restores_signals(self):
        ros=types.ModuleType('rclpy');signals=types.ModuleType('rclpy.signals')
        signals.SignalHandlerOptions=types.SimpleNamespace(NO='none')
        ros.init=Mock();ros.ok=lambda:True;ros.shutdown=Mock()
        previous=signal.getsignal(signal.SIGINT)
        with patch.dict(sys.modules,{'rclpy':ros,'rclpy.signals':signals}),self.assertRaises(RuntimeError):
            run_node(Mock(side_effect=RuntimeError('bad startup')))
        ros.shutdown.assert_called_once();self.assertEqual(signal.getsignal(signal.SIGINT),previous)
