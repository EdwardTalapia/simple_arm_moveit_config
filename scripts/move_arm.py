#!/usr/bin/env python3
"""Move the simple arm with MoveItPy: a named pose, then a tip position.

Needs the arm running:
    ros2 launch simple_arm_moveit_config demo.launch.py
then:
    ros2 run simple_arm_moveit_config move_arm.py
"""

import time

from geometry_msgs.msg import Pose
from moveit.core.robot_state import RobotState
from moveit.planning import MoveItPy
from moveit_configs_utils import MoveItConfigsBuilder

config = (
    MoveItConfigsBuilder("simple_arm", package_name="simple_arm_moveit_config")
    .robot_description(file_path="config/simple_arm.urdf")
    .robot_description_semantic(file_path="config/simple_arm.srdf")
    .robot_description_kinematics(file_path="config/kinematics.yaml")
    .joint_limits(file_path="config/joint_limits.yaml")
    .trajectory_execution(file_path="config/moveit_controllers.yaml")
    .planning_pipelines(pipelines=["ompl"])
    .to_moveit_configs()
    .to_dict()
)

# MoveItPy's own settings: where to read joint states, and default planner.
config.update(
    {
        "planning_scene_monitor_options": {
            "name": "planning_scene_monitor",
            "robot_description": "robot_description",
            "joint_state_topic": "/joint_states",
            "attached_collision_object_topic": "/moveit_cpp/planning_scene_monitor",
            "publish_planning_scene_topic": "/moveit_cpp/publish_planning_scene",
            "monitored_planning_scene_topic": "/moveit_cpp/monitored_planning_scene",
            "wait_for_initial_state_timeout": 10.0,
        },
        "planning_pipelines": {"pipeline_names": ["ompl"]},
        "plan_request_params": {
            "planning_attempts": 1,
            "planning_pipeline": "ompl",
            "planning_time": 1.0,
            "max_velocity_scaling_factor": 0.5,
            "max_acceleration_scaling_factor": 0.5,
        },
    }
)


def move(robot, arm, label):
    plan = arm.plan()
    if plan:
        robot.execute("arm", plan.trajectory, blocking=True)
        print(f"Reached {label}", flush=True)
    else:
        print(f"Planning to {label} failed", flush=True)


def main():
    robot = MoveItPy(node_name="move_arm", config_dict=config)
    arm = robot.get_planning_component("arm")
    time.sleep(1.0)  # give MoveItPy a moment to receive /joint_states

    # 1. Named pose from the SRDF.
    arm.set_start_state_to_current_state()
    arm.set_goal_state(configuration_name="reach")
    move(robot, arm, "'reach'")

    # 2. Tip position in the world frame. A pose goal would also demand an
    # orientation the 3-joint arm can't match, so solve IK for the position
    # only (position_only_ik in kinematics.yaml), then plan to those joints.
    target = Pose()
    target.position.x = 0.3
    target.position.y = -0.3
    target.position.z = 0.4
    goal_state = RobotState(robot.get_robot_model())
    if goal_state.set_from_ik("arm", target, "tool0", 1.0):
        goal_state.update()
        arm.set_start_state_to_current_state()
        arm.set_goal_state(robot_state=goal_state)
        move(robot, arm, "tip position (0.3, -0.3, 0.4)")
    else:
        print("No IK solution for tip position", flush=True)

    # 3. Back home.
    arm.set_start_state_to_current_state()
    arm.set_goal_state(configuration_name="home")
    move(robot, arm, "'home'")


if __name__ == "__main__":
    main()
