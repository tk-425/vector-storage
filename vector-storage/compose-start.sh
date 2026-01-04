#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Load environment variables from .env
source ${SCRIPT_DIR}/.env

echo "Starting existing vector-storage containers..."
docker compose -f ${SCRIPT_DIR}/docker-compose.yml start

echo "Containers started."
echo "Starting ngrok (HTTPS → vector-api on port 8080)..."

ngrok start --config ~/.config/ngrok/ngrok-chroma.yml chroma
