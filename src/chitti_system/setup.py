from setuptools import find_packages, setup

package_name = 'chitti_system'

setup(
    name=package_name,
    version='0.0.1',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='IITGN Robotics',
    maintainer_email='dev@iitgn.ac.in',
    description='System management layer for Chitti robot',
    license='Apache License 2.0',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'state_manager_node = chitti_system.state_manager_node:main',
            'battery_monitor_node = chitti_system.battery_monitor_node:main',
            'diagnostics_node = chitti_system.diagnostics_node:main',
            'network_monitor_node = chitti_system.network_monitor_node:main',
            'tour_manager_node = chitti_system.tour_manager_node:main',
        ],
    },
)
