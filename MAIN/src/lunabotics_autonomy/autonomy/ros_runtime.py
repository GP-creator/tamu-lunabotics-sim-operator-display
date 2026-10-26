"""Keep repeated launch stop signals from interrupting ROS cleanup."""
import signal


def run_node(factory,args=None):
    import rclpy
    from rclpy.signals import SignalHandlerOptions
    stopping=False
    def request_stop(*_):
        nonlocal stopping
        stopping=True
    rclpy.init(args=args,signal_handler_options=SignalHandlerOptions.NO)
    previous={sig:signal.signal(sig,request_stop) for sig in (signal.SIGINT,signal.SIGTERM)}
    node=None
    try:
        node=factory()
        while not stopping and rclpy.ok():rclpy.spin_once(node,timeout_sec=.05)
    finally:
        try:
            try:
                if node is not None:node.destroy_node()
            finally:
                if rclpy.ok():rclpy.shutdown()
        finally:
            for sig,handler in previous.items():signal.signal(sig,handler)
