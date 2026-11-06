#!/usr/bin/env python3
"""SIMULATION ONLY: relay camera images to a test-only topic for Fault B.

Run in a separate terminal while the normal simulation and Rosbridge remain running.
In a COPY of the LichtBlick layout, change BOTH camera_health script references
from /sim/camera/image to /fault_test/camera/image. Keep /tf as the heartbeat.
Stop this relay with Ctrl+C to simulate loss of the test camera feed; restart
it to verify recovery. This does NOT simulate physical camera hardware failure.
"""

import argparse
import os

import rclpy
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import Image


class CameraRelay(Node):
    def __init__(self, source, target):
        super().__init__('fault_test_camera_relay')
        self.frames = 0
        self.publisher = self.create_publisher(Image, target, qos_profile_sensor_data)
        self.subscription = self.create_subscription(
            Image, source, self.forward, qos_profile_sensor_data
        )
        self.timer = self.create_timer(5.0, self.report)
        self.get_logger().info(f'Relaying {source} -> {target} (Ctrl+C to stop)')

    def forward(self, msg):
        self.publisher.publish(msg)
        self.frames += 1

    def report(self):
        self.get_logger().info(f'Forwarded {self.frames} camera frames total')
        if self.frames == 0:
            self.get_logger().warning('No images received; check source topic and ROS_DOMAIN_ID')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', default='/sim/camera/image')
    parser.add_argument('--target', default='/fault_test/camera/image')
    args = parser.parse_args()

    if os.environ.get('HARDWARE_ENABLED') != '0':
        parser.error('Set HARDWARE_ENABLED=0 explicitly (simulation-only test).')
    if args.source == args.target:
        parser.error('Source and target topics must differ.')

    rclpy.init()
    node = CameraRelay(args.source, args.target)
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.get_logger().info(f'Stopped. Total forwarded: {node.frames} frames.')
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
