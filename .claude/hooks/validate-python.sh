#!/bin/bash
# PostToolUse hook: syntax-check any .py file Claude just wrote or edited.
# Runs automatically after Edit and Write tool calls.

INPUT=$(cat)
FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // empty')

# Only process .py files
if [[ "$FILE_PATH" != *.py ]]; then
  exit 0
fi

# File must exist
if [[ ! -f "$FILE_PATH" ]]; then
  exit 0
fi

TMPFILE=$(mktemp)
if python3 -m py_compile "$FILE_PATH" 2>"$TMPFILE"; then
  rm -f "$TMPFILE"
  exit 0
else
  ERR=$(cat "$TMPFILE")
  rm -f "$TMPFILE"
  echo "Python syntax error in $FILE_PATH:" >&2
  echo "$ERR" >&2
  # Exit 2 signals Claude to treat this as a blocking error and fix it
  exit 2
fi
