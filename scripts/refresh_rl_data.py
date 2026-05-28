#!/usr/bin/env python3
"""
Queries is_prod.rocketlane from Databricks and fully refreshes LIVE_RL_DATA
in index.html — projects list (progress, status, go_live_date, company_id)
AND brMap (integration-phase bank task subtask statuses).

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
from datetime import date

INDEX_HTML = os.path.join(os.path.dirname(__file__), "..", "index.html")
DBSQL = "https://{host}/api/2.0/sql/statements/"
POLL  = "https://{host}/api/2.0/sql/statements/{sid}"

SKIP_WORDS = ["test", "template", "mock", "trainer", "journey", "acme", "example", "matt pro"]


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
    return [dict(zip(cols, [
        (cell.get("string_value") if "string_value" in cell else None)
        for cell in row["values"]
    ])) for row in (data.get("result", {}).get("data_array") or [])]


def build_projects(project_rows, field_rows, task_rows, window_start, window_end):
    """Build the projects list with fresh data from all three tables."""
    # Index custom fields by project_id
    go_live_map = {}
    company_id_map = {}
    for f in field_rows:
        pid = str(f.get("project_id") or "")
        label = (f.get("label") or "").strip()
        val   = (f.get("value_label") or "").strip()
        if label.lower() == "go live date" and val:
            go_live_map[pid] = val
        if label.lower() == "companyid" and val:
            company_id_map[pid] = val

    # Build task counts per project (top-level tasks only)
    task_counts = {}
    for t in task_rows:
        pid = str(t.get("project_id") or "")
        if not pid:
            continue
        parent_id = t.get("parent_id") or ""
        if parent_id:
            continue  # skip subtasks
        tc = task_counts.setdefault(pid, {"total": 0, "done": 0})
        tc["total"] += 1
        status = (t.get("status_label") or "").lower()
        if status in ("completed", "complete", "done", "closed"):
            tc["done"] += 1

    projects_out = []
    for p in project_rows:
        pid  = str(p.get("id") or "")
        name = (p.get("name") or "").strip()
        customer = (p.get("customer_company_name") or name).strip()

        # Skip test/template projects
        name_lower = name.lower()
        cust_lower = customer.lower()
        if any(w in name_lower for w in SKIP_WORDS):
            continue
        if any(w in cust_lower for w in ["test", "acme", "example"]):
            continue

        # Go-live date: prefer custom field, fall back to due_date
        go_live = go_live_map.get(pid) or p.get("due_date") or ""

        # Filter to window
        if go_live and window_start and window_end:
            if not (window_start <= go_live[:10] <= window_end):
                continue

        tc = task_counts.get(pid, {"total": 0, "done": 0})
        projects_out.append({
            "id":                    pid,
            "name":                  name,
            "customer_company_name": customer,
            "status_label":          p.get("status_label") or "In Progress",
            "progress_percentage":   int(p.get("progress_percentage") or 0),
            "go_live_date":          go_live[:10] if go_live else None,
            "company_id":            company_id_map.get(pid, ""),
            "pre_gl_total":          tc["total"],
            "pre_gl_done":           tc["done"],
        })

    return projects_out


def build_br_map(task_rows, project_ids):
    """Build brMap: integration-phase parent tasks → subtask statuses."""
    by_project = {}
    for r in task_rows:
        pid = str(r.get("project_id") or "")
        if pid in project_ids:
            by_project.setdefault(pid, []).append(r)

    br_map = {}
    for pid, tasks in by_project.items():
        parents = {}
        for t in tasks:
            phase     = (t.get("phase_name") or "").lower()
            parent_id = t.get("parent_id") or ""
            if "integration" in phase and not parent_id:
                parents[str(t["task_id"])] = {
                    "name":     t.get("task_name") or "(unnamed)",
                    "start":    t.get("start_date") or None,
                    "subtasks": [],
                }
        for t in tasks:
            parent_id = t.get("parent_id") or ""
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


def patch_html(html: str, projects, br_map, today: str) -> str:
    m = re.search(r'const LIVE_RL_DATA = (\{.*?\});', html, re.DOTALL)
    if not m:
        raise ValueError("Could not locate LIVE_RL_DATA in index.html")
    existing = json.loads(m.group(1))
    existing["projects"]    = projects
    existing["brMap"]       = br_map
    existing["generatedAt"] = today
    new_json = json.dumps(existing, separators=(',', ':'))
    return html[:m.start(1)] + new_json + html[m.end(1):]


def main():
    host         = os.environ.get("DATABRICKS_HOST", "").strip().lstrip("https://").rstrip("/")
    warehouse_id = os.environ.get("DATABRICKS_WAREHOUSE_ID", "").strip()
    token        = os.environ.get("DATABRICKS_TOKEN", "").strip()

    if not all([host, warehouse_id, token]):
        print("ERROR: Set DATABRICKS_HOST, DATABRICKS_WAREHOUSE_ID, DATABRICKS_TOKEN")
        sys.exit(1)

    today        = date.today().isoformat()
    # Rolling 3-month window: current month through 2 months ahead
    year, month  = date.today().year, date.today().month
    end_month    = month + 2
    end_year     = year + (end_month - 1) // 12
    end_month    = ((end_month - 1) % 12) + 1
    window_start = f"{year}-{month:02d}-01"
    window_end   = f"{end_year}-{end_month:02d}-28"  # safe last day

    print(f"Window: {window_start} → {window_end}")

    # 1. Fetch projects
    print("Fetching projects...")
    project_sql = f"""
        SELECT
            CAST(p.id AS STRING)    AS id,
            p.name,
            p.customer_company_name,
            p.status_label,
            p.progress_percentage,
            CAST(p.due_date AS STRING) AS due_date
        FROM is_prod.rocketlane.project p
        WHERE p._fivetran_deleted = false
          AND p.archived = false
          AND p.due_date BETWEEN '{window_start}' AND '{window_end}'
        ORDER BY p.due_date, p.name
    """
    project_rows = run_query(host, warehouse_id, token, project_sql)
    print(f"  Got {len(project_rows)} project rows")

    # 2. Fetch custom fields
    print("Fetching custom fields (Go Live Date, CompanyID)...")
    field_sql = """
        SELECT CAST(project_id AS STRING) AS project_id, label, value_label
        FROM is_prod.rocketlane.project_field
        WHERE _fivetran_deleted = false
          AND label IN ('Go Live Date', 'CompanyID')
    """
    field_rows = run_query(host, warehouse_id, token, field_sql)
    print(f"  Got {len(field_rows)} field rows")

    # 3. Build project list (filter to window using Go Live Date custom field)
    projects = build_projects(project_rows, field_rows, [], window_start, window_end)
    project_ids = set(p["id"] for p in projects)
    print(f"  {len(projects)} projects in window after filtering")

    if not project_ids:
        print("ERROR: No projects found in window")
        sys.exit(1)

    # 4. Fetch tasks for those projects
    safe_ids = ", ".join(str(int(pid)) for pid in project_ids)
    print(f"Fetching tasks for {len(project_ids)} projects...")
    task_sql = f"""
        SELECT
            CAST(t.id              AS STRING) AS task_id,
            t.name                            AS task_name,
            t.status_label,
            CAST(t.project_id      AS STRING) AS project_id,
            CAST(t.parent_task_id  AS STRING) AS parent_id,
            t.phase_name,
            CAST(t.start_date      AS STRING) AS start_date,
            CAST(t.due_date        AS STRING) AS due_date
        FROM is_prod.rocketlane.task t
        WHERE t.project_id IN ({safe_ids})
          AND t._fivetran_deleted = false
        ORDER BY t.project_id, t.id
    """
    task_rows = run_query(host, warehouse_id, token, task_sql)
    print(f"  Got {len(task_rows)} task rows")

    # 5. Update task counts in projects (now that we have task data)
    projects = build_projects(project_rows, field_rows, task_rows, window_start, window_end)

    # 6. Build brMap
    br_map = build_br_map(task_rows, project_ids)
    print(f"  Built brMap for {len(br_map)} projects")

    # 7. Patch index.html
    with open(INDEX_HTML, "r", encoding="utf-8") as f:
        html = f.read()
    patched = patch_html(html, projects, br_map, today)
    with open(INDEX_HTML, "w", encoding="utf-8") as f:
        f.write(patched)

    print(f"\n✓ index.html updated — generatedAt={today}")
    print(f"  {len(projects)} projects, {len(br_map)} brMap entries")


if __name__ == "__main__":
    main()
