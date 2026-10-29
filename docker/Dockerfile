FROM osrf/ros:humble-desktop-full

RUN apt-get update && apt-get install -y --no-install-recommends \
    python3-pip git nano \
        ros-humble-moveit \
    && rm -rf /var/lib/apt/lists/*
RUN bash -c "source /opt/ros/humble/setup.bash && ros2 pkg prefix moveit_ros_move_group"

# MoveIt tutorial demo (Panda), simulated controllers, Python API, and the
# CycloneDDS middleware MoveIt recommends on Humble. Separate layer so the
# base apt layer above stays cached.
RUN apt-get update && apt-get install -y --no-install-recommends \
    ros-humble-moveit-py \
    ros-humble-moveit-resources-panda-moveit-config \
    ros-humble-ros2-control \
    ros-humble-ros2-controllers \
    ros-humble-gripper-controllers \
    ros-humble-rmw-cyclonedds-cpp \
    && rm -rf /var/lib/apt/lists/*
RUN bash -c "source /opt/ros/humble/setup.bash \
    && ros2 pkg prefix moveit_py \
    && ros2 pkg prefix moveit_resources_panda_moveit_config"

ENV RMW_IMPLEMENTATION=rmw_cyclonedds_cpp

# run.sh passes the host user's UID/GID so files written to the mounted
# workspace aren't root-owned.
ARG USER_UID=1000
ARG USER_GID=1000
ARG USERNAME=ros

# sros: source the ROS install. sws: source this workspace's build
# (re-run after colcon build to pick up new packages).
RUN groupadd -f -g "${USER_GID}" "${USERNAME}" \
    && useradd -m -u "${USER_UID}" -g "${USER_GID}" -s /bin/bash "${USERNAME}" \
    && echo "source /opt/ros/humble/setup.bash" >> "/home/${USERNAME}/.bashrc" \
    && echo 'alias sros="source /opt/ros/$ROS_DISTRO/setup.bash"' >> "/home/${USERNAME}/.bashrc" \
    && echo 'alias sws="source /workspace/install/setup.bash"' >> "/home/${USERNAME}/.bashrc"

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

USER ${USERNAME}
WORKDIR /workspace
ENTRYPOINT ["/entrypoint.sh"]
CMD ["bash"]
