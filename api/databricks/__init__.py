import azure.functions as func
import json
import os
import logging
import requests
import time

DBSQL_API = "https://{host}/api/2.0/sql/statements/"
POLL_API  = "https://{host}/api/2.0/sql/statements/{sid}"


def _run_query(host: str, warehouse_id: str, token: str, sql: str, params: list = None):
    """
    Execute a SQL statement via Databricks Statement Execution API.
    Polls until completion (max ~60 s). Returns list of row dicts.
    """
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    body = {
        "warehouse_id": warehouse_id,
        "statement":    sql,
        "wait_timeout": "50s",
        "on_wait_timeout": "CANCEL",
        "format": "JSON_ARRAY",
        "disposition": "INLINE",
    }
    if params:
        body["parameters"] = params

    url = DBSQL_API.format(host=host)
    resp = requests.post(url, headers=headers, json=body, timeout=60)
    resp.raise_for_status()
    data = resp.json()

    # Poll if still running
    for _ in range(20):
        state = data.get("status", {}).get("state", "")
        if state in ("SUCCEEDED", "FAILED", "CANCELED", "CLOSED"):
            break
        sid = data["statement_id"]
        time.sleep(3)
        r = requests.get(POLL_API.format(host=host, sid=sid), headers=headers, timeout=30)
        r.raise_for_status()
        data = r.json()

    state = data.get("status", {}).get("state", "")
    if state != "SUCCEEDED":
        err = data.get("status", {}).get("error", {}).get("message", state)
        raise RuntimeError(f"Query failed: {err}")

    manifest = data.get("manifest", {})
    schema   = manifest.get("schema", {}).get("columns", [])
    col_names = [c["name"] for c in schema]

    rows = []
    for row in (data.get("result", {}).get("data_array") or []):
        rows.append(dict(zip(col_names, row)))
    return rows


def _build_br_map(rows: list) -> dict:
    """
    Convert flat task rows into the brMap structure the dashboard expects:
    { projectId: { taskName: { rlTaskId, taskStart, items: [{id, name, rlStatus}] } } }
    """
    # Group tasks by project
    by_project: dict[str, list] = {}
    for r in rows:
        pid = str(r.get("project_id") or "")
        if pid:
            by_project.setdefault(pid, []).append(r)

    br_map: dict[str, dict] = {}
    for pid, tasks in by_project.items():
        # Index all tasks so we can look up by parent_id
        by_id = {str(t.get("task_id") or ""): t for t in tasks}

        # Parent tasks: in the Integrations phase and have no parent
        parents: dict[str, dict] = {}
        for t in tasks:
            phase = (t.get("phase_name") or "").lower()
            parent_id = str(t.get("parent_id") or "") if t.get("parent_id") is not None else ""
            if "integration" in phase and not parent_id:
                parents[str(t["task_id"])] = {
                    "name":     t.get("task_name") or "(unnamed)",
                    "start":    t.get("start_date") or None,
                    "subtasks": [],
                }

        # Subtasks: their parent_id points to a known integration parent
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


def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("Databricks function triggered")

    try:
        body       = req.get_json()
        operation  = body.get("operation", "getBankReadiness")
        project_ids = body.get("projectIds", [])

        host         = os.environ.get("DATABRICKS_HOST", "").strip().lstrip("https://").rstrip("/")
        warehouse_id = os.environ.get("DATABRICKS_WAREHOUSE_ID", "").strip()
        token        = os.environ.get("DATABRICKS_TOKEN", "").strip()

        if not all([host, warehouse_id, token]):
            return func.HttpResponse(
                json.dumps({"error": "Missing Databricks configuration (DATABRICKS_HOST, DATABRICKS_WAREHOUSE_ID, DATABRICKS_TOKEN)"}),
                status_code=500,
                mimetype="application/json",
            )

        if operation == "getBankReadiness":
            if not project_ids:
                return func.HttpResponse(
                    json.dumps({"error": "Missing projectIds"}),
                    status_code=400,
                    mimetype="application/json",
                )

            # Build a safe IN clause — project IDs are integers in Rocketlane
            safe_ids = [str(int(pid)) for pid in project_ids]
            placeholders = ", ".join(safe_ids)

            sql = f"""
                SELECT
                    CAST(t.id          AS STRING) AS task_id,
                    t.name                        AS task_name,
                    t.status_label                AS status_label,
                    CAST(t.project_id  AS STRING) AS project_id,
                    CAST(t.parent_id   AS STRING) AS parent_id,
                    t.phase_name                  AS phase_name,
                    CAST(t.start_date  AS STRING) AS start_date
                FROM is_prod.rocketlane.task t
                WHERE t.project_id IN ({placeholders})
                  AND t._fivetran_deleted = false
                ORDER BY t.project_id, t.id
            """

            rows   = _run_query(host, warehouse_id, token, sql)
            br_map = _build_br_map(rows)

            return func.HttpResponse(
                json.dumps({"status": {"state": "SUCCEEDED"}, "brMap": br_map}),
                status_code=200,
                mimetype="application/json",
            )

        else:
            return func.HttpResponse(
                json.dumps({"error": f"Unknown operation: {operation}"}),
                status_code=400,
                mimetype="application/json",
            )

    except requests.exceptions.RequestException as e:
        logging.error(f"Databricks HTTP error: {e}")
        return func.HttpResponse(
            json.dumps({"error": f"Databricks HTTP error: {str(e)}"}),
            status_code=500,
            mimetype="application/json",
        )
    except Exception as e:
        logging.error(f"Error in Databricks function: {e}")
        return func.HttpResponse(
            json.dumps({"error": str(e)}),
            status_code=500,
            mimetype="application/json",
        )
