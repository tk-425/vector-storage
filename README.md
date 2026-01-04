# vmem - Vector Memory System

A persistent vector memory system for AI agents. Saves and retrieves context across sessions using ChromaDB + Ollama embeddings.

> **📖 User Guide:** See [Instruction.md](Instruction.md) for the complete manual and setup guide.

## Architecture

```
Local (Client)                      Remote (Server)
┌────────────────────┐              ┌────────────────────┐
│ AI Agent           │              │ Docker Compose     │
│ (Claude/Gemini/...)│              │ ┌────────────────┐ │
│        ↓           │   HTTPS      │ │ Vector API     │ │
│ vmem CLI           │ ──────────→  │ │ (FastAPI)      │ │
│ (~/.bin/vmem)      │   ngrok      │ └────────────────┘ │
└────────────────────┘              │        ↓           │
                                    │ ┌────────────────┐ │
                                    │ │ ChromaDB       │ │
                                    │ │ + Ollama       │ │
                                    │ └────────────────┘ │
                                    └────────────────────┘
```

## Quick Start

### 1. Initialize in a Project

```bash
cd ~/your-project

# Basic init (auto-save OFF)
vmem init

# Full init (auto-save ON + Claude Code hooks)
vmem init on
```

### 2. Use Commands

```bash
# Save a note
vmem save "API uses JWT auth with httpOnly cookies"

# Query for context
vmem query "authentication"

# Check status
vmem status
```

---

## Commands Reference

### Project Initialization

| Command        | Purpose                     |
| -------------- | --------------------------- |
| `vmem init`    | Initialize vmem in project  |
| `vmem init on` | Init with auto-save + hooks |
| `vmem uninit`  | Complete project teardown   |

### Core Commands

| Command                      | Purpose                           |
| ---------------------------- | --------------------------------- |
| `vmem save "text"`           | Save to project (respects toggle) |
| `vmem save "text" --force`   | Force save (always works)         |
| `vmem save "text" --global`  | Save to global collection         |
| `vmem query "term"`          | Search project collection         |
| `vmem query "term" --global` | Search global collection          |
| `vmem search "term"`         | Search project + global           |

### Configuration

| Command              | Purpose                      |
| -------------------- | ---------------------------- |
| `vmem status`        | Check auto-save mode         |
| `vmem status --json` | Status as JSON (for scripts) |
| `vmem toggle on`     | Enable project auto-save     |
| `vmem toggle off`    | Disable project auto-save    |

### Maintenance

| Command                              | Purpose                           |
| ------------------------------------ | --------------------------------- |
| `vmem ping`                          | Check server connectivity         |
| `vmem history`                       | Show recent saves                 |
| `vmem history --global`              | Show global history               |
| `vmem prune --duplicates`            | Remove duplicate entries          |
| `vmem prune --older-than 30`         | Remove entries older than 30 days |
| `vmem prune compact --all`           | Remove all compacts               |
| `vmem prune compact --all --dry-run` | Preview compact removal           |
| `vmem prune compact --older-than`    | Remove old compacts               |
| `vmem prune --dry-run`               | Preview without deleting          |

### Compacts (Project Snapshots)

| Command                       | Purpose                    |
| ----------------------------- | -------------------------- |
| `vmem compact "text"`         | Save snapshot (max 5 kept) |
| `vmem retrieve compact`       | Get most recent compact    |
| `vmem retrieve compact 3`     | Get 3rd compact (1=newest) |
| `vmem retrieve compact --all` | List all compacts          |

---

## Configuration Files

| File                 | Location | Purpose               |
| -------------------- | -------- | --------------------- |
| `~/.vmem/config.yml` | Home     | Global auto-save mode |
| `~/.vmem/vmem-*.sh`  | Home     | Claude Code hooks     |

> **Hooks Documentation:** See [cc-hooks/README.md](cc-hooks/README.md).

---

## AI Agent Integration

### Claude Code

Skills are stored in `~/.claude/skills/vmem/SKILL.md`. Claude Code reads this automatically.

**Install:**

```bash
cp -r cc-skills/skills/* ~/.claude/skills/
```

> **Skill Documentation:** See [cc-skills/README.md](cc-skills/README.md).

### Gemini / Codex / Others

Run `vmem init` to automatically configure `AGENTS.md`, `GEMINI.md`, or `CLAUDE.md`.

---

## Server Setup

### Prerequisites

- Docker + Docker Compose
- Ollama with nomic-embed-text model
- ngrok for HTTPS tunnel

### Location

```
/path/to/vector-storage/
├── docker-compose.yml
├── vector-api/
│   └── main.py
└── data/
    └── chromadb/
```

> **Detailed Server Docs:** See [vector-storage/README.md](vector-storage/README.md).

### Start Server

```bash
cd /path/to/vector-storage
docker compose up -d
```

### Environment Variables (Remote)

Add to `~/.zshrc`:

```bash
export VECTOR_BASE_URL="https://your-ngrok-url.ngrok-free.dev"
export VECTOR_AUTH_TOKEN="your-token"
```

---

## Directory Structure

```
vector-storage/
├── AGENTS.md             # Universal agent reference
├── cc-hooks/             # Claude Code hook scripts
│   ├── vmem-pre-query.sh
│   └── vmem-post-save.sh
├── cc-skills/            # Claude Code skills
│   └── skills/vmem/SKILL.md
├── vmem-cli/             # CLI implementation
│   └── vmem.py
└── vector-storage/       # Server code
    └── vector-api/main.py
```

---

## Deployment Cheatsheet

```bash
# Deploy CLI
cp vmem-cli/vmem.py ~/.bin/vmem

# Deploy Claude Code skills
cp -r cc-skills/skills/* ~/.claude/skills/

# Deploy hooks
cp cc-hooks/vmem-*.sh ~/.vmem/

# Deploy server
scp vector-storage/vector-api/main.py <SERVER_HOST>:/path/to/vector-api/
ssh <SERVER_HOST> "cd /path/to/vector-storage && docker compose build && docker compose up -d"
```

---

## SSH Config

Add to `~/.ssh/config`:

```
Host server-host
    HostName <YOUR_SERVER_IP>
    User <YOUR_REMOTE_USER>
```

---

## Troubleshooting

| Issue                     | Solution                                       |
| ------------------------- | ---------------------------------------------- |
| `Cannot reach Vector API` | Check ngrok tunnel and server status           |
| `Auto-save is OFF`        | Use `vmem toggle on` or `--force` flag         |
| YAML boolean error        | Fixed in latest vmem.py                        |
| Hooks not working         | Restart Claude Code, verify `~/.vmem/` scripts |

### View Server Logs

```bash
ssh <SERVER_HOST> "cd /path/to/vector-storage && docker compose logs -f vector-api"
```
