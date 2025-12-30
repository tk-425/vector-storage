# Claude Code Skills

Skills that teach Claude Code how to use vmem.

## Installation

```bash
cp -r skills/* ~/.claude/skills/
```

## Files

| Path                             | Purpose                    |
| -------------------------------- | -------------------------- |
| `skills/vmem/SKILL.md`           | vmem commands and behavior |
| `skills/vmem-codegraph/SKILL.md` | Combined vmem + code-graph |

## How It Works

Claude Code reads `~/.claude/skills/*/SKILL.md` files automatically and follows the instructions inside.

The vmem skill teaches Claude to:

- Query vmem before answering "how did we" questions
- Save summaries after completing work
- Use compact for project snapshots
