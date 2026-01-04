#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "Starting vector-storage stack..."
docker compose -f ${SCRIPT_DIR}/docker-compose.yml up -d --pull always

echo "Docker services are up."
echo "Starting ngrok (HTTPS → vector-api on port 8080)..."
echo "Press CTRL+C to stop ngrok."

ngrok start --config ~/.config/ngrok/ngrok-chroma.yml chroma
