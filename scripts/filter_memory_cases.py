#!/usr/bin/env python3
import json, re, shutil, os, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ARVO = ROOT / "data" / "arvo" / "ARVO-Meta"
META = ARVO / "meta"
PATCHES = ARVO / "patches"
OUT = ROOT / "data" / "arvo_filtered"
OUT_META = OUT / "meta"
OUT_PATCHES = OUT / "patches"
OUT_IDS = OUT / "memory_ids.txt"

# Memory-related patterns (lower-cased compare)
MEM_PATTERNS = [
    r"buffer[- ]?overflow",
    r"use[- ]?after[- ]?free",
    r"double[- ]?free",
    r"invalid[- ]?free",
    r"out[- ]?of[- ]?bounds",
    r"heap[- ]",
    r"stack[- ]",
]
MEM_RE = re.compile("|".join(MEM_PATTERNS))

def is_memory_bug(meta_obj):
    # Be permissive: sanitizer == asan OR crash_type matches patterns
    sanitizer = str(meta_obj.get("sanitizer", "")).lower()
    ctype = str(meta_obj.get("crash_type", "")).lower()
    if "asan" in sanitizer:
        return True
    if MEM_RE.search(ctype or ""):
        return True
    return False

def main():
    if not META.exists():
        print(f"Missing {META}. Run your prepare script first.", file=sys.stderr)
        sys.exit(1)

    OUT_META.mkdir(parents=True, exist_ok=True)
    OUT_PATCHES.mkdir(parents=True, exist_ok=True)

    kept = []
    for jpath in META.glob("*.json"):
        try:
            meta = json.loads(jpath.read_text(encoding="utf-8"))
        except Exception as e:
            print(f"Skip {jpath.name}: {e}", file=sys.stderr)
            continue

        if is_memory_bug(meta):
            case_id = str(meta.get("localId") or jpath.stem)
            kept.append(case_id)

            # copy meta/<id>.json
            shutil.copy2(jpath, OUT_META / jpath.name)

            # copy patches/<id>.diff if present
            dpath = PATCHES / f"{case_id}.diff"
            if dpath.exists():
                shutil.copy2(dpath, OUT_PATCHES / dpath.name)

    OUT_IDS.write_text("\n".join(sorted(kept)) + "\n", encoding="utf-8")
    print(f"Kept {len(kept)} memory cases.")
    print(f"- IDs written to: {OUT_IDS}")
    print(f"- Meta copied to: {OUT_META}")
    print(f"- Patches copied to: {OUT_PATCHES}")

if __name__ == "__main__":
    main()
