#!/usr/bin/env python3

import os

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node, SetParameter
from ament_index_python.packages import get_package_share_directory


def generate_launch_description():

    bringup_dir = get_package_share_directory('chitti_bringup')
    nav2_params_file = os.path.join(bringup_dir, 'config', 'nav2_params.yaml')
    rviz_config_file = os.path.join(bringup_dir, 'rviz', 'nav_debug.rviz')
    descr_dir = get_package_share_directory('chitti_description')
    ekf_config = os.path.join(bringup_dir, 'config', 'ekf.yaml')
    navsat_config = os.path.join(bringup_dir, 'config', 'navsat_transform.yaml')
    map_yaml_file = os.path.join(bringup_dir, 'maps', 'campus_map.yaml')

    ekf_node = Node(
        package='robot_localization', executable='ekf_node', name='ekf_filter_node',
        output='screen', parameters=[ekf_config]
    )

    navsat_node = Node(
        package='robot_localization', executable='navsat_transform_node', name='navsat_transform',
        output='screen', parameters=[navsat_config],
        remappings=[('gps/fix', '/fix'), ('odometry/filtered', '/odometry/filtered')]
    )

    map_to_odom_tf = Node(
        package='tf2_ros',
        executable='static_transform_publisher',
        name='map_to_odom_static_tf',
        arguments=[
            '--x', '0', '--y', '0', '--z', '0',
            '--roll', '0', '--pitch', '0', '--yaw', '0.0',
            '--frame-id', 'map', '--child-frame-id', 'odom'
        ]
    )

    return LaunchDescription([
        DeclareLaunchArgument(
            'use_fake_sensors',
            default_value='true',
            description='Publish fake GPS/IMU when physical sensors are unavailable',
        ),
        DeclareLaunchArgument(
            'is_simulation',
            default_value='false',
            description='Toggle simulation-only sensor behavior and robot description',
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
        SetParameter(name='use_sim_time', value=LaunchConfiguration('is_simulation')),
        ekf_node,
        navsat_node,
        map_to_odom_tf,
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
            remappings=[('cmd_vel', '/diff_drive_controller/cmd_vel')],
            parameters=[nav2_params_file]
        ),
        Node(
            package='nav2_planner',
            executable='planner_server',
            name='planner_server',
            condition=IfCondition(LaunchConfiguration('use_nav2_controller')),
            output='screen',
            parameters=[nav2_params_file]
        ),
        Node(
            package='nav2_behaviors',
            executable='behavior_server',
            name='behavior_server',
            condition=IfCondition(LaunchConfiguration('use_nav2_controller')),
            output='screen',
            parameters=[nav2_params_file]
        ),
        Node(
            package='nav2_bt_navigator',
            executable='bt_navigator',
            name='bt_navigator',
            condition=IfCondition(LaunchConfiguration('use_nav2_controller')),
            output='screen',
            parameters=[nav2_params_file]
        ),
        Node(
            package='nav2_map_server',
            executable='map_server',
            name='map_server',
            condition=IfCondition(LaunchConfiguration('use_nav2_controller')),
            output='screen',
            parameters=[{
                'yaml_filename': map_yaml_file,
                'topic_name': 'map',
                'frame_id': 'map'
            }]
        ),
        Node(
            package='nav2_lifecycle_manager',
            executable='lifecycle_manager',
            name='lifecycle_manager_navigation',
            condition=IfCondition(LaunchConfiguration('use_nav2_controller')),
            output='screen',
            parameters=[{
                'autostart': True,
                'node_names': [
                    'map_server',
                    'planner_server',
                    'controller_server',
                    'behavior_server',
                    'bt_navigator'
                ],
                'bond_timeout': 60.0
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
