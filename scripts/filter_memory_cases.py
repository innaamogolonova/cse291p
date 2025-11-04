#!/usr/bin/env python3
import json
import csv
import os
import re

META_DIR = "data/arvo/ARVO-Meta/meta"
OUTPUT_CSV = "data/arvo/memory_cases_asan.csv"

# Define memory-safety crash types (case-insensitive substring match)
MEMORY_PATTERNS = [
    r"use[- ]?after[- ]?free",
    r"use[- ]?after[- ]?return",
    r"double[- ]?free",
    r"heap[- ]?buffer[- ]?overflow",
    r"stack[- ]?buffer[- ]?overflow",
    r"global[- ]?buffer[- ]?overflow",
    r"buffer[- ]?overflow",
    r"out[- ]?of[- ]?bounds",
    r"oob[- ]?(read|write)?",
    r"invalid[- ]?(read|write)",
    r"heap[- ]?use[- ]?after[- ]?free",
    r"stack[- ]?use[- ]?after[- ]?return",
    r"use[- ]?of[- ]?uninitialized",
    r"null[- ]?dereference",
]
MEMORY_REGEX = re.compile("|".join(MEMORY_PATTERNS), re.IGNORECASE)

rows = []
for fname in os.listdir(META_DIR):
    if not fname.endswith(".json"):
        continue
    path = os.path.join(META_DIR, fname)
    try:
        with open(path, "r") as f:
            data = json.load(f)
    except json.JSONDecodeError:
        print(f"Skipping invalid JSON: {fname}")
        continue

    local_id = data.get("localId")
    crash_type = data.get("crash_type") or ""
    sanitizer = (data.get("sanitizer") or "").lower()

    # Filter: sanitizer must be ASan, and crash_type must look like a memory bug
    if sanitizer == "asan" and MEMORY_REGEX.search(crash_type):
        rows.append({
            "localId": local_id,
            "crash_type": crash_type,
            "sanitizer": sanitizer,
        })

# Sort results by ID (numerically)
rows.sort(key=lambda r: (r["localId"] is None, r["localId"]))

# Write CSV
os.makedirs(os.path.dirname(OUTPUT_CSV), exist_ok=True)
with open(OUTPUT_CSV, "w", newline="") as csvfile:
    fieldnames = ["localId", "crash_type", "sanitizer"]
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows)

print(f"✅ Wrote {len(rows)} ASan memory bugs to {OUTPUT_CSV}")
