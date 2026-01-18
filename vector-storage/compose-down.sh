#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "Stopping and removing vector-storage containers..."

docker compose -f ${SCRIPT_DIR}/docker-compose.yml down

echo "Containers removed. Volumes preserved."
# echo "If ngrok is running, stop it with CTRL+C."
