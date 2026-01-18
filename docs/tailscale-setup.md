# Tailscale Setup Guide

This document covers the Tailscale configuration for securing the connection between the `vmem` CLI (client) and the ChromaDB/Vector API server.

## Overview

Tailscale creates a private, secure mesh network (VPN) between your devices. It allows you to access your server using a private IP address (e.g., `100.x.y.z`) as if it were on your local network, without exposing any ports to the public internet.

## Architecture

```
Local (Client)                      Remote (Server)
┌────────────────────┐              ┌────────────────────┐
│ AI Agent           │              │ Docker Compose     │
│ (Claude/Gemini/...)│              │ ┌────────────────┐ │
│        ↓           │   HTTPS      │ │ Vector API     │ │
│ vmem CLI           │ ──────────→  │ │ (Port 8080)    │ │
│ (~/.bin/vmem)      │ Tailscale IP │ └────────────────┘ │
└────────────────────┘              │        ↓           │
                                    │ ┌────────────────┐ │
                                    │ │ ChromaDB       │ │
                                    │ │ + Ollama       │ │
                                    │ └────────────────┘ │
                                    └────────────────────┘
```

## Setup Steps

### 1. Install Tailscale

Please follow the official [Tailscale Installation Guide](https://tailscale.com/kb/1347/installation) to install Tailscale on both your Server and Client machines.

### 2. Connect and Verify

1.  Log in to Tailscale on both devices using the same account.
2.  On your Client machine, verify you can ping the Server:
    ```bash
    ping 100.x.y.z  # Use your server's Tailscale IP
    ```

### 3. Server Configuration

Ensure your `docker-compose.yml` exposes the `vector-api` port (8080) to the host.

```yaml
services:
  vector-api:
    ports:
      - "8080:8080" # Maps container 8080 to host 8080
```

_Note: Since Tailscale is a VPN, exposing port 8080 to the "host" effectively exposes it to the Tailscale network, but NOT the public internet (assuming your firewall blocks public traffic)._

### 4. Client Configuration

Add the Tailscale URL to your **client-side** shell configuration (`~/.zshrc`).

```bash
# Get your server's IP from the Tailscale dashboard or `tailscale ip` on the server
export VECTOR_BASE_URL="http://100.x.y.z:8080"
export VECTOR_AUTH_TOKEN="your-token"
```

Reload your shell:

```bash
source ~/.zshrc
```

## Security Benefits

| Feature         | Tailscale                            | Public Internet / Ngrok    |
| :-------------- | :----------------------------------- | :------------------------- |
| **Access**      | Private (Authenticated Devices Only) | Public (Anyone with URL)   |
| **Encryption**  | End-to-End (WireGuard®)              | TLS (Terminates at tunnel) |
| **Stability**   | Static IP (100.x.y.z)                | Dynamic URL (Free Tier)    |
| **Performance** | P2P Direct Connection (Low Latency)  | Relayed through Cloud      |

## Troubleshooting

### Connection Refused

- Ensure `vector-api` Docker container is running (`docker compose ps`).
- Ensure Tailscale is connected on both devices (`tailscale status`).
- Verify firewall allows port 8080 on the specific Tailscale interface (usually `tailscale0`).

### MagicDNS

If you have MagicDNS enabled in Tailscale, you can use the machine name instead of the IP:

```bash
export VECTOR_BASE_URL="http://my-server:8080"
```

## References

- [Tailscale Quick Start](https://tailscale.com/kb/1017/install-guides)
- [Tailscale & Docker](https://tailscale.com/kb/1054/container-networking)
