#!/usr/bin/env python3
"""
Queries is_prod.rocketlane.task from Databricks and patches LIVE_RL_DATA
(the brMap section) inside index.html in-place.

Usage:
  python scripts/refresh_rl_data.py

Required env vars:
  DATABRICKS_HOST          e.g. adb-xxxx.azuredatabricks.net
  DATABRICKS_WAREHOUSE_ID  SQL warehouse ID
  DATABRICKS_TOKEN         personal access token
"""
import json
import os
import re
import sys
import time
import requests

DBSQL = "https://{host}/api/2.0/sql/statements/"
POLL  = "https://{host}/api/2.0/sql/statements/{sid}"

INDEX_HTML = os.path.join(os.path.dirname(__file__), "..", "index.html")


def run_query(host, warehouse_id, token, sql):
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    body = {
        "warehouse_id": warehouse_id,
        "statement": sql,
        "wait_timeout": "50s",
        "on_wait_timeout": "CANCEL",
        "format": "JSON_ARRAY",
        "disposition": "INLINE",
    }
    resp = requests.post(DBSQL.format(host=host), headers=headers, json=body, timeout=60)
    resp.raise_for_status()
    data = resp.json()

    for _ in range(20):
        state = data.get("status", {}).get("state", "")
        if state in ("SUCCEEDED", "FAILED", "CANCELED", "CLOSED"):
            break
        sid = data["statement_id"]
        time.sleep(3)
        r = requests.get(POLL.format(host=host, sid=sid), headers=headers, timeout=30)
        r.raise_for_status()
        data = r.json()

    state = data.get("status", {}).get("state", "")
    if state != "SUCCEEDED":
        err = data.get("status", {}).get("error", {}).get("message", state)
        raise RuntimeError(f"Query failed: {err}")

    cols = [c["name"] for c in data["manifest"]["schema"]["columns"]]
    return [dict(zip(cols, row)) for row in (data.get("result", {}).get("data_array") or [])]


def build_br_map(rows):
    by_project = {}
    for r in rows:
        pid = str(r.get("project_id") or "")
        if pid:
            by_project.setdefault(pid, []).append(r)

    br_map = {}
    for pid, tasks in by_project.items():
        by_id = {str(t.get("task_id") or ""): t for t in tasks}

        parents = {}
        for t in tasks:
            phase = (t.get("phase_name") or "").lower()
            parent_id = str(t.get("parent_id") or "") if t.get("parent_id") is not None else ""
            if "integration" in phase and not parent_id:
                parents[str(t["task_id"])] = {
                    "name":     t.get("task_name") or "(unnamed)",
                    "start":    t.get("start_date") or None,
                    "subtasks": [],
                }

        for t in tasks:
            parent_id = str(t.get("parent_id") or "") if t.get("parent_id") is not None else ""
            if parent_id and parent_id in parents:
                parents[parent_id]["subtasks"].append({
                    "id":       str(t.get("task_id") or ""),
                    "name":     t.get("task_name") or "(unnamed)",
                    "rlStatus": t.get("status_label") or "To do",
                })

        br_map[pid] = {
            meta["name"]: {
                "rlTaskId":  tid,
                "taskStart": meta["start"],
                "items":     meta["subtasks"],
            }
            for tid, meta in parents.items()
        }
    return br_map


def patch_html(html: str, new_br_map: dict, today: str) -> str:
    # Replace only the brMap value and the generatedAt date inside LIVE_RL_DATA
    # Strategy: parse the existing LIVE_RL_DATA JSON, merge, write back.
    m = re.search(r'const LIVE_RL_DATA = (\{.*?\});', html, re.DOTALL)
    if not m:
        raise ValueError("Could not locate LIVE_RL_DATA in index.html")

    existing = json.loads(m.group(1))
    existing["brMap"] = new_br_map
    existing["generatedAt"] = today

    new_json = json.dumps(existing, separators=(',', ':'))
    patched  = html[:m.start(1)] + new_json + html[m.end(1):]
    return patched


def main():
    host         = os.environ.get("DATABRICKS_HOST", "").strip().lstrip("https://").rstrip("/")
    warehouse_id = os.environ.get("DATABRICKS_WAREHOUSE_ID", "").strip()
    token        = os.environ.get("DATABRICKS_TOKEN", "").strip()

    if not all([host, warehouse_id, token]):
        print("ERROR: Set DATABRICKS_HOST, DATABRICKS_WAREHOUSE_ID, DATABRICKS_TOKEN")
        sys.exit(1)

    print("Fetching project IDs from LIVE_RL_DATA...")
    with open(INDEX_HTML, "r", encoding="utf-8") as f:
        html = f.read()

    m = re.search(r'const LIVE_RL_DATA = (\{.*?\});', html, re.DOTALL)
    if not m:
        print("ERROR: LIVE_RL_DATA not found in index.html")
        sys.exit(1)

    existing    = json.loads(m.group(1))
    project_ids = [str(p["id"]) for p in existing.get("projects", [])]
    if not project_ids:
        print("ERROR: No projects found in LIVE_RL_DATA")
        sys.exit(1)

    print(f"Querying Databricks for {len(project_ids)} projects...")
    safe_ids = ", ".join(str(int(pid)) for pid in project_ids)
    sql = f"""
        SELECT
            CAST(t.id         AS STRING) AS task_id,
            t.name                       AS task_name,
            t.status_label               AS status_label,
            CAST(t.project_id AS STRING) AS project_id,
            CAST(t.parent_id  AS STRING) AS parent_id,
            t.phase_name                 AS phase_name,
            CAST(t.start_date AS STRING) AS start_date
        FROM is_prod.rocketlane.task t
        WHERE t.project_id IN ({safe_ids})
          AND t._fivetran_deleted = false
        ORDER BY t.project_id, t.id
    """

    rows = run_query(host, warehouse_id, token, sql)
    print(f"  Got {len(rows)} task rows")

    br_map = build_br_map(rows)
    print(f"  Built brMap for {len(br_map)} projects")

    from datetime import date
    today   = date.today().isoformat()
    patched = patch_html(html, br_map, today)

    with open(INDEX_HTML, "w", encoding="utf-8") as f:
        f.write(patched)

    print(f"index.html updated — generatedAt={today}")


if __name__ == "__main__":
    main()
