# vmem CLI Tool - Command Reference

**Status: 🔄 IN PROGRESS** (2025-12-30)

Universal CLI for vector memory operations. Works with any AI agent.

**New Commands:** `ping`, `history`, `prune`, `init on`, `save compact`, `retrieve compact`

---

## Commands

### vmem save

Save text to vector storage.

```bash
# Save to project collection (default) - respects auto-save toggle
vmem save "API uses JWT authentication"

# Force save (bypass auto-save toggle)
vmem save "API uses JWT authentication" --force
vmem save "API uses JWT authentication" -f

# Save to global collection
vmem save "Docker runs on tk-lenovo" --global

# Save with metadata
vmem save "Password reset via email" --tags auth,security --importance high --type note

# Force save to global with metadata
vmem save "text" --global --force --agent claude-code
```

**Options:**
| Option | Description |
|--------|-------------|
| `--force`, `-f` | Bypass auto-save toggle (always saves) |
| `--global` | Save to global collection |
| `--tags` | Comma-separated tags |
| `--importance` | low, medium, high |
| `--type` | note, workflow, bug, etc. |
| `--agent` | Agent name (default: cli) |

> **Note:** If auto-save is OFF, `vmem save` will show a message and skip. Use `--force` for manual saves.

---

### vmem query

Search vector storage.

```bash
# Query project collection (default)
vmem query "authentication method"

# Query global collection
vmem query "docker setup" --global

# Get more results
vmem query "auth" --top-k 10

# Output as JSON
vmem query "auth" --json
```

**Options:**
| Option | Description |
|--------|-------------|
| `--global` | Search global collection |
| `--top-k` | Number of results (default: 5) |
| `--json` | Output as JSON |

---

### vmem search

Search both project AND global collections.

**Quick Reference:**
| Command | Scope |
|---------|-------|
| `vmem query "term"` | Project only |
| `vmem query "term" --global` | Global only |
| `vmem search "term"` | Both project + global |

```bash
vmem search "deployment"
vmem search "docker" --top-k 5
```

---

### vmem status

Show current configuration.

```bash
vmem status
```

**Output:**

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 Vector Memory Status
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Global Auto-save mode: off
Project Auto-save mode: on
Current project: vector-storage
Vector API: https://...ngrok-free.dev
```

---

### vmem toggle

Set auto-save mode.

```bash
# Set global auto-save
vmem toggle on
vmem toggle off
vmem toggle prompt

# Set project auto-save (creates .vmem.yml)
vmem toggle on --scope project
vmem toggle off --scope project
```

**Modes:**
| Mode | Description |
|------|-------------|
| `off` | Auto-save disabled |
| `on` | Auto-save enabled |
| `prompt` | Ask before saving |

---

### vmem ping

Check server connectivity.

```bash
vmem ping
```

**Output (success):**

```
✓ Connected to Vector API (123ms)
  URL: https://...ngrok-free.dev
```

**Output (failure):**

```
✗ Cannot reach Vector API
  URL: https://...ngrok-free.dev
  Error: Connection refused
```

---

### vmem history

Show recent saves for a project.

```bash
# Show last 10 saves (default)
vmem history

# Show last 5 saves
vmem history --limit 5

# Show global history
vmem history --global
```

**Options:**
| Option | Description |
|--------|-------------|
| `--limit` | Number of entries (default: 10) |
| `--global` | Show global collection history |

**Output:**

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📜 Recent saves (vector-storage):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[1] 2025-12-29 | JWT auth with httpOnly cookies...
[2] 2025-12-28 | Password reset via email token...
[3] 2025-12-27 | Rate limiting at 100 req/min...
```

---

### vmem prune

Remove duplicates and old entries.

```bash
# Dry run - show what would be deleted
vmem prune --dry-run

# Remove duplicate entries (same text)
vmem prune --duplicates

# Remove entries older than 30 days
vmem prune --older-than 30

# Combine options
vmem prune --duplicates --older-than 90
```

**Options:**
| Option | Description |
|--------|-------------|
| `--dry-run` | Preview without deleting |
| `--duplicates` | Remove entries with identical text |
| `--older-than DAYS` | Remove entries older than N days |
| `--global` | Prune global collection |

**When to Use:**

- 🧹 **Monthly maintenance** — Run `vmem prune --duplicates` to clean up accidental duplicate saves
- 📅 **Project milestones** — After major releases, prune old entries: `vmem prune --older-than 90`
- 💾 **Before backups** — Clean up with `--dry-run` first to review what will be removed
- 🔄 **After heavy iteration** — If you've been saving frequently during debugging, prune duplicates

**Example workflow:**

```bash
# 1. First, see what would be deleted
vmem prune --duplicates --older-than 60 --dry-run

# 2. If the preview looks good, run for real
vmem prune --duplicates --older-than 60
```

---

### vmem init

Initialize vmem in current project.

```bash
# Basic init (auto_save: off)
vmem init

# Init with auto-save ON and Claude Code hooks
vmem init on
```

**`vmem init` creates:**

- `.vmem.md` — Agent instructions
- `.vmem.yml` — Auto-save config (off)
- Updates `CLAUDE.md`, `AGENTS.md`, etc.

**`vmem init on` also creates:**

- `.vmem.yml` — Auto-save config (on)
- `.claude/settings.json` — Claude Code hooks enabled

---

### vmem save compact

Save a comprehensive project snapshot. Unlike regular saves (2-4 sentences), compacts can be long. Only 5 compacts are kept per project — oldest is auto-deleted when 6th is added.

```bash
# Save a compact (can be long text)
vmem save compact "Full project summary: Architecture uses FastAPI + ChromaDB.
Main components are vmem CLI (vmem.py), Vector API (main.py), and hooks.
Recent changes include --verbose flag for prune, YAML boolean fix, init on feature..."

# Save compact to global
vmem save compact "Global knowledge snapshot..." --global
```

**Comparison:**

| Type                       | Length        | Limit     | Purpose           |
| -------------------------- | ------------- | --------- | ----------------- |
| `vmem save "text"`         | 2-4 sentences | Unlimited | Quick notes       |
| `vmem save compact "text"` | Unlimited     | Max 5     | Project snapshots |

---

### vmem retrieve compact

Retrieve saved compacts.

```bash
# Get most recent compact
vmem retrieve compact

# Get specific compact (1=newest, 5=oldest)
vmem retrieve compact 1
vmem retrieve compact 5

# List all compacts
vmem retrieve compact --all

# Get from global
vmem retrieve compact --global
```

**Options:**
| Option | Description |
|--------|-------------|
| `1-5` | Specific compact (1=newest) |
| `--all` | List all compacts with previews |
| `--global` | Retrieve from global collection |

---

## Architecture

```
MacBook                          tk-lenovo
┌──────────────────┐             ┌──────────────────┐
│ AI Agent         │             │ Vector API       │
│ (Claude Code)    │             │ (FastAPI)        │
│       ↓          │   HTTP      │       ↓          │
│ vmem CLI         │ ──────────> │ ChromaDB         │
│ (~/.bin/vmem)    │   ngrok     │ (port 8080)      │
└──────────────────┘             └──────────────────┘
```

---

## Config Files

| Location             | Scope   | Purpose                |
| -------------------- | ------- | ---------------------- |
| `~/.vmem/config.yml` | Global  | Default auto-save mode |
| `.vmem.yml`          | Project | Per-project override   |

---

## Environment Variables

Add to `~/.zshrc`:

```bash
export PATH="$HOME/.bin:$PATH"
export VECTOR_BASE_URL="$VECTOR_URL"
export VECTOR_AUTH_TOKEN="$AUTH_TOKEN"
```
