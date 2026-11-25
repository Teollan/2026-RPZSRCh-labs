"""
    ros2 launch lab2 cloud.launch.py
    ros2 topic echo /cloud --field width   # out-of-process subscriber will cause conversions
"""
from launch import LaunchDescription
from launch_ros.actions import ComposableNodeContainer
from launch_ros.descriptions import ComposableNode


def generate_launch_description():
    return LaunchDescription([
        ComposableNodeContainer(
            name='cloud_container',
            namespace='',
            package='rclcpp_components',
            executable='component_container',
            composable_node_descriptions=[
                ComposableNode(
                    package='lab2',
                    plugin='lab2::CloudPublisher',
                    name='cloud_publisher',
                    extra_arguments=[{'use_intra_process_comms': True}],
                ),
                ComposableNode(
                    package='lab2',
                    plugin='lab2::CloudSubscriber',
                    name='cloud_subscriber',
                    extra_arguments=[{'use_intra_process_comms': True}],
                ),
            ],
            output='screen',
        ),
    ])
