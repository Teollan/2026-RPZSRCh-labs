"""
    ros2 launch lab2 data_filter.launch.py
    ros2 topic pub /lowercase_topic std_msgs/msg/String "{data: hello}"
    ros2 topic echo /uppercase_topic
"""
from launch import LaunchDescription
from launch_ros.actions import ComposableNodeContainer
from launch_ros.descriptions import ComposableNode


def generate_launch_description():
    return LaunchDescription([
        ComposableNodeContainer(
            name='data_filter_container',
            namespace='',
            package='rclcpp_components',
            executable='component_container',
            composable_node_descriptions=[
                ComposableNode(
                    package='lab2',
                    plugin='lab2::DataFilter',
                    name='data_filter',
                    parameters=[{
                        'qos_overrides./uppercase_topic.publisher.depth': 1,
                        'qos_overrides./uppercase_topic.publisher.reliability': 'reliable',
                        'qos_overrides./uppercase_topic.publisher.durability': 'transient_local',
                    }],
                    extra_arguments=[{'use_intra_process_comms': True}],
                ),
            ],
            output='screen',
        ),
    ])
