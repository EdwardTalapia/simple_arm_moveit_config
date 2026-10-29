#!/bin/bash
# Run anything inside the ROS2 Humble + MoveIt container. Works from a plain
# clone of this repo: the repo is mounted at /workspace/src/<pkg>, and the
# colcon build/install/log dirs live in .ws/ (gitignored) so they persist.
# Usage: docker/run.sh [command...]
#   docker/run.sh                      # interactive shell
#   docker/run.sh colcon build --symlink-install
#   docker/run.sh ros2 topic list
#   REBUILD=1 docker/run.sh            # force an image rebuild
set -e

IMAGE="${IMAGE:-ros2-dev}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(dirname "$SCRIPT_DIR")"
PKG="$(basename "$REPO_DIR")"
WORKSPACE="$REPO_DIR/.ws"

# Pre-create the mount point so docker doesn't make it root-owned.
mkdir -p "$WORKSPACE/src/$PKG"

if [ -n "$REBUILD" ] || ! docker image inspect "$IMAGE" >/dev/null 2>&1; then
  echo "[*] Building $IMAGE (this pulls a multi-GB base image on first run)..."
  docker build -t "$IMAGE" -f "$SCRIPT_DIR/Dockerfile" \
    --build-arg USER_UID="$(id -u)" --build-arg USER_GID="$(id -g)" \
    "$SCRIPT_DIR"
fi

# Allow the container's X server connections through for GUI apps (rviz/gazebo/rqt).
# The container user shares our UID, so the X server sees it as us, not root.
xhost +si:localuser:"$(id -un)" >/dev/null 2>&1 || true

# Pass the X auth cookie through. On GNOME Wayland it lives at $XAUTHORITY
# (e.g. /run/user/1000/.mutter-Xwaylandauth.*), not ~/.Xauthority. Only mount
# it if it's a real file, otherwise docker creates an empty root-owned dir.
XAUTH_FILE="${XAUTHORITY:-$HOME/.Xauthority}"
XAUTH_ARGS=()
if [ -f "$XAUTH_FILE" ]; then
  XAUTH_ARGS=(-e XAUTHORITY=/tmp/.Xauthority -v "$XAUTH_FILE:/tmp/.Xauthority:ro")
fi

# Only ask for a TTY when we have one, so scripts/CI can call this too.
TTY_ARGS=(-i)
[ -t 0 ] && [ -t 1 ] && TTY_ARGS+=(-t)

# --privileged + full /dev mount: broad hardware access for robots/sensors/USB.
# Narrow this to specific --device=/dev/ttyUSB0 etc. if you don't need everything.
docker run --rm "${TTY_ARGS[@]}" \
  --network host \
  --privileged \
  -e DISPLAY="$DISPLAY" \
  -e ROS_DOMAIN_ID="${ROS_DOMAIN_ID:-12}" \
  -v /tmp/.X11-unix:/tmp/.X11-unix:rw \
  "${XAUTH_ARGS[@]}" \
  -v "$WORKSPACE:/workspace" \
  -v "$REPO_DIR:/workspace/src/$PKG" \
  -v /dev:/dev \
  --name "${IMAGE}-run-$$" \
  "$IMAGE" "${@:-bash}"
