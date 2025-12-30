# Claude Code Hooks Setup

## Files in this folder:

| File                   | Purpose                                       |
| ---------------------- | --------------------------------------------- |
| `settings.json`        | Hook config → copy to `.claude/settings.json` |
| `vmem-pre-query.sh`    | Auto-query vmem → copy to `~/.vmem/`          |
| `vmem-post-save.sh`    | Suggest saving → copy to `~/.vmem/`           |
| `hooks-integration.md` | Full documentation                            |

## Quick Setup

```bash
# 1. Copy hook scripts to ~/.vmem/
cp vmem-pre-query.sh ~/.vmem/
cp vmem-post-save.sh ~/.vmem/

# 2. Make executable
chmod +x ~/.vmem/*.sh

# 3. Copy settings to your project's .claude folder
cp settings.json /path/to/your/project/.claude/settings.json
```

**Note:** Shell scripts are installed globally in `~/.vmem/`. The settings.json is copied per-project to `.claude/settings.json`.

## To Disable Hooks

Remove or rename `.claude/settings.json` in the project.

## Note

- Hooks use `vmem status --json` for reliable mode detection
- Hooks are optional — the `.vmem.md` skill already provides auto-retrieval and auto-save through Claude's instructions
