#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "Stopping vector-storage containers..."

docker compose -f ${SCRIPT_DIR}/docker-compose.yml stop

echo "All vector-storage containers stopped."
# echo "If ngrok is still running in another terminal, stop it with CTRL+C."
