#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Load environment variables from .env
source ${SCRIPT_DIR}/.env

echo "Starting existing n8n containers..."
docker compose -f ${SCRIPT_DIR}/docker-compose.yml start

echo "Containers started."
echo "Starting ngrok (HTTPS → n8n-primary on port 5678)..."

ngrok http 5678
