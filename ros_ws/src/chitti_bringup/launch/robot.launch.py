#!/usr/bin/env python3
"""
robot.launch.py - The Master Bringup File for Chitti

This single launch file initiates the entire real-world robot stack:
  1. Sensor Drivers (GPS, IMU)
  2. Hardware Control (Motor Output, TF, URDF)
  3. Navigation (EKF, OSRM, Path Follower, Nav2 Controller)
"""

import os
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, TimerAction
from launch.launch_description_sources import PythonLaunchDescriptionSource
from ament_index_python.packages import get_package_share_directory

def generate_launch_description():
    bringup_dir = get_package_share_directory('chitti_bringup')
    
    # ── 1. Launch Sensor Interfaces ──
    # Connects physical hardware pins to ROS topics
    sensors_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(os.path.join(bringup_dir, 'launch', 'sensors.launch.py'))
    )
    
    # ── 2. Launch Motor Controllers & Robot State ──
    # Spawns diff_drive_controller and transforms mathematically
    hardware_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(os.path.join(bringup_dir, 'launch', 'hardware.launch.py'))
    )
    
    # ── 3. Launch Navigation & Localization ──
    # Starts the EKF sensor fusion, NavSat, and higher-level pathing algorithms.
    # Note: We set use_fake_sensors=false because we are using real ones,
    # and is_simulation=false to let the EKF provide the dynamic map->odom TF.
    nav_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(os.path.join(bringup_dir, 'launch', 'navigation.launch.py')),
        launch_arguments={
            'use_fake_sensors': 'false',
            'is_simulation': 'false'  # Critical: Disables hardcoded position Locks
        }.items()
    )

    return LaunchDescription([
        # Start sensors instantly
        sensors_launch,
        # Boot hardware 2 seconds later to ensure clean state
        TimerAction(period=2.0, actions=[hardware_launch]),
        # Start navigation stack 10 seconds later, once TF tree and Odometry are populated
        TimerAction(period=10.0, actions=[nav_launch])
    ])
