# Ngrok Setup Guide

This document covers the ngrok configuration for exposing local services (n8n and ChromaDB) to the internet on the server.

## Overview

Ngrok creates secure tunnels from public URLs to locally running services. On your server, you can use ngrok to expose:

- **ChromaDB** (vector database) on port 8000

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                           Host                                  │
│                                                                 │
│   ┌─────────────┐                                               │
│   │   ngrok     │ ◄── Runs on HOST, not in Docker               │
│   │  (process)  │                                               │
│   └──────┬──────┘                                               │
│          │                                                      │
│          │ connects to  localhost:8000                          │
│          ▼                                                      │
│   ┌──────────────────────────────────────────────────────┐      │
│   │                Docker Network                        │      │
│   │                                                      │      │
│   │                         ┌─────────┐                  │      │
│   │                         │ chroma  │                  │      │
│   │                         │  :8000  │                  │      │
│   │                         └─────────┘                  │      │
│   │                                                      │      │
│   └──────────────────────────────────────────────────────┘      │
│                                       │                         │
│                                       ▼                         │
│                                 localhost:8000                  │
│                                (exposed to host)                │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
                                       │
                                       ▼
                                https://yyy.ngrok.io
                                (public chroma URL)
```

## Key Concept: Host vs Docker Networking

> [!IMPORTANT]
> Since ngrok runs on the **host machine** (not inside Docker), it can only access services via **localhost** and exposed ports. Docker container names like `chroma` are NOT resolvable from the host.

| Running From                | Access ChromaDB via |
| --------------------------- | ------------------- |
| **Host machine** (ngrok)    | `localhost:8000`    |
| **Inside Docker container** | `chroma:8000`       |

## Configuration Files

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

### Start ChromaDB tunnel

```bash
ngrok start --config ~/.config/ngrok/ngrok-chroma.yml chroma
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

## Troubleshooting

### Error: `ERR_NGROK_8012 - dial tcp: lookup chroma on 127.0.0.53:53: server misbehaving`

**Cause:** Ngrok is trying to resolve a Docker container name (like `chroma`) from the host machine, which doesn't work.

**Solution:** Use `localhost` or just the port number in the ngrok config:

**Solution:** Use `localhost` or just the port number in the ngrok config:

```yaml
# ✅ Correct - Use localhost or just the port
addr: 8000
addr: localhost:8000
```

### Error: `Your account is limited to 1 simultaneous ngrok agent session`

**Cause:** Free tier limitation - you can only run one ngrok process at a time.

**Solution:** Either:

1. Upgrade to a paid ngrok plan
2. Combine all tunnels in one config and use `ngrok start --all`

## Useful Commands

| Command                                | Description                                |
| -------------------------------------- | ------------------------------------------ |
| `ngrok start --config <path> <tunnel>` | Start specific tunnel from specific config |
| `ngrok start --all`                    | Start all tunnels in config                |
| `ngrok http 8000`                      | Quick tunnel without config file           |
| `ngrok config check`                   | Validate config file syntax                |
| `ngrok version`                        | Check ngrok version                        |

## References

- [Ngrok Documentation](https://ngrok.com/docs)
- [Ngrok Configuration File](https://ngrok.com/docs/agent/config/)
- [Docker Networking](https://docs.docker.com/network/)
