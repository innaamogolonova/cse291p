#!/usr/bin/env bash
set -euo pipefail

# Requirements:
# - git
# - python3 (optional)
# - sqlite3
# - docker

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ARVO_DIR="${ROOT_DIR}/data/arvo"
META_DIR="${ARVO_DIR}/ARVO-Meta"
DB_PATH="${ARVO_DIR}/arvo.db"

mkdir -p "${ARVO_DIR}"

echo "==> Step 1: Download arvo.db to ${DB_PATH}"
if command -v gh >/dev/null 2>&1; then
  # Prefer GitHub CLI for a stable asset download by name
  gh release download -R n132/ARVO-Meta -p "arvo.db" -D "${ARVO_DIR}"
else
  echo "GitHub CLI not found. Please download 'arvo.db' from the ARVO-Meta Releases page"
  echo "and place it at: ${DB_PATH}"
  if [[ ! -f "${DB_PATH}" ]]; then
    echo "arvo.db not found. Aborting."
    exit 1
  fi
fi

ls -lh "${DB_PATH}"

echo "==> Step 2: clone ARVO_Meta"
if [[ ! -d "${META_DIR}" ]]; then
  git clone https://github.com/n132/ARVO-Meta.git "${META_DIR}"

else
  echo "ARVO-Meta already present, updating..."
  (cd "${META_DIR}" && git fetch --all --tags && git pull)
fi

echo "==> Step 3: Quick sanity checks"
sqlite3 "${DB_PATH}" ".tables" || { echo "sqlite3 check failed"; exit 1; }
ls "${META_DIR}/meta" | head || true
ls "${META_DIR}/patches" | head || true

echo "All set."
