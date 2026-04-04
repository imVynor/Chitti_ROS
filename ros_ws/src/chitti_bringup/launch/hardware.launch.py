"""
hardware.launch.py  –  Bring up the ros2_control stack for Chitti's motors.

Starts:
  1. robot_state_publisher  (publishes URDF on /robot_description topic)
  2. controller_manager     (subscribes to /robot_description, loads hardware plugin)
  3. diff_drive_controller   (subscribes to /cmd_vel, publishes /odom)
  4. joint_state_broadcaster (publishes /joint_states for TF)
"""

import os
from launch import LaunchDescription 
from launch.actions import TimerAction
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory
import xacro


def generate_launch_description():

    # ── Paths ──
    description_pkg = get_package_share_directory('chitti_description')
    control_pkg = get_package_share_directory('chitti_control')

    xacro_file = os.path.join(description_pkg, 'urdf', 'chitti.urdf.xacro')
    controllers_yaml = os.path.join(control_pkg, 'config', 'controllers.yaml')
                       
    # ── Process xacro → URDF string ──
    robot_description_content = xacro.process_file(xacro_file).toxml()

    # ── robot_state_publisher ──
    robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        parameters=[{
            'robot_description': robot_description_content,
        }],
        output='screen',
    )

    # ── controller_manager ──
    controller_manager = Node(
        package='controller_manager',
        executable='ros2_control_node',
        parameters=[controllers_yaml],
        output='screen',
    )

    # ── Spawn controllers ──
    # Note: Use a generous delay to ensure controller_manager is ready
    spawn_controllers = TimerAction(
        period=8.0,
        actions=[
            # Joint State Broadcaster
            Node(
                package='controller_manager',
                executable='spawner',
                arguments=[
                    'joint_state_broadcaster',
                    '--controller-manager-timeout', '10',
                ],
                output='screen',
            ),
            # Diff Drive Controller
            # Corrected syntax: pass remappings as a single string to --controller-ros-args
            Node(
                package='controller_manager',
                executable='spawner',
                arguments=[
                    'diff_drive_controller',
                    '--controller-manager-timeout', '10',
                    '--controller-ros-args', '--ros-args --remap /diff_drive_controller/cmd_vel:=/cmd_vel --remap /diff_drive_controller/odom:=/odom',
                ],
                output='screen',
            ),
        ],
    )

    return LaunchDescription([
        robot_state_publisher,
        controller_manager,
        spawn_controllers,
    ])
