from setuptools import setup

setup(
    license='Apache-2.0',
    install_requires=['numpy>=1.21,<3'],
    name='lunabotics_autonomy',
    version='0.3.1',
    packages=['autonomy'],
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/lunabotics_autonomy']),
        ('share/lunabotics_autonomy', ['package.xml', 'README.md']),
        ('share/lunabotics_autonomy/launch', ['launch/autonomy.launch.py']),
        ('share/lunabotics_autonomy/launch', ['launch/graph_sitl.launch.py']),
        ('share/lunabotics_autonomy/launch', ['launch/lidar.launch.py']),
    ],
    entry_points={'console_scripts': [
        'lunabotics-sitl = autonomy.sitl:main',
        'lunabotics-mission = autonomy.ros_mission:main',
        'lunabotics-fiducials = autonomy.ros_fiducials:main',
        'lunabotics-berm = autonomy.ros_berm:main',
        'mission_node = autonomy.ros_mission:main',
        'simulation_navigator = autonomy.ros_simulation_navigation:main',
        'localization_node = autonomy.ros_localization:main',
        'lidar_health_node = autonomy.ros_lidar_health:main',
        'graph_sitl_node = autonomy.ros_graph_sitl:main',
        'graph_acceptance = autonomy.ros_graph_acceptance:main',
        'fiducial_node = autonomy.ros_fiducials:main',
        'berm_node = autonomy.ros_berm:main',
    ]},
)


