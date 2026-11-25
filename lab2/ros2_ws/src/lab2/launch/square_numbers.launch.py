"""
    ros2 launch lab2 square_numbers.launch.py
"""
from launch import LaunchDescription
from launch_ros.actions import ComposableNodeContainer, Node
from launch_ros.descriptions import ComposableNode


def generate_launch_description():
    return LaunchDescription([
        ComposableNodeContainer(
            name='square_numbers_container',
            namespace='',
            package='rclcpp_components',
            executable='component_container',
            arguments=['--executor-type', 'multi-threaded'],
            composable_node_descriptions=[
                ComposableNode(
                    package='lab2',
                    plugin='lab2::SquareNumbersActionServer',
                    name='square_numbers_action_server',
                    extra_arguments=[{'use_intra_process_comms': True}],
                ),
            ],
            output='screen',
        ),
        Node(
            package='lab2',
            executable='square_numbers_client',
            name='square_numbers_action_client',
            output='screen',
        ),
    ])
