#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

PYTHON_BIN="${PYTHON_BIN:-python3}"
OUT_ZIP="${OUT_ZIP:-${ROOT_DIR}/lambda.zip}"
PKG_DIR="${PKG_DIR:-${ROOT_DIR}/package}"

if ! command -v "${PYTHON_BIN}" >/dev/null 2>&1; then
  echo "Error: ${PYTHON_BIN} not found. Set PYTHON_BIN or install Python 3." >&2
  exit 1
fi

if ! command -v zip >/dev/null 2>&1; then
  echo "Error: zip not found. Install zip (e.g., apt-get install zip)." >&2
  exit 1
fi

PYTHON_VERSION="$(${PYTHON_BIN} -c 'import sys; print("%d.%d" % sys.version_info[:2])')"
if [[ "${PYTHON_VERSION}" != "3.12" ]]; then
  echo "Warning: expected Python 3.12 for Lambda, found ${PYTHON_VERSION}." >&2
fi

rm -rf "${PKG_DIR}"
mkdir -p "${PKG_DIR}"

"${PYTHON_BIN}" -m pip install -r "${ROOT_DIR}/requirements.txt" -t "${PKG_DIR}"
cp -r "${ROOT_DIR}/app" "${PKG_DIR}/app"
cp "${ROOT_DIR}/lambda_handler.py" "${ROOT_DIR}/config.py" "${PKG_DIR}/"

( cd "${PKG_DIR}" && zip -r "${OUT_ZIP}" . )

echo "Built ${OUT_ZIP}"
