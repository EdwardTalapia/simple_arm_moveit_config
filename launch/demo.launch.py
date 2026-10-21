"""Start the simple arm: RViz, move_group and simulated controllers.

    ros2 launch simple_arm_moveit_config demo.launch.py
"""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node
from moveit_configs_utils import MoveItConfigsBuilder


def generate_launch_description():
    pkg = get_package_share_directory("simple_arm_moveit_config")

    moveit_config = (
        MoveItConfigsBuilder("simple_arm", package_name="simple_arm_moveit_config")
        .robot_description(file_path="config/simple_arm.urdf")
        .robot_description_semantic(file_path="config/simple_arm.srdf")
        .robot_description_kinematics(file_path="config/kinematics.yaml")
        .joint_limits(file_path="config/joint_limits.yaml")
        .trajectory_execution(file_path="config/moveit_controllers.yaml")
        .planning_pipelines(pipelines=["ompl"])
        .to_moveit_configs()
    )

    # Publishes the TF transforms of every link from /joint_states.
    robot_state_publisher = Node(
        package="robot_state_publisher",
        executable="robot_state_publisher",
        output="both",
        parameters=[moveit_config.robot_description],
    )

    # The planner: answers planning requests from RViz and Python scripts.
    move_group = Node(
        package="moveit_ros_move_group",
        executable="move_group",
        output="screen",
        parameters=[moveit_config.to_dict()],
    )

    # Simulated hardware plus the controllers that run on it.
    ros2_control_node = Node(
        package="controller_manager",
        executable="ros2_control_node",
        output="screen",
        parameters=[
            moveit_config.robot_description,
            os.path.join(pkg, "config", "ros2_controllers.yaml"),
        ],
    )
    spawners = [
        Node(
            package="controller_manager",
            executable="spawner",
            arguments=[name, "--controller-manager", "/controller_manager"],
        )
        for name in ["joint_state_broadcaster", "arm_controller"]
    ]

    rviz = Node(
        package="rviz2",
        executable="rviz2",
        output="log",
        arguments=["-d", os.path.join(pkg, "config", "moveit.rviz")],
        parameters=[
            moveit_config.robot_description,
            moveit_config.robot_description_semantic,
            moveit_config.robot_description_kinematics,
            moveit_config.planning_pipelines,
        ],
    )

    return LaunchDescription(
        [robot_state_publisher, move_group, ros2_control_node, *spawners, rviz]
    )
