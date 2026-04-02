#!/usr/bin/env python3

from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    
    return LaunchDescription([
        # Placeholder for sensor drivers
        Node(
            package='chitti_system',
            executable='diagnostics_node',
            name='sensor_diagnostics',
            output='screen'
        ),
    ])
