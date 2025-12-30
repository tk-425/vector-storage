#!/bin/bash
# vmem-pre-query.sh
# Runs on UserPromptSubmit - queries vmem for relevant context
#
# Location: ./.claude/hooks/vmem-pre-query.sh
# Make executable: chmod +x vmem-pre-query.sh

# Read input from Claude Code (JSON via stdin)
INPUT=$(cat)

# Extract user message
USER_MESSAGE=$(echo "$INPUT" | jq -r '.prompt // empty')

# Exit early if no message
if [ -z "$USER_MESSAGE" ]; then
  echo '{"result": "continue"}'
  exit 0
fi

# Check if vmem auto-save is enabled (using JSON for reliable parsing)
MODE=$(vmem status --json 2>/dev/null | jq -r '.mode // "off"')

if [ "$MODE" = "off" ]; then
  # Auto-save off = skip auto-retrieval too
  echo '{"result": "continue"}'
  exit 0
fi

# Extract keywords (first 100 chars)
KEYWORDS=$(echo "$USER_MESSAGE" | head -c 100)

# Query vmem for context
RESULTS=$(vmem search "$KEYWORDS" 2>/dev/null)

if [ -n "$RESULTS" ] && [ "$RESULTS" != "No results found" ]; then
  # Inject context into Claude's response
  # Escape for JSON
  ESCAPED_RESULTS=$(echo "$RESULTS" | jq -Rs '.')
  echo "{\"result\": \"continue\", \"message\": \"[vmem context]: $ESCAPED_RESULTS\"}"
else
  echo '{"result": "continue"}'
fi
