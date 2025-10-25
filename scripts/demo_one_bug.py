#!/usr/bin/env python3
import sqlite3, json, os, sys

DB = os.path.join("data", "arvo", "arvo.db")

def find_table_with_id(conn):
    cur = conn.cursor()
    tables = [r[0] for r in cur.execute("SELECT name FROM sqlite_master WHERE type='table'")]
    # Heuristics: prefer 'records', 'cases', 'vulns', then first non-sqlite table
    preferred = [t for t in tables if t.lower() in ("records", "cases", "vulns", "meta")]
    if preferred:
        return preferred[0]
    for t in tables:
        if not t.startswith("sqlite_"):
            return t
    raise RuntimeError("No usable tables found")

def pick_one_c_cpp_row(conn, table):
    cur = conn.cursor()
    # Try a few likely column names for filtering/IDs
    cols = [c[1] for c in cur.execute(f"PRAGMA table_info({table})")]
    id_col = "id" if "id" in cols else (cols[0] if cols else "id")
    lang_cols = [c for c in cols if c.lower() in ("lang","language","project_lang","proj_lang")]
    # Build a simple SELECT
    if lang_cols:
        lang_col = lang_cols[0]
        q = f"SELECT * FROM {table} WHERE {lang_col} LIKE '%C%+' OR {lang_col} LIKE '%C++%' LIMIT 1"
    else:
        q = f"SELECT * FROM {table} LIMIT 1"
    row = cur.execute(q).fetchone()
    if not row:
        raise RuntimeError("No rows found (try removing the language filter).")
    return cols, row

def main():
    if not os.path.exists(DB):
        print("Missing data/arvo/arvo.db – download from ARVO-Meta Releases first.", file=sys.stderr)
        sys.exit(1)
    conn = sqlite3.connect(DB)
    table = find_table_with_id(conn)
    cols, row = pick_one_c_cpp_row(conn, table)
    data = dict(zip(cols, row))
    # Try to find a case identifier; fallback to the first column
    case_id = str(data.get("id", data.get("case_id", data.get(cols[0]))))
    print("Picked case:", case_id)
    print("Row (truncated keys):", {k: data[k] for k in list(data)[:8]})
    # Docker tags per README convention:
    print("Try these Docker commands:")
    print(f"  docker run -it n132/arvo:{case_id}-vul arvo")
    print(f"  docker run -it n132/arvo:{case_id}-fix arvo")

if __name__ == "__main__":
    main()
