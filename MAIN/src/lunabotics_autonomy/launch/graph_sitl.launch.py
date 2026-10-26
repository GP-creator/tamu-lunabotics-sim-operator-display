"""Isolated ROS graph test; synthetic robot only, never starts a CDH driver."""
from launch import LaunchDescription
from launch.actions import SetEnvironmentVariable, DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def generate_launch_description():
    return LaunchDescription([
        SetEnvironmentVariable('ROS_DOMAIN_ID','213'),
        DeclareLaunchArgument('feedback_delay_steps',default_value='2'),
        Node(package='lunabotics_autonomy',executable='graph_sitl_node',
             parameters=[{'feedback_delay_steps':ParameterValue(
                 LaunchConfiguration('feedback_delay_steps'),value_type=int)}],output='screen'),
        Node(package='lunabotics_autonomy',executable='localization_node',
             parameters=[{'wheel_radius_m':.1,'wheel_track_m':.5,
                 'ticks_per_revolution':1000.,'max_wheel_speed_mps':1.,
                 'arena_width':7.9,'arena_height':4.4}],output='screen'),
        Node(package='lunabotics_autonomy',executable='mission_node',
             parameters=[{'armed':True,'geometry_confirmed':True,
                 'hopper_limit_l':16.,'bulk_density_kg_m3':1600.,
                 'target_l':25.,'per_cycle_l':14.,
                 'arena_width':7.9,'arena_height':4.4,'robot_radius':.48,
                 'dig_x':6.9,'dig_y':2.2,'dump_x':1.1,'dump_y':2.2,
                 'minimum_battery_v':20.}],output='screen'),
    ])
