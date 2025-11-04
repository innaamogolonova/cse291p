#!/usr/bin/env bash
set -euo pipefail

CASE_ID="$1"  # e.g. 25402

# 1. Create containers (but do not run them yet)
VULN_CID=$(docker create "n132/arvo:${CASE_ID}-vul")
FIX_CID=$(docker create "n132/arvo:${CASE_ID}-fix")

# 2. Prepare output dir
OUT_DIR="data/cases/${CASE_ID}"
mkdir -p "${OUT_DIR}"

# 3. Copy source trees out of each container
docker cp "$VULN_CID":/src  "${OUT_DIR}/buggy_src"  2>/dev/null || \
docker cp "$VULN_CID":/work "${OUT_DIR}/buggy_src" 2>/dev/null || \
echo "warning: could not find buggy_src for $CASE_ID"

docker cp "$FIX_CID":/src   "${OUT_DIR}/fixed_src"  2>/dev/null || \
docker cp "$FIX_CID":/work  "${OUT_DIR}/fixed_src" 2>/dev/null || \
echo "warning: could not find fixed_src for $CASE_ID"

# (optional) PoC input etc
docker cp "$VULN_CID":/poc        "${OUT_DIR}/poc"         2>/dev/null || true
docker cp "$VULN_CID":/arvo       "${OUT_DIR}/arvo_runner" 2>/dev/null || true

# 4. Clean up temp containers
docker rm "$VULN_CID" "$FIX_CID"
