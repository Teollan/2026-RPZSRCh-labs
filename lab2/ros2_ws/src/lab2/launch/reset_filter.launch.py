"""
    ros2 launch lab2 reset_filter.launch.py
    ros2 service echo /reset_filter             # introspection events
"""
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    data_filter = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            PathJoinSubstitution([FindPackageShare('lab2'), 'launch', 'data_filter.launch.py'])
        )
    )

    return LaunchDescription([
        data_filter,
        Node(
            package='lab2',
            executable='reset_client',
            name='reset_client',
            output='screen',
        ),
    ])
