#!/usr/bin/env python3
"""Move the simple arm through a target or chain from a YAML file.

Needs the arm running:
    ros2 launch simple_arm_moveit_config demo.launch.py
then run a chain or single target from config/waypoints.yaml:
    ros2 run simple_arm_moveit_config move_to.py circle
    ros2 run simple_arm_moveit_config move_to.py side
or from your own file:
    ros2 run simple_arm_moveit_config move_to.py circle --file my_points.yaml
"""

import argparse
import math
import os
import sys
import time

import numpy as np
import yaml
from ament_index_python.packages import get_package_share_directory
from geometry_msgs.msg import Pose
from moveit.core.robot_state import RobotState
from moveit.planning import MoveItPy
from rclpy.utilities import remove_ros_args

# Same MoveItPy config and plan/execute helper as move_arm.py (installed
# next to this script, so it imports directly).
from move_arm import config, move

DEFAULT_FILE = os.path.join(
    get_package_share_directory("simple_arm_moveit_config"), "config", "waypoints.yaml"
)


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("name", nargs="?", help="chain or target to run")
    parser.add_argument("--file", default=DEFAULT_FILE, help="waypoints YAML file")
    parser.add_argument("--list", action="store_true", help="list chains and targets")
    return parser.parse_args(remove_ros_args(sys.argv)[1:])


def circle_points(center, radius, plane="yz", points=16, laps=1):
    """Tip positions around a circle, ending back where it started."""
    cx, cy, cz = center
    out = []
    for i in range(points * laps + 1):
        a = 2 * math.pi * i / points
        u, v = radius * math.cos(a), radius * math.sin(a)
        if plane == "xy":
            out.append((cx + u, cy + v, cz))
        elif plane == "xz":
            out.append((cx + u, cy, cz + v))
        elif plane == "yz":
            out.append((cx, cy + u, cz + v))
        else:
            raise ValueError(f"circle plane must be xy, xz or yz, not {plane!r}")
    return out


def expand(step, targets):
    """Turn one chain step into a list of (label, target dict)."""
    if isinstance(step, str):
        if step not in targets:
            raise ValueError(f"unknown target {step!r}")
        return [(f"'{step}'", targets[step])]
    if "circle" in step:
        return [
            (f"circle point {i}", {"position": p})
            for i, p in enumerate(circle_points(**step["circle"]))
        ]
    return [(str(step), step)]


def go_to(robot, arm, goal_state, label, target):
    """Plan and move to one target. goal_state is reused across calls, so
    each IK solve starts from the last solution and the arm doesn't flip
    between elbow-up and elbow-down along a chain."""
    if "joints" in target:
        goal_state.set_joint_group_positions("arm", np.array(target["joints"], dtype=float))
    else:
        # Position-only IK (see kinematics.yaml); the 3-joint arm can't also
        # match an orientation.
        pose = Pose()
        pose.position.x, pose.position.y, pose.position.z = map(float, target["position"])
        if not goal_state.set_from_ik("arm", pose, "tool0", 1.0):
            print(f"No IK solution for {label}", flush=True)
            return False
    goal_state.update()

    arm.set_start_state_to_current_state()
    arm.set_goal_state(robot_state=goal_state)
    return move(robot, arm, label)


def main():
    args = parse_args()
    with open(args.file) as f:
        data = yaml.safe_load(f)
    targets = data.get("targets", {})
    chains = data.get("chains", {})

    if args.list or not args.name:
        print("chains: ", ", ".join(chains) or "(none)")
        print("targets:", ", ".join(targets) or "(none)")
        return
    if args.name in chains:
        steps = chains[args.name]
    elif args.name in targets:
        steps = [args.name]
    else:
        sys.exit(f"No chain or target named {args.name!r} in {args.file}")
    moves = [m for step in steps for m in expand(step, targets)]

    robot = MoveItPy(node_name="move_to", config_dict=config)
    arm = robot.get_planning_component("arm")
    time.sleep(1.0)  # give MoveItPy a moment to receive /joint_states

    goal_state = RobotState(robot.get_robot_model())
    for label, target in moves:
        if not go_to(robot, arm, goal_state, label, target):
            print("Stopping chain", flush=True)
            break


if __name__ == "__main__":
    main()
