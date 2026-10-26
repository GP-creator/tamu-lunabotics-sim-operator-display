from setuptools import setup
from glob import glob

setup(
    license='Apache-2.0',
    install_requires=[],
    name='lunabotics_simulation', version="0.1.0", packages=['lunabotics_simulation'],
    data_files=[
        ("share/ament_index/resource_index/packages", ["resource/lunabotics_simulation"]),
        ("share/lunabotics_simulation", ["package.xml", "README.md"]),
        ("share/lunabotics_simulation/launch", glob("launch/*")),
        ("share/lunabotics_simulation/config", glob("config/*")),
        ("share/lunabotics_simulation/worlds", glob("worlds/*")),
        ("share/lunabotics_simulation/layouts", glob("layouts/*")),
    ],
    entry_points={"console_scripts": []},
)
