#!/usr/bin/env python3

import os

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory


def generate_launch_description():

    bringup_dir = get_package_share_directory('chitti_bringup')
    nav2_params_file = os.path.join(bringup_dir, 'config', 'nav2_params.yaml')
    rviz_config_file = os.path.join(bringup_dir, 'rviz', 'nav_debug.rviz')

    return LaunchDescription([
        DeclareLaunchArgument(
            'use_fake_sensors',
            default_value='true',
            description='Publish fake GPS/IMU when physical sensors are unavailable',
        ),
        DeclareLaunchArgument(
            'use_nav2_controller',
            default_value='true',
            description='Start Nav2 FollowPath action server',
        ),
        DeclareLaunchArgument(
            'use_rviz',
            default_value='true',
            description='Start RViz with navigation debug config',
        ),
        Node(
            package='chitti_navigation',
            executable='fake_sensors',
            name='fake_sensors',
            condition=IfCondition(LaunchConfiguration('use_fake_sensors')),
            output='screen'
        ),
        Node(
            package='chitti_navigation',
            executable='destination_manager_node',
            name='destination_manager',
            output='screen'
        ),
        Node(
            package='chitti_navigation',
            executable='waypoint_manager_node',
            name='waypoint_manager',
            output='screen'
        ),
        Node(
            package='chitti_navigation',
            executable='osrm_path_node',
            name='osrm_path_node',
            output='screen'
        ),
        Node(
            package='chitti_navigation',
            executable='path_follower_node',
            name='path_follower_node',
            output='screen'
        ),
        Node(
            package='nav2_controller',
            executable='controller_server',
            name='controller_server',
            condition=IfCondition(LaunchConfiguration('use_nav2_controller')),
            output='screen',
            parameters=[nav2_params_file]
        ),
        Node(
            package='nav2_lifecycle_manager',
            executable='lifecycle_manager',
            name='lifecycle_manager_navigation',
            condition=IfCondition(LaunchConfiguration('use_nav2_controller')),
            output='screen',
            parameters=[{
                'autostart': True,
                'node_names': ['controller_server']
            }]
        ),
        Node(
            package='rviz2',
            executable='rviz2',
            name='rviz2_navigation',
            condition=IfCondition(LaunchConfiguration('use_rviz')),
            arguments=['-d', rviz_config_file],
            output='screen'
        ),
    ])
