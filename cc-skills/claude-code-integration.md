# Claude Code Integration for vmem

Instructions for integrating vmem CLI with Claude Code agent.

---

## Overview

vmem integrates with Claude Code through:

1. **Skill files** - Define commands Claude can run
2. **Custom instructions** - Teach Claude when to save

---

## 1. Skill File

**Location:** `~/.claude/skills/vector-memory/vmem.md`

**Template:** See `agent-config/vmem.md` for the complete skill file.

### Create the skill:

```bash
mkdir -p ~/.claude/skills/vector-memory
cp /path/to/vector-storage/agent-config/vmem.md ~/.claude/skills/vector-memory/vmem.md
```

Or manually create the file with content from `agent-config/vmem.md`.

---

## 2. Usage Flow

```
User: "implement JWT authentication"
Claude: [does the work]
Claude: [checks vmem status]
  - If ON: runs `vmem save "JWT auth implemented with..." `
  - If OFF: does nothing unless user asks

User: "remember how we set up auth"
Claude: runs `vmem save "JWT setup details..." --force`

User: "how did we implement auth?"
Claude: runs `vmem query "auth implementation"`
```

---

## 3. Environment Variables

Claude Code needs these in the environment:

```bash
export VECTOR_BASE_URL="https://your-ngrok-url.ngrok-free.app"
export VECTOR_AUTH_TOKEN="your-token"
```

Add to `~/.zshrc` for persistence.
