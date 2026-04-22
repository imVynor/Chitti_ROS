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
from launch.actions import TimerAction, DeclareLaunchArgument
from launch.substitutions import Command, LaunchConfiguration
from launch.conditions import UnlessCondition
from launch_ros.actions import Node, SetParameter
from launch_ros.parameter_descriptions import ParameterValue
from ament_index_python.packages import get_package_share_directory


def generate_launch_description():

    use_sim = LaunchConfiguration('use_sim')
    motor_port = LaunchConfiguration('motor_port')
    
    use_sim_arg = DeclareLaunchArgument(
        'use_sim',
        default_value='false',
        description='Use simulation (Gazebo)'
    )

    motor_port_arg = DeclareLaunchArgument(
        'motor_port',
        default_value='/dev/ttyUSB1',
        description='Serial port for ESP32 motor controller (for example /dev/ttyUSB1)',
    )

    # ── Paths ──
    description_pkg = get_package_share_directory('chitti_description')
    control_pkg = get_package_share_directory('chitti_control')

    xacro_file = os.path.join(description_pkg, 'urdf', 'chitti.urdf.xacro')
    controllers_yaml = os.path.join(control_pkg, 'config', 'controllers.yaml')
                       
    # ── Process xacro → URDF string ──
    robot_description = {
        'robot_description': ParameterValue(
            Command([
                'xacro ', xacro_file,
                ' use_sim:=', use_sim,
                ' serial_port:=', motor_port,
            ]),
            value_type=str,
        )
    }

    # ── robot_state_publisher ──
    robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        parameters=[robot_description],
        output='screen',
    )

    # ── controller_manager ──
    controller_manager = Node(
        package='controller_manager',
        executable='ros2_control_node',
        parameters=[robot_description, controllers_yaml],
        output='screen',
        condition=UnlessCondition(use_sim),
    )

    # ── Spawn controllers sequentially to prevent service deadlocks in Jazzy ──
    # First spawn the Joint State Broadcaster after CM is up
    joint_state_spawner = Node(
        package='controller_manager',
        executable='spawner',
        arguments=[
            'joint_state_broadcaster',
            '--controller-manager-timeout', '20',
        ],
        output='screen',
        condition=UnlessCondition(use_sim),
    )
    
    spawn_joint_states = TimerAction(
        period=5.0,
        actions=[joint_state_spawner]
    )

    # Then spawn Diff Drive Controller ONCE Joint State Broadcaster finishes
    from launch.actions import RegisterEventHandler
    from launch.event_handlers import OnProcessExit
    
    diff_drive_spawner = Node(
        package='controller_manager',
        executable='spawner',
        arguments=[
            'diff_drive_controller',
            '--controller-manager-timeout', '20'
        ],
        output='screen',
        condition=UnlessCondition(use_sim),
    )
    
    spawn_diff_drive = RegisterEventHandler(
        event_handler=OnProcessExit(
            target_action=joint_state_spawner,
            on_exit=[diff_drive_spawner],
        )
    )

    return LaunchDescription([
        use_sim_arg,
        motor_port_arg,
        SetParameter(name='use_sim_time', value=use_sim),
        robot_state_publisher,
        controller_manager,
        spawn_joint_states,
        spawn_diff_drive,
    ])
