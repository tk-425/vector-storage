# Ngrok Setup Guide for tk-lenovo

This document covers the ngrok configuration for exposing local services (n8n and ChromaDB) to the internet on the tk-lenovo server.

## Overview

Ngrok creates secure tunnels from public URLs to locally running services. On tk-lenovo, we use ngrok to expose:

- **n8n** (workflow automation) on port 5678
- **ChromaDB** (vector database) on port 8000

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        tk-lenovo Host                           │
│                                                                 │
│   ┌─────────────┐                                               │
│   │   ngrok     │ ◄── Runs on HOST, not in Docker               │
│   │  (process)  │                                               │
│   └──────┬──────┘                                               │
│          │                                                      │
│          │ connects to localhost:5678 and localhost:8000        │
│          ▼                                                      │
│   ┌──────────────────────────────────────────────────────┐      │
│   │                Docker Network                        │      │
│   │                                                      │      │
│   │   ┌─────────────┐    ┌─────────────┐    ┌─────────┐  │      │
│   │   │ n8n-primary │    │ n8n-worker  │    │ chroma  │  │      │
│   │   │   :5678     │    │             │    │  :8000  │  │      │
│   │   └─────────────┘    └─────────────┘    └─────────┘  │      │
│   │                                                      │      │
│   └──────────────────────────────────────────────────────┘      │
│          │                                    │                 │
│          ▼                                    ▼                 │
│     localhost:5678                      localhost:8000          │
│     (exposed to host)                   (exposed to host)       │
└─────────────────────────────────────────────────────────────────┘
           │                                    │
           ▼                                    ▼
    https://xxx.ngrok.io                https://yyy.ngrok.io
    (public n8n URL)                    (public chroma URL)
```

## Key Concept: Host vs Docker Networking

> [!IMPORTANT]
> Since ngrok runs on the **host machine** (not inside Docker), it can only access services via **localhost** and exposed ports. Docker container names like `n8n-primary` are NOT resolvable from the host.

| Running From                | Access n8n via     | Access ChromaDB via |
| --------------------------- | ------------------ | ------------------- |
| **Host machine** (ngrok)    | `localhost:5678`   | `localhost:8000`    |
| **Inside Docker container** | `n8n-primary:5678` | `chroma:8000`       |

## Configuration Files

### n8n Tunnel: `~/.config/ngrok/ngrok.yml`

```yaml
version: "3"
agent:
  authtoken: YOUR_NGROK_AUTHTOKEN
tunnels:
  n8n:
    proto: http
    addr: 5678
```

### ChromaDB Tunnel: `~/.config/ngrok/ngrok-chroma.yml`

```yaml
version: "3"
agent:
  authtoken: YOUR_NGROK_AUTHTOKEN
tunnels:
  chroma:
    proto: http
    addr: 8000
```

## Starting the Tunnels

### Start n8n tunnel

```bash
ngrok start --config ~/.config/ngrok/ngrok.yml n8n
```

### Start ChromaDB tunnel

```bash
ngrok start --config ~/.config/ngrok/ngrok-chroma.yml chroma
```

### Using the compose-up.sh script

The `/n8n/compose-up.sh` script starts Docker services and the n8n ngrok tunnel:

```bash
#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "Starting n8n stack..."
docker compose -f ${SCRIPT_DIR}/docker-compose.yml up -d

echo "Docker services are up."
echo "Starting ngrok (HTTPS → n8n-primary on port 5678)..."
echo "Press CTRL+C to stop ngrok."

ngrok start --config ~/.config/ngrok/ngrok.yml n8n
```

## Managing Ngrok Processes

### View running ngrok processes

```bash
ps aux | grep ngrok
```

### Stop all ngrok processes

```bash
pkill ngrok
```

### Stop a specific ngrok process

```bash
kill <PID>
```

## Free Tier Limitations

> [!WARNING]
> Free ngrok accounts can only run **one agent session at a time**.

To run multiple tunnels on a free account, combine them in a single config file:

```yaml
version: "3"
agent:
  authtoken: YOUR_NGROK_AUTHTOKEN
tunnels:
  n8n:
    proto: http
    addr: 5678
  chroma:
    proto: http
    addr: 8000
```

Then start all tunnels with:

```bash
ngrok start --all
```

This gives you two separate public URLs from one agent session.

## Troubleshooting

### Error: `ERR_NGROK_8012 - dial tcp: lookup n8n on 127.0.0.53:53: server misbehaving`

**Cause:** Ngrok is trying to resolve a Docker container name (like `n8n` or `n8n-primary`) from the host machine, which doesn't work.

**Solution:** Use `localhost` or just the port number in the ngrok config:

```yaml
# ❌ Wrong - Docker container name doesn't work from host
addr: n8n-primary:5678

# ✅ Correct - Use localhost or just the port
addr: 5678
addr: localhost:5678
```

### Error: `Your account is limited to 1 simultaneous ngrok agent session`

**Cause:** Free tier limitation - you can only run one ngrok process at a time.

**Solution:** Either:

1. Upgrade to a paid ngrok plan
2. Combine all tunnels in one config and use `ngrok start --all`

### Ngrok not picking up config changes

**Solution:** Kill and restart ngrok:

```bash
pkill ngrok
ngrok start --config ~/.config/ngrok/ngrok.yml n8n
```

## Useful Commands

| Command                                | Description                                |
| -------------------------------------- | ------------------------------------------ |
| `ngrok start n8n`                      | Start tunnel using default config          |
| `ngrok start --config <path> <tunnel>` | Start specific tunnel from specific config |
| `ngrok start --all`                    | Start all tunnels in config                |
| `ngrok http 5678`                      | Quick tunnel without config file           |
| `ngrok config check`                   | Validate config file syntax                |
| `ngrok version`                        | Check ngrok version                        |

## References

- [Ngrok Documentation](https://ngrok.com/docs)
- [Ngrok Configuration File](https://ngrok.com/docs/agent/config/)
- [Docker Networking](https://docs.docker.com/network/)
