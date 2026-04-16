from setuptools import find_packages, setup

package_name = 'chitti_navigation'

setup(
    name=package_name,
    version='0.0.1',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        ('share/' + package_name + '/maps', ['maps/iitg.graphml']),
    ],
    install_requires=[
        'setuptools',
        'networkx',
        'osmnx',
    ],
    zip_safe=True,
    maintainer='IITGN Robotics',
    maintainer_email='dev@iitgn.ac.in',
    description='Navigation layer for Chitti robot',
    license='Apache License 2.0',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'destination_manager_node = chitti_navigation.destination_manager_node:main',
            'waypoint_manager_node = chitti_navigation.waypoint_manager_node:main',
            'fake_sensors = chitti_navigation.fake_sensors:main',
            'osrm_path_node = chitti_navigation.osrm_path_node:main',
            'path_follower_node = chitti_navigation.path_follower_node:main',
        ],
    },
)
