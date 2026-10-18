#!/bin/bash
# First boot of the demo VM. Docker is only installed here; the laptop
# starts the same processes without containers.
set -euxo pipefail
export DEBIAN_FRONTEND=noninteractive
apt-get update
apt-get install -y docker.io docker-compose-v2
systemctl enable --now docker
