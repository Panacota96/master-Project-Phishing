#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

PYTHON_BIN="${PYTHON_BIN:-python3}"
OUT_ZIP="${OUT_ZIP:-${ROOT_DIR}/campaign_mailer.zip}"
PKG_DIR="${PKG_DIR:-${ROOT_DIR}/campaign_mailer_package}"

if ! command -v "${PYTHON_BIN}" >/dev/null 2>&1; then
  echo "Error: ${PYTHON_BIN} not found." >&2
  exit 1
fi

if ! command -v zip >/dev/null 2>&1; then
  echo "Error: zip not found. Install zip (e.g., apt-get install zip)." >&2
  exit 1
fi

rm -rf "${PKG_DIR}"
mkdir -p "${PKG_DIR}"

"${PYTHON_BIN}" -m pip install -r "${ROOT_DIR}/campaign_mailer/requirements.txt" -t "${PKG_DIR}"
cp "${ROOT_DIR}/campaign_mailer/handler.py" "${PKG_DIR}/"

( cd "${PKG_DIR}" && zip -r "${OUT_ZIP}" . )

echo "Built ${OUT_ZIP}"
