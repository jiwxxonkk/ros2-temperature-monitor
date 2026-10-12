from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    # monitor_node가 서비스 서버를 함께 담당합니다.
    # threshold_client는 사용자가 별도 터미널에서 필요할 때 실행합니다.
    return LaunchDescription([
        Node(
            package='sensor_monitor_py',
            executable='monitor_node',
            name='monitor_node',
            output='screen',
            parameters=[{'use_sim_time': False}],
        ),
        Node(
            package='sensor_monitor_py',
            executable='temperature_publisher',
            name='temperature_publisher',
            output='screen',
            parameters=[{'sensor_id': 'sensor_A', 'use_sim_time': False}],
        ),
    ])
