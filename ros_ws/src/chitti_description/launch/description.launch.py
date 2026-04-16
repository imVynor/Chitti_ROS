import os
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import Command, LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue
from ament_index_python.packages import get_package_share_directory

def generate_launch_description():
    use_sim = LaunchConfiguration('use_sim')
    
    use_sim_arg = DeclareLaunchArgument(
        'use_sim',
        default_value='false',
        description='Use simulation (Gazebo) clock and plugins'
    )

    pkg_path = get_package_share_directory('chitti_description')
    xacro_file = os.path.join(pkg_path, 'urdf', 'chitti.urdf.xacro')
    robot_description = {'robot_description': ParameterValue(Command(['xacro ', xacro_file, ' use_sim:=', use_sim]), value_type=str)}

    robot_state_publisher_node = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        name='robot_state_publisher',
        output='screen',
        parameters=[robot_description]
    )

    # publishes dummy joint states for the wheels so tf2 knows they exist
    joint_state_publisher_node = Node(
        package='joint_state_publisher',
        executable='joint_state_publisher',
        name='joint_state_publisher',
        output='screen',
        parameters=[robot_description]
    )

    return LaunchDescription([
        use_sim_arg,
        robot_state_publisher_node,
        joint_state_publisher_node,
    ])
