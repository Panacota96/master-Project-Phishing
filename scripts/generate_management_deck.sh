#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MD_FILE="${ROOT_DIR}/management_deck.md"

if [[ ! -f "${MD_FILE}" ]]; then
  echo "Error: ${MD_FILE} not found." >&2
  exit 1
fi

command -v python3 >/dev/null 2>&1 || {
  echo "Error: python3 not found." >&2
  exit 1
}

command -v marp >/dev/null 2>&1 || command -v marp-cli >/dev/null 2>&1 || {
  echo "Error: marp-cli not found. Install with: npm i -g @marp-team/marp-cli" >&2
  exit 1
}

PY_PPTX_CHECK="import importlib.util; exit(0) if importlib.util.find_spec('pptx') else exit(1)"
if ! python3 -c "${PY_PPTX_CHECK}"; then
  echo "Error: python-pptx not installed. Install with: python3 -m pip install python-pptx" >&2
  exit 1
fi

${ROOT_DIR}/scripts/generate_management_deck.py

if command -v marp >/dev/null 2>&1; then
  marp "${MD_FILE}" -o "${ROOT_DIR}/management_deck.pdf"
else
  marp-cli "${MD_FILE}" -o "${ROOT_DIR}/management_deck.pdf"
fi

echo "Generated management_deck.pptx and management_deck.pdf"
