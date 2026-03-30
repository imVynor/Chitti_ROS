#!/usr/bin/env python3

from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node
import os
from ament_index_python.packages import get_package_share_directory


def generate_launch_description():
    hmi_dir = get_package_share_directory('chitti_hmi')
    bringup_dir = get_package_share_directory('chitti_bringup')
    
    return LaunchDescription([
        # Touchscreen interface
        Node(
            package='chitti_hmi',
            executable='touchscreen_interface_node',
            name='touchscreen_interface',
            parameters=[
                os.path.join(hmi_dir, 'config', 'ui_layout.yaml')
            ],
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
        
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                os.path.join(bringup_dir, 'launch', 'navigation.launch.py')
            )
        ),
    ])
