#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "Stopping n8n containers..."

docker compose -f ${SCRIPT_DIR}/docker-compose.yml stop

echo "All n8n containers stopped."
echo "If ngrok is still running in another terminal, stop it with CTRL+C."
