#!/usr/bin/env python3
"""SIMULATION ONLY: forward every second camera frame for bandwidth testing."""

import rclpy
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import Image


class CameraThrottle(Node):
    def __init__(self):
        super().__init__('camera_throttle_test')

        self.frames_received = 0
        self.frames_forwarded = 0

        self.publisher = self.create_publisher(
            Image, '/perf_test/camera/image_5fps', qos_profile_sensor_data
        )

        self.subscription = self.create_subscription(
            Image, '/sim/camera/image', self.forward, qos_profile_sensor_data
        )

        self.timer = self.create_timer(5.0, self.report)

    def forward(self, msg):
        self.frames_received += 1

        if self.frames_received % 2 == 0:
            self.publisher.publish(msg)
            self.frames_forwarded += 1

    def report(self):
        self.get_logger().info(
            f'Received: {self.frames_received}, '
            f'Forwarded: {self.frames_forwarded}'
        )


def main():
    rclpy.init()
    node = CameraThrottle()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()