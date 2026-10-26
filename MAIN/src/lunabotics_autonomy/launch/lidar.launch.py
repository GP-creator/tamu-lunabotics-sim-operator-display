"""Sensor-only Unitree SDK2 bringup with filtered public outputs."""
import ipaddress
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, OpaqueFunction, RegisterEventHandler, EmitEvent
from launch.event_handlers import OnProcessExit
from launch.events import Shutdown
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def start(context):
    get = lambda k: LaunchConfiguration(k).perform(context)
    local, remote = (str(ipaddress.IPv4Address(get(k))) for k in ('local_ip', 'lidar_ip'))
    if local == remote or any(ipaddress.IPv4Address(a).is_unspecified or
                             ipaddress.IPv4Address(a).is_multicast for a in (local, remote)):
        raise ValueError('LiDAR and local addresses must be distinct unicast addresses')
    ports = {k:int(get(k)) for k in ('local_port', 'lidar_port')}
    if not all(1 <= p <= 65535 for p in ports.values()):
        raise ValueError('invalid LiDAR UDP port')
    order = get('quaternion_order')
    if order not in ('xyzw', 'wxyz'):
        raise ValueError('invalid SDK quaternion order')
    driver = Node(package='unitree_lidar_ros2', executable='unitree_lidar_ros2_node',
        name='vinny_lidar_vendor', output='screen', parameters=[{
            'initialize_type':2, 'local_ip':local, 'lidar_ip':remote, **ports,
            'cloud_scan_num':18, 'use_system_timestamp':True,
            'range_min':0., 'range_max':50.,
            'cloud_frame':'unilidar_lidar', 'imu_frame':'unilidar_imu',
            'cloud_topic':'/vinny/lidar/raw_cloud', 'imu_topic':'/vinny/lidar/raw_imu'}],
        remappings=[('/tf','/vinny/lidar/raw_tf')])
    adapter = Node(package='lunabotics_autonomy', executable='lidar_health_node',
        output='screen', parameters=[{'quaternion_order':order}])
    handlers = [RegisterEventHandler(OnProcessExit(target_action=node,
        on_exit=[EmitEvent(event=Shutdown(reason='LiDAR process exited'))]))
        for node in (driver, adapter)]
    return [*handlers, adapter, driver]


def generate_launch_description():
    defaults = {'local_ip':'', 'lidar_ip':'', 'local_port':'6201',
                'lidar_port':'6101', 'quaternion_order':'xyzw'}
    return LaunchDescription([*[DeclareLaunchArgument(k, default_value=v)
        for k,v in defaults.items()], OpaqueFunction(function=start)])

