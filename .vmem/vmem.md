# vmem - Vector Memory (v.1.1.4)

## AUTO-RETRIEVAL (Before work)
When user asks about implementation, debugging, or "how did we do X":
1. Query: `vmem query "relevant keywords"`
2. Also try: `vmem search "keywords"` (searches project + global)
3. Use results as context for your response

## AUTO-SAVE (After work)
After completing implementation tasks:
1. Check: `vmem status`
2. If auto-save is **ON** → `vmem save "summary of work"`
3. If auto-save is **OFF** → only save if user asks (use `--force`)
4. If auto-save is **PROMPT** → ask user first

## What to Save
✅ Implementation decisions, bug fixes, API patterns, architecture choices
✅ Workflows, configurations, troubleshooting steps, lessons learned
✅ Key findings and conclusions from research/exploration
❌ Pure questions without answers, incomplete brainstorming
❌ Long documentation dumps (keep saves to 2-4 sentences max)

**Save format:** WHAT was done + WHY it matters + KEY function names


## Commands
| Command | Purpose |
|---------|---------|
| `vmem query "term"` | Search project collection |
| `vmem search "term"` | Search project + global |
| `vmem save "text"` | Save (respects toggle) |
| `vmem save "text" --force` | Force save (always works) |
| `vmem status` | Check auto-save toggle |
| `vmem toggle on` | Enable auto-save |
| `vmem toggle off` | Disable auto-save |
| `vmem ping` | Check server connectivity |
| `vmem history` | Show recent saves |
| `vmem delete --duplicates` | Remove duplicate entries |
| `vmem delete --days 30` | Remove entries >30 days old |
| `vmem delete --dry-run` | Preview without deleting |
| `vmem delete compact --all` | Remove all compacts |
| `vmem delete compact --all --dry-run` | Preview compact removal |
| `vmem delete compact --older-than 7` | Remove compacts >7 days old |
| `vmem compact "text"` | Save project snapshot (max 10) |
| `vmem retrieve compact` | Get recent compact |
| `vmem retrieve compact --all` | List all compacts |
| `vmem delete compact 2` | Delete compact at index 2 |
| `vmem init` | Initialize project |
| `vmem init on` | Initialize + enable hooks |
| `vmem upgrade-docs` | Refresh docs to match CLI version |
| `vmem add-agent` | Add agent configs to existing project |
| `vmem hooks status` | Check hooks status |
| `vmem hooks on` | Enable hooks (Claude Code) |
| `vmem hooks off` | Disable hooks |
