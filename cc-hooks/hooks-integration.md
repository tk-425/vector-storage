# Claude Code Hooks for vmem

**Status:** Not yet implemented - documentation only

This document explains how Claude Code hooks could integrate with vmem for automatic context retrieval and saving.

---

## What Are Hooks?

Claude Code hooks are shell commands that run automatically at specific events:

| Hook Event           | When it runs                    | vmem use case               |
| -------------------- | ------------------------------- | --------------------------- |
| **UserPromptSubmit** | When user submits a message     | Auto-query vmem for context |
| **Stop**             | When Claude finishes responding | Auto-save summary           |
| **PostToolUse**      | After Claude uses a tool        | Track what was done         |

---

## Hook Configuration

Hooks are configured in `~/.claude/settings.json`:

```json
{
  "hooks": {
    "UserPromptSubmit": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "~/.claude/hooks/vmem-pre-query.sh"
          }
        ]
      }
    ],
    "Stop": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "~/.claude/hooks/vmem-post-save.sh"
          }
        ]
      }
    ]
  }
}
```

---

## Hook Scripts

### Pre-Query Hook (UserPromptSubmit)

**File:** `~/.claude/hooks/vmem-pre-query.sh`

```bash
#!/bin/bash
# Runs when user submits a message
# Reads user prompt from stdin as JSON

INPUT=$(cat)
USER_MESSAGE=$(echo "$INPUT" | jq -r '.prompt // empty')

if [ -n "$USER_MESSAGE" ]; then
  # Extract keywords and query vmem
  KEYWORDS=$(echo "$USER_MESSAGE" | head -c 100)
  RESULTS=$(vmem search "$KEYWORDS" 2>/dev/null)

  if [ -n "$RESULTS" ]; then
    # Output JSON to inject context
    echo "{\"result\": \"continue\", \"message\": \"Context from vmem: $RESULTS\"}"
  fi
fi
```

### Post-Save Hook (Stop)

**File:** `~/.claude/hooks/vmem-post-save.sh`

```bash
#!/bin/bash
# Runs when Claude finishes responding
# Could suggest saving based on conversation

INPUT=$(cat)
STOP_REASON=$(echo "$INPUT" | jq -r '.stop_reason // empty')

# Only trigger on normal stops (not errors)
if [ "$STOP_REASON" = "end_turn" ]; then
  # Check if auto-save is on
  MODE=$(vmem status 2>/dev/null | grep "Auto-save mode" | awk '{print $NF}')

  if [ "$MODE" = "on" ]; then
    echo "{\"result\": \"continue\", \"message\": \"[vmem: Consider saving this if implementation was done]\"}"
  fi
fi
```

---

## Usage Examples

### Example 1: Auto-Context Before Question

**Without hooks:**

```
User: "How did we implement authentication?"
Claude: [Doesn't know, asks for context]
```

**With UserPromptSubmit hook:**

```
User: "How did we implement authentication?"
[Hook runs: vmem search "authentication"]
[Hook injects: "Context: JWT with httpOnly cookies, 24hr expiration"]
Claude: "Based on our previous work, you implemented JWT authentication with..."
```

### Example 2: Auto-Save Reminder After Work

**Without hooks:**

```
User: "Add password reset"
Claude: [Implements password reset]
Claude: "Done!"
[Nothing saved - context lost]
```

**With Stop hook:**

```
User: "Add password reset"
Claude: [Implements password reset]
[Hook runs: checks vmem status → "on"]
[Hook injects: "Consider saving: password reset implementation"]
Claude: "Done! I've saved the implementation details to vector memory."
```

### Example 3: PostToolUse for Write Operations

**Hook config for tracking file writes:**

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Write",
        "hooks": [
          {
            "type": "command",
            "command": "echo '{\"result\": \"continue\"}'"
          }
        ]
      }
    ]
  }
}
```

**Flow:**

```
Claude: [Writes to src/auth.ts]
[PostToolUse hook runs for "Write" tool]
[Could log or trigger vmem save for file changes]
```

---

## Comparison: Hooks vs .vmem.md

| Approach     | Automation                  | Control | Complexity |
| ------------ | --------------------------- | ------- | ---------- |
| **Hooks**    | Forced (always runs)        | Low     | High       |
| **.vmem.md** | Instructed (Claude decides) | High    | Low        |

**Current recommendation:** Use `.vmem.md` for now. Hooks add complexity without clear benefit since Claude already follows `.vmem.md` instructions.

---

## Implementation Status

- [ ] Pre-query hook script
- [ ] Post-save hook script
- [ ] settings.json configuration
- [ ] Testing and validation

**Note:** These hooks are optional. The `.vmem.md` skill file already provides auto-retrieval and auto-save behavior through instructions rather than forced automation.
