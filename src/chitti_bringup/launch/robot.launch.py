#!/usr/bin/env python3

from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, DeclareLaunchArgument
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory
import os


def generate_launch_description():
    use_sim_time = LaunchConfiguration('use_sim_time', default='false')
    
    bringup_dir = get_package_share_directory('chitti_bringup')
    hmi_dir = get_package_share_directory('chitti_hmi')
    
    return LaunchDescription([
        DeclareLaunchArgument(
            'use_sim_time',
            default_value='false',
            description='Use simulation (Gazebo) clock if true'
        ),
        
        # Core system state manager
        Node(
            package='chitti_system',
            executable='state_manager_node',
            name='state_manager',
            parameters=[{'use_sim_time': use_sim_time}],
            output='screen'
        ),
        
        # Network monitoring
        Node(
            package='chitti_system',
            executable='network_monitor_node',
            name='network_monitor',
            parameters=[{'use_sim_time': use_sim_time}],
            output='screen'
        ),
        
        # Battery monitoring
        Node(
            package='chitti_system',
            executable='battery_monitor_node',
            name='battery_monitor',
            parameters=[{'use_sim_time': use_sim_time}],
            output='screen'
        ),
        
        # Diagnostics
        Node(
            package='chitti_system',
            executable='diagnostics_node',
            name='diagnostics',
            parameters=[{'use_sim_time': use_sim_time}],
            output='screen'
        ),
        
        # Tour Manager
        Node(
            package='chitti_system',
            executable='tour_manager_node',
            name='tour_manager',
            parameters=[{'use_sim_time': use_sim_time}],
            output='screen'
        ),
    ])
