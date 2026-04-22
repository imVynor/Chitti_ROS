#!/usr/bin/env python3

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, ExecuteProcess, IncludeLaunchDescription, TimerAction
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node, SetParameter
import os
from ament_index_python.packages import get_package_share_directory


def generate_launch_description():
    hmi_dir = get_package_share_directory('chitti_hmi')
    bringup_dir = get_package_share_directory('chitti_bringup')
    ros_gz_sim_dir = get_package_share_directory('ros_gz_sim')
    descr_dir = get_package_share_directory('chitti_description')
    web_app_path = os.path.join(hmi_dir, 'web_interface', 'app.py')

    web_host = LaunchConfiguration('web_host')
    web_port = LaunchConfiguration('web_port')
    start_web_interface = LaunchConfiguration('start_web_interface')
    start_gazebo_sim = LaunchConfiguration('start_gazebo_sim')
    use_rviz = LaunchConfiguration('use_rviz')
    use_nav2_controller = LaunchConfiguration('use_nav2_controller')
    use_fake_sensors = LaunchConfiguration('use_fake_sensors')
    is_simulation = LaunchConfiguration('is_simulation')
    start_hardware_control = LaunchConfiguration('start_hardware_control')
    motor_port = LaunchConfiguration('motor_port')

    web_server = ExecuteProcess(
        condition=IfCondition(start_web_interface),
        cmd=['python3', web_app_path, '--host', web_host, '--port', web_port],
        output='screen'
    )

    gazebo_sim = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(ros_gz_sim_dir, 'launch', 'gz_sim.launch.py')
        ),
        launch_arguments={'gz_args': '-r empty.sdf'}.items(),
        condition=IfCondition(start_gazebo_sim),
    )

    robot_description = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(descr_dir, 'launch', 'description.launch.py')
        ),
        launch_arguments={'use_sim': 'true'}.items(),
        condition=IfCondition(start_gazebo_sim),
    )

    spawn_robot = Node(
        package='ros_gz_sim',
        executable='create',
        arguments=['-topic', 'robot_description', '-name', 'chitti', '-z', '0.15'],
        output='screen',
        condition=IfCondition(start_gazebo_sim),
    )

    delayed_spawn = TimerAction(period=4.0, actions=[spawn_robot])

    hardware_control = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(bringup_dir, 'launch', 'hardware.launch.py')
        ),
        launch_arguments={'use_sim': start_gazebo_sim, 'motor_port': motor_port}.items(),
        condition=IfCondition(start_hardware_control),
    )

    navigation_stack = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(bringup_dir, 'launch', 'navigation.launch.py')
        ),
        launch_arguments={
            'use_rviz': use_rviz,
            'use_nav2_controller': use_nav2_controller,
            'use_fake_sensors': use_fake_sensors,
            'is_simulation': is_simulation,
        }.items()
    )

    clock_bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        arguments=['/clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock'],
        output='screen',
        condition=IfCondition(start_gazebo_sim),
    )
    
    return LaunchDescription([
        DeclareLaunchArgument(
            'start_web_interface',
            default_value='true',
            description='Start Flask-based web touchscreen/voice interface',
        ),
        DeclareLaunchArgument(
            'web_host',
            default_value='0.0.0.0',
            description='Host binding for web interface server',
        ),
        DeclareLaunchArgument(
            'web_port',
            default_value='5000',
            description='Port for web interface server',
        ),
        DeclareLaunchArgument(
            'start_gazebo_sim',
            default_value='false',
            description='Start Gazebo (GZ) simulation with Chitti robot model',
        ),
        DeclareLaunchArgument(
            'use_rviz',
            default_value='true',
            description='Start RViz navigation debug view',
        ),
        DeclareLaunchArgument(
            'use_nav2_controller',
            default_value='true',
            description='Start Nav2 controller server for path following',
        ),
        DeclareLaunchArgument(
            'use_fake_sensors',
            default_value='false',
            description='Use simulated GPS/IMU messages',
        ),
        DeclareLaunchArgument(
            'is_simulation',
            default_value='false',
            description='Use static map to odom transform for simulation',
        ),
        DeclareLaunchArgument(
            'start_hardware_control',
            default_value='true',
            description='Bring up ros2_control motor controllers',
        ),
        DeclareLaunchArgument(
            'motor_port',
            default_value='/dev/ttyUSB1',
            description='Serial port for ESP32 motor controller (for example /dev/ttyUSB1)',
        ),

        SetParameter('use_sim_time', start_gazebo_sim),

        web_server,
        gazebo_sim,
        clock_bridge,
        robot_description,
        delayed_spawn,
        hardware_control,

        # Touchscreen interface
        Node(
            package='chitti_hmi',
            executable='touchscreen_interface_node',
            name='touchscreen_interface',
            output='screen'
        ),
        
        # QR code generator
        Node(
            package='chitti_hmi',
            executable='qr_generator_node',
            name='qr_generator',
            parameters=[{
                'base_url': 'http://192.168.1.100:5000'
            }],
            output='screen'
        ),
        
        # Voice input server
        Node(
            package='chitti_hmi',
            executable='voice_input_server_node',
            name='voice_input_server',
            output='screen'
        ),
        
        # Audio output manager
        Node(
            package='chitti_hmi',
            executable='audio_output_manager_node',
            name='audio_output_manager',
            output='screen'
        ),
        
        # User session manager
        Node(
            package='chitti_hmi',
            executable='user_session_manager_node',
            name='session_manager',
            output='screen'
        ),
        
        # UI state manager
        Node(
            package='chitti_hmi',
            executable='ui_state_manager_node',
            name='ui_state_manager',
            output='screen'
        ),
        
        # NLP processor
        Node(
            package='chitti_interaction',
            executable='nlp_processor_node',
            name='nlp_processor',
            output='screen'
        ),
        
        # Intent classifier
        Node(
            package='chitti_interaction',
            executable='intent_classifier_node',
            name='intent_classifier',
            output='screen'
        ),
        
        # Response generator
        Node(
            package='chitti_interaction',
            executable='response_generator_node',
            name='response_generator',
            output='screen'
        ),
        
        # Text to speech
        Node(
            package='chitti_interaction',
            executable='text_to_speech_node',
            name='text_to_speech',
            output='screen'
        ),
        
        # Tour dialogue
        Node(
            package='chitti_interaction',
            executable='tour_dialogue_node',
            name='tour_dialogue',
            output='screen'
        ),
        
        # Delay navigation stack to let Gazebo and controller manager stabilize
        TimerAction(
            period=20.0,
            actions=[navigation_stack]
        ),
    ])
