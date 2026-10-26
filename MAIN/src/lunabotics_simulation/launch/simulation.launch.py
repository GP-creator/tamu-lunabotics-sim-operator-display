"""Gazebo Harmonic with measured simulated sensors and navigation-only autonomy."""
from pathlib import Path
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, OpaqueFunction, SetEnvironmentVariable
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration as L
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def bringup(context):
    share = Path(get_package_share_directory('lunabotics_simulation'))
    interfaces = Path(get_package_share_directory('lunabotics_interfaces'))
    gz_share = Path(get_package_share_directory('ros_gz_sim'))
    telemetry = Path(get_package_share_directory('lunabotics_telemetry'))
    headless = L('headless').perform(context).lower() in ('true','1')
    gz_args = ('-r -s --headless-rendering ' if headless else '-r ') + str(share/'worlds/arena.sdf')
    fixed = {'use_sim_time': True}
    return [
        IncludeLaunchDescription(PythonLaunchDescriptionSource(str(gz_share/'launch/gz_sim.launch.py')),
                                 launch_arguments={'gz_args': gz_args}.items()),
        Node(package='ros_gz_bridge', executable='parameter_bridge', output='screen',
             parameters=[fixed, {'config_file': str(interfaces/'config/gazebo_bridge.yaml')}]),
        Node(package='lunabotics_autonomy', executable='simulation_navigator', output='screen',
             parameters=[fixed, {'simulation_only': True,
                 'goal_x': ParameterValue(L('goal_x'), value_type=float),
                 'goal_y': ParameterValue(L('goal_y'), value_type=float)}]),
        Node(package='tf2_ros', executable='static_transform_publisher',
             arguments=['--x','0','--y','0','--z','.42','--frame-id','base_link','--child-frame-id','base_scan'], parameters=[fixed]),
        Node(package='tf2_ros', executable='static_transform_publisher',
             arguments=['--x','.25','--y','0','--z','.35','--frame-id','base_link','--child-frame-id','camera_link'], parameters=[fixed]),
        Node(package='tf2_ros', executable='static_transform_publisher',
             arguments=['--x','0','--y','0','--z','.25','--frame-id','base_link','--child-frame-id','imu_link'], parameters=[fixed]),
        IncludeLaunchDescription(PythonLaunchDescriptionSource(str(telemetry/'launch/telemetry.launch.py')),
             condition=IfCondition(L('telemetry'))),
    ]


def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument('headless', default_value='false'),
        DeclareLaunchArgument('telemetry', default_value='true'),
        DeclareLaunchArgument('goal_x', default_value='6.4'),
        DeclareLaunchArgument('goal_y', default_value='3.1'),
        SetEnvironmentVariable('HARDWARE_ENABLED','0'),
        OpaqueFunction(function=bringup),
    ])
