#!/usr/bin/env bash
# deploy.sh — one-shot deploy of the tradebot stack on a fresh Ubuntu 24.04 box.
#
# Usage (from your laptop):
#     scp -r infra/stack/* scripts/deploy.sh root@<SERVER_IP>:/opt/stack/
#     ssh root@<SERVER_IP> "bash /opt/stack/deploy.sh"
#
# Requires: /opt/stack/.env to already exist with real values (copy from .env.example).

set -euo pipefail

STACK_DIR="/opt/stack"

if [[ ! -f "${STACK_DIR}/.env" ]]; then
  echo "ERROR: ${STACK_DIR}/.env not found. Copy .env.example, fill secrets, then re-run."
  exit 1
fi

echo "==> Installing Docker if missing"
if ! command -v docker >/dev/null 2>&1; then
  apt update
  apt install -y ca-certificates curl gnupg git
  install -m 0755 -d /etc/apt/keyrings
  curl -fsSL https://download.docker.com/linux/ubuntu/gpg \
    | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
  chmod a+r /etc/apt/keyrings/docker.gpg
  echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo "$VERSION_CODENAME") stable" \
    > /etc/apt/sources.list.d/docker.list
  apt update
  apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
fi

echo "==> Pulling images"
cd "${STACK_DIR}"
docker compose pull

echo "==> Starting stack"
docker compose up -d

echo "==> Waiting for services..."
sleep 15

echo "==> Status"
docker compose ps
echo
echo "n8n:       http://$(hostname -I | awk '{print $1}'):5678"
echo "Evolution: http://$(hostname -I | awk '{print $1}'):8080/manager"
