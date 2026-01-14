---
name: vmem
description: Vector memory CLI for saving and retrieving context across sessions. Use after completing work to save summaries, or query before starting to retrieve past decisions.
---

# vmem - Vector Memory

## AUTO-RETRIEVAL (Before work)

When user asks about implementation, debugging, or "how did we do X":

1. Query: `vmem query "relevant keywords"`
2. Also try: `vmem search "keywords"` (searches project + global)
3. Use results as context for your response

## AUTO-SAVE (After work)

After completing implementation tasks:

1. Check: `vmem status`
2. If auto-save is **ON** → `vmem save "summary of work"`
3. If auto-save is **OFF** → only save if user explicitly asks:
   - Triggers: "remember this", "save this", "store this"
   - Use: `vmem save "text" --force`
4. If auto-save is **PROMPT** → ask user first

**Keep saves SHORT: 2-4 sentences max.**

Good: `"Added vmem ping using /health endpoint. Returns response time. Checks connectivity."`

Bad: `[50+ lines explaining every detail]`

**Formula:** WHAT was done + WHY it matters + KEY function names

## COMPACT (Project Snapshots)

**Compacts can be LONG** — unlike regular saves (2-4 sentences), compacts have no length limit.

When user says "compact to vmem", "save a compact", or similar:

1. **Summarize the current conversation** — what was done, key decisions, files changed
2. **Include project context** — architecture, main components, important patterns
3. **Run:** `vmem compact "your comprehensive summary..."`

**Compact content should include:**

- What was implemented/changed
- Key files modified (with function names)
- Important decisions and why
- Current project state
- Any gotchas or things to remember

**Example compact:**

```
vmem compact "Session 2025-12-30: Added vmem compact and retrieve commands.
save_compact() in vmem.py auto-deletes oldest when 6th added (max 5).
retrieve_compact() gets by index (1=newest). Updated SKILL.md and .vmem.md.
Also fixed YAML boolean bug in get_effective_mode(). Project uses FastAPI + ChromaDB."
```

## What to Save

✅ Implementation decisions, bug fixes, API patterns, architecture choices
✅ Workflows, configurations, troubleshooting steps, lessons learned
✅ Key findings and conclusions from research/exploration
❌ Pure questions without answers, incomplete brainstorming
❌ Long documentation dumps or full file contents

## Commands

| Command                              | Purpose                             |
| ------------------------------------ | ----------------------------------- |
| `vmem query "term"`                  | Search project collection           |
| `vmem query "term" --global`         | Search global collection            |
| `vmem search "term"`                 | Search project + global             |
| `vmem save "text"`                   | Save to project (respects toggle)   |
| `vmem save "text" --global`          | Save to global                      |
| `vmem save "text" --force`           | Force save to project               |
| `vmem save "text" --global --force`  | Force save to global                |
| `vmem status`                        | Check auto-save toggle              |
| `vmem status --json`                 | Status as JSON (for scripts)        |
| `vmem toggle on`                     | Enable project auto-save            |
| `vmem toggle off`                    | Disable project auto-save           |
| `vmem toggle on --scope global`      | Enable global auto-save             |
| `vmem toggle off --scope global`     | Disable global auto-save            |
| `vmem init`                          | Initialize vmem in project          |
| `vmem ping`                          | Check server connectivity           |
| `vmem history`                       | Show recent saves                   |
| `vmem history --global`              | Show global history                 |
| `vmem prune --duplicates --dry-run`  | Preview duplicate removal           |
| `vmem prune --duplicates`            | Remove duplicate entries            |
| `vmem prune --older-than 30`         | Remove entries older than 30 days   |
| `vmem prune compact --all`           | Remove all compacts                 |
| `vmem prune compact --all --dry-run` | Preview compact removal             |
| `vmem prune compact --older-than 7`  | Prune compacts >7 days old          |
| `vmem init on`                       | Init with auto-save + hooks         |
| `vmem compact "text"`                | Save project snapshot (max 10 kept) |
| `vmem retrieve compact`              | Get most recent compact             |
| `vmem retrieve compact 3`            | Get 3rd compact (1=newest)          |
| `vmem retrieve compact --all`        | List all compacts                   |
| `vmem delete compact 2`              | Delete compact at index 2           |

## Maintenance

- Use `vmem ping` to verify server is reachable before operations
- Use `vmem history` to review what's been saved
- Use `vmem prune --dry-run` before actual pruning to preview changes
- Use `vmem prune compact --all --dry-run` to preview compact cleanup
