# docker

ROS2 Humble + MoveIt 2 dev container for this package. Everything runs
from the repo folder, so you don't need ROS installed or a colcon
workspace set up.

## Quick start

```
git clone git@github.com:EdwardTalapia/simple_arm_moveit_config.git
cd simple_arm_moveit_config

docker/run.sh colcon build --symlink-install
docker/run.sh ros2 launch simple_arm_moveit_config demo.launch.py   # terminal 1
docker/run.sh ros2 run simple_arm_moveit_config move_to.py circle   # terminal 2
```

`docker/run.sh` with no arguments opens a shell in the container.

The first run builds the `ros2-dev` image from `docker/Dockerfile`. That
pulls the multi-GB `osrf/ros:humble-desktop-full` base image, so expect it
to take a while. Later runs reuse the image. To rebuild it after editing
the Dockerfile, run `REBUILD=1 docker/run.sh`.

## Layout inside the container

| Container path                            | Host path            |
|-------------------------------------------|----------------------|
| `/workspace`                              | `.ws/` (gitignored)  |
| `/workspace/src/simple_arm_moveit_config` | this repo            |

`colcon build` output (`build/`, `install/`, `log/`) lands in `.ws/`, so it
survives between runs. Edits to the repo show up in the container
immediately. With `--symlink-install`, changes to the Python scripts take
effect without rebuilding. `install/setup.bash` is sourced automatically
when the container starts.

Shell aliases inside the container:

| Alias  | Runs                                       |
|--------|--------------------------------------------|
| `sros` | `source /opt/ros/$ROS_DISTRO/setup.bash`   |
| `sws`  | `source /workspace/install/setup.bash`     |

Run `sws` after a `colcon build` so an open shell picks up new or changed
packages.

## What run.sh sets up

- **`--network host`**: containers from separate `run.sh` calls (and
  other machines on the LAN) see each other's topics. `ROS_DOMAIN_ID`
  defaults to 12. To use another domain, set it before running, e.g.
  `ROS_DOMAIN_ID=5 docker/run.sh`.
- **X11 forwarding**: GUI tools (rviz2, gazebo, rqt) open on your desktop.
- **`--privileged` + `-v /dev:/dev`**: full hardware access for robots,
  sensors and USB devices. This is broad. If you only need one device,
  swap it for `--device=/dev/ttyUSB0` (etc.).
- **Matching UID/GID**: the image's user gets your host UID/GID, so files
  it writes to the repo aren't owned by root.

## Requirements

- Linux with Docker installed and the daemon running.
- Your user in the `docker` group (`sudo usermod -aG docker $USER`, then
  log out and back in).
- An X11 or XWayland desktop for GUI tools.

## Sharing a prebuilt image instead (offline)

If someone can't pull from Docker Hub, export the image and send them the
file:

```
docker save ros2-dev | gzip > ros2-dev.tar.gz   # ~1.5 GB
docker load < ros2-dev.tar.gz                   # on their machine
```

The image's user has the builder's UID. If the other person's UID isn't
1000, they should rebuild with `REBUILD=1 docker/run.sh`.
