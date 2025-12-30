# vmem - Vector Memory System

A persistent vector memory system for AI agents. Saves and retrieves context across sessions using ChromaDB + Ollama embeddings.

## Architecture

```
MacBook (Client)                    tk-lenovo (Server)
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
| `vmem init`          | Initialize vmem in project   |
| `vmem init on`       | Init with auto-save + hooks  |

### Maintenance

| Command                      | Purpose                           |
| ---------------------------- | --------------------------------- |
| `vmem ping`                  | Check server connectivity         |
| `vmem history`               | Show recent saves                 |
| `vmem history --global`      | Show global history               |
| `vmem prune --duplicates`    | Remove duplicate entries          |
| `vmem prune --older-than 30` | Remove entries older than 30 days |
| `vmem prune --dry-run`       | Preview without deleting          |

### Compacts (Project Snapshots)

| Command                       | Purpose                    |
| ----------------------------- | -------------------------- |
| `vmem compact "text"`         | Save snapshot (max 5 kept) |
| `vmem retrieve compact`       | Get most recent compact    |
| `vmem retrieve compact 3`     | Get 3rd compact (1=newest) |
| `vmem retrieve compact --all` | List all compacts          |

---

## Configuration Files

| File                 | Location     | Purpose                    |
| -------------------- | ------------ | -------------------------- |
| `.vmem.yml`          | Project root | Per-project auto-save mode |
| `.vmem.md`           | Project root | AI agent instructions      |
| `~/.vmem/config.yml` | Home         | Global auto-save mode      |
| `~/.vmem/vmem-*.sh`  | Home         | Claude Code hooks          |

### .vmem.yml

```yaml
auto_save: on # on | off | prompt
```

---

## AI Agent Integration

### Claude Code

Skills are stored in `~/.claude/skills/vmem/SKILL.md`. Claude Code reads this automatically.

**Install:**

```bash
cp -r cc-skills/skills/* ~/.claude/skills/
```

### Gemini / Codex / Others

Add to `AGENTS.md`, `GEMINI.md`, or `CLAUDE.md`:

```markdown
## Vector Memory

For vmem commands and auto-save/retrieval behavior, read: `.vmem.md`
```

---

## Server Setup (tk-lenovo)

### Prerequisites

- Docker + Docker Compose
- Ollama with nomic-embed-text model
- ngrok for HTTPS tunnel

### Location

```
/home/tk-lenovo/Docker-Container/vector-storage/
├── docker-compose.yml
├── vector-api/
│   └── main.py
└── data/
    └── chromadb/
```

### Start Server

```bash
cd /home/tk-lenovo/Docker-Container/vector-storage
docker compose up -d
```

### Environment Variables (MacBook)

Add to `~/.zshrc`:

```bash
export VECTOR_BASE_URL="https://your-ngrok-url.ngrok-free.dev"
export VECTOR_AUTH_TOKEN="your-token"
```

---

## Directory Structure

```
vector-storage/
├── .vmem.md              # AI agent instructions (project)
├── .vmem.yml             # Auto-save config (project)
├── AGENTS.md             # Universal agent reference
├── cc-hooks/             # Claude Code hook scripts
│   ├── vmem-pre-query.sh
│   └── vmem-post-save.sh
├── cc-skills/            # Claude Code skills
│   └── skills/vmem/SKILL.md
├── vmem-cli/             # CLI implementation
│   └── vmem.py
└── vector-storage/       # Server code (for tk-lenovo)
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

# Deploy server (tk-lenovo)
scp vector-storage/vector-api/main.py tk-lenovo:/home/tk-lenovo/Docker-Container/vector-storage/vector-api/
ssh tk-lenovo "cd /home/tk-lenovo/Docker-Container/vector-storage && docker compose build && docker compose up -d"
```

---

## SSH Config

Add to `~/.ssh/config`:

```
Host tk-lenovo
    HostName <YOUR_SERVER_IP>
    User tk-lenovo
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
ssh tk-lenovo "cd /home/tk-lenovo/Docker-Container/vector-storage && docker compose logs -f vector-api"
```
