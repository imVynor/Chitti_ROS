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
from launch.actions import IncludeLaunchDescription, TimerAction, DeclareLaunchArgument
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from ament_index_python.packages import get_package_share_directory

def generate_launch_description():
    bringup_dir = get_package_share_directory('chitti_bringup')
    gps_port = LaunchConfiguration('gps_port')
    motor_port = LaunchConfiguration('motor_port')
    
    is_sim_arg = DeclareLaunchArgument(
        'is_simulation',
        default_value='false',
        description='Toggle simulation (Fake sensors + map->odom static TF)'
    )
    is_sim = LaunchConfiguration('is_simulation')

    gps_port_arg = DeclareLaunchArgument(
        'gps_port',
        default_value='/dev/ttyACM0',
        description='Serial port for GPS device (for example /dev/ttyACM0 or /dev/ttyUSB0)'
    )

    motor_port_arg = DeclareLaunchArgument(
        'motor_port',
        default_value='/dev/ttyUSB1',
        description='Serial port for ESP32 motor controller (for example /dev/ttyUSB1)',
    )

    # ── 1. Launch Sensor Interfaces ──
    # Connects physical hardware pins to ROS topics
    sensors_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(os.path.join(bringup_dir, 'launch', 'sensors.launch.py')),
        launch_arguments={'gps_port': gps_port}.items()
    )
    
    # ── 2. Launch Motor Controllers & Robot State ──
    # Spawns diff_drive_controller and transforms mathematically
    hardware_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(os.path.join(bringup_dir, 'launch', 'hardware.launch.py')),
        launch_arguments={'use_sim': is_sim, 'motor_port': motor_port}.items()
    )
    
    # ── 3. Launch Navigation & Localization ──
    # Starts the EKF sensor fusion, NavSat, and higher-level pathing algorithms.
    nav_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(os.path.join(bringup_dir, 'launch', 'navigation.launch.py')),
        launch_arguments={
            'use_fake_sensors': is_sim,
            'is_simulation': is_sim
        }.items()
    )

    return LaunchDescription([
        is_sim_arg,
        gps_port_arg,
        motor_port_arg,
        # Start sensors instantly
        sensors_launch,
        # Boot hardware 2 seconds later to ensure clean state
        TimerAction(period=2.0, actions=[hardware_launch]),
        # Start navigation stack 10 seconds later, once TF tree and Odometry are populated
        TimerAction(period=10.0, actions=[nav_launch])
    ])
