from setuptools import find_packages, setup
import os

package_name = 'chitti_hmi'

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
    description='Human-Machine Interface for Chitti robot',
    license='Apache License 2.0',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'touchscreen_interface_node = chitti_hmi.touchscreen_interface_node:main',
            'qr_generator_node = chitti_hmi.qr_generator_node:main',
            'voice_input_server_node = chitti_hmi.voice_input_server_node:main',
            'audio_output_manager_node = chitti_hmi.audio_output_manager_node:main',
            'user_session_manager_node = chitti_hmi.user_session_manager_node:main',
            'ui_state_manager_node = chitti_hmi.ui_state_manager_node:main',
        ],
    },
)
