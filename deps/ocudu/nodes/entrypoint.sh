#!/bin/bash
set -eu

NODE_USER="${NODE_USER:-aether}"
NODE_PASSWORD="${NODE_PASSWORD:-aether}"

if ! id "$NODE_USER" >/dev/null 2>&1; then
    useradd -m -s /bin/bash -G sudo "$NODE_USER"
fi
echo "$NODE_USER:$NODE_PASSWORD" | chpasswd

ssh-keygen -A
mkdir -p /run/sshd

# cgroup v2: move this container's processes into a leaf cgroup so that the
# inner dockerd can manage the controllers (same approach as the docker:dind image).
if [ -f /sys/fs/cgroup/cgroup.controllers ]; then
    mkdir -p /sys/fs/cgroup/init
    xargs -rn1 < /sys/fs/cgroup/cgroup.procs > /sys/fs/cgroup/init/cgroup.procs 2>/dev/null || :
    sed -e 's/ / +/g' -e 's/^/+/' < /sys/fs/cgroup/cgroup.controllers \
        > /sys/fs/cgroup/cgroup.subtree_control 2>/dev/null || :
fi

rm -f /var/run/docker.pid /var/run/docker/containerd/containerd.pid
dockerd >/var/log/dockerd.log 2>&1 &
DOCKERD_PID=$!

trap 'kill "$DOCKERD_PID" 2>/dev/null || :; wait "$DOCKERD_PID" 2>/dev/null || :; exit 0' TERM INT

/usr/sbin/sshd -D -e &
SSHD_PID=$!
wait "$SSHD_PID"
