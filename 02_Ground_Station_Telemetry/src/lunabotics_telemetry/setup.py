from setuptools import setup
from glob import glob

setup(
    license='Apache-2.0',
    install_requires=[],
    name='lunabotics_telemetry', version="0.1.0", packages=['lunabotics_telemetry'],
    data_files=[
        ("share/ament_index/resource_index/packages", ["resource/lunabotics_telemetry"]),
        ("share/lunabotics_telemetry", ["package.xml", "README.md"]),
        ("share/lunabotics_telemetry/launch", glob("launch/*")),
        ("share/lunabotics_telemetry/config", glob("config/*")),
        ("share/lunabotics_telemetry/worlds", glob("worlds/*")),
        ("share/lunabotics_telemetry/layouts", glob("layouts/*")),
    ],
    entry_points={"console_scripts": []},
)
