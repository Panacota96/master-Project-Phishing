#!/bin/bash
# PostToolUse hook: validate answer_key.py structure after edits.
# Checks that every ANSWER_KEY entry has 'classification' and 'signals' keys.

INPUT=$(cat)
FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // empty')

# Only trigger for answer_key.py
if [[ "$FILE_PATH" != *answer_key.py ]]; then
  exit 0
fi

if [[ ! -f "$FILE_PATH" ]]; then
  exit 0
fi

python3 - "$FILE_PATH" <<'PYEOF'
import sys, ast

path = sys.argv[1]
with open(path) as f:
    source = f.read()

try:
    tree = ast.parse(source)
except SyntaxError as e:
    print(f"Syntax error: {e}", file=sys.stderr)
    sys.exit(2)

# Find the ANSWER_KEY dict assignment
answer_key = None
for node in ast.walk(tree):
    if isinstance(node, ast.Assign):
        for target in node.targets:
            if isinstance(target, ast.Name) and target.id == 'ANSWER_KEY':
                answer_key = node.value

if answer_key is None:
    print("WARNING: ANSWER_KEY not found in answer_key.py", file=sys.stderr)
    sys.exit(0)

errors = []
if isinstance(answer_key, ast.Dict):
    for key_node, val_node in zip(answer_key.keys, answer_key.values):
        if not isinstance(key_node, ast.Constant):
            continue
        filename = key_node.value
        if not isinstance(val_node, ast.Dict):
            errors.append(f"{filename}: value must be a dict")
            continue
        keys_present = set()
        for k in val_node.keys:
            if isinstance(k, ast.Constant):
                keys_present.add(k.value)
        missing = {'classification', 'signals'} - keys_present
        if missing:
            errors.append(f"{filename}: missing keys {missing}")

if errors:
    print("answer_key.py validation errors:", file=sys.stderr)
    for e in errors:
        print(f"  - {e}", file=sys.stderr)
    sys.exit(2)

print(f"answer_key.py OK ({len(answer_key.keys)} entries)")
PYEOF
