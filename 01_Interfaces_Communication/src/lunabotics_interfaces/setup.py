from setuptools import setup
from glob import glob

setup(
    license='Apache-2.0',
    install_requires=[],
    name='lunabotics_interfaces', version="0.1.0", packages=['lunabotics_interfaces'],
    data_files=[
        ("share/ament_index/resource_index/packages", ["resource/lunabotics_interfaces"]),
        ("share/lunabotics_interfaces", ["package.xml", "README.md"]),
        ("share/lunabotics_interfaces/launch", glob("launch/*")),
        ("share/lunabotics_interfaces/config", glob("config/*")),
        ("share/lunabotics_interfaces/worlds", glob("worlds/*")),
        ("share/lunabotics_interfaces/layouts", glob("layouts/*")),
    ],
    entry_points={"console_scripts": []},
)
