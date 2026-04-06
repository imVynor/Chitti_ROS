#!/usr/bin/env python3

from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    
    return LaunchDescription([
        # ── GPS Driver (NEO-6M via UART) ──
        # Uses standard nmea_navsat_driver to capture NMEA strings from serial port
        Node(
            package='nmea_navsat_driver',
            executable='nmea_serial_driver',
            name='nmea_navsat_driver',
            output='screen',
            parameters=[{
                'port': '/dev/ttyUSB0',  # Update to your actual Pi serial port
                'baud': 9600,
                'frame_id': 'gps_link',
                'use_rostime': True
            }],
            remappings=[
                ('fix', '/fix')  # The standard expected by navsat_transform
            ]
        ),

        # ── IMU Driver (MPU9250 via I2C) ──
        # Generic placeholder for an I2C IMU node on the Pi
        Node(
            package='mpu9250driver',  # Or your chosen custom python package
            executable='mpu9250_node',
            name='mpu9250_driver',
            output='screen',
            parameters=[{
                'calibrate': True,
                'i2c_bus': 1,
                'i2c_address': 0x68
            }],
            remappings=[
                ('imu/data', '/imu/data')
            ]
        ),
    ])
