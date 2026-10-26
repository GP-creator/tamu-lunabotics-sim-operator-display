"""One documented Rosbridge transport for LichtBlick; local-only by default."""
from pathlib import Path
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import AnyLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration


def generate_launch_description():
    source = Path(get_package_share_directory('rosbridge_server')) / 'launch/rosbridge_websocket_launch.xml'
    return LaunchDescription([
        DeclareLaunchArgument('address', default_value='127.0.0.1'),
        DeclareLaunchArgument('port', default_value='9090'),
        IncludeLaunchDescription(AnyLaunchDescriptionSource(str(source)),
            launch_arguments={
                'address': LaunchConfiguration('address'),
                'port': LaunchConfiguration('port'),
            }.items()),
    ])
