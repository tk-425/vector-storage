#!/bin/bash
# vmem-post-save.sh
# Runs on Stop - suggests saving to vmem after Claude finishes
#
# Location: ./.claude/hooks/vmem-post-save.sh
# Make executable: chmod +x vmem-post-save.sh

# Read input from Claude Code (JSON via stdin)
INPUT=$(cat)

# Extract stop reason
STOP_REASON=$(echo "$INPUT" | jq -r '.stop_reason // empty')

# Only trigger on normal completion (not errors or interrupts)
if [ "$STOP_REASON" != "end_turn" ]; then
  echo '{"result": "continue"}'
  exit 0
fi

# Check if vmem auto-save is enabled (using JSON for reliable parsing)
MODE=$(vmem status --json 2>/dev/null | jq -r '.mode // "off"')

case "$MODE" in
  "on")
    # Auto-save is on - remind Claude to save
    echo '{"result": "continue", "message": "[vmem: Auto-save is ON. Save implementation summary if work was done.]"}'
    ;;
  "prompt")
    # Prompt mode - ask user
    echo '{"result": "continue", "message": "[vmem: Should I save this to vector memory?]"}'
    ;;
  *)
    # Off or unknown - do nothing
    echo '{"result": "continue"}'
    ;;
esac
