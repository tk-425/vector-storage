#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "Starting n8n stack..."
docker compose -f ${SCRIPT_DIR}/docker-compose.yml up -d --pull always

echo "Docker services are up."
echo "Starting ngrok (HTTPS → n8n-primary on port 5678)..."
echo "Press CTRL+C to stop ngrok."

ngrok start --config ~/.config/ngrok/ngrok.yml n8n 

