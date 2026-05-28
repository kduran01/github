import azure.functions as func
import json
import os
import logging
import requests
from datetime import datetime, timedelta

RL_BASE = "https://api.rocketlane.com/api/1.0"

def rl_get(path, params, api_key):
    """Make a GET request to Rocketlane API and return parsed JSON."""
    headers = {
        "api-key": api_key,
        "Accept": "application/json",
    }
    url = f"{RL_BASE}{path}"
    resp = requests.get(url, headers=headers, params=params, timeout=30)
    resp.raise_for_status()
    return resp.json()

def paginate(path, base_params, api_key, max_pages=20):
    """Collect all pages from a Rocketlane paginated endpoint."""
    items = []
    page_token = None
    for _ in range(max_pages):
        params = {**base_params, "pageSize": 100}
        if page_token:
            params["pageToken"] = page_token
        data = rl_get(path, params, api_key)
        batch = data.get("data") or data.get("result") or []
        items.extend(batch)
        page_token = data.get("pagination", {}).get("nextPageToken") or data.get("nextPageToken")
        if not page_token:
            break
    return items

def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("Rocketlane function triggered")

    try:
        body = req.get_json()
        operation = body.get("operation", "getProjects")

        api_key = os.environ.get("ROCKETLANE_API_KEY")
        if not api_key:
            return func.HttpResponse(
                json.dumps({"error": "Missing ROCKETLANE_API_KEY configuration"}),
                status_code=500,
                mimetype="application/json",
            )

        # ── GET PROJECTS ──────────────────────────────────────────────────────
        # Returns projects within the rolling 3-month window (current + next 2 months),
        # including go-live date (custom field), company ID, progress, and pre-GL task counts.
        if operation == "getProjects":
            window_start = body.get("windowStart")  # YYYY-MM-DD
            window_end   = body.get("windowEnd")    # YYYY-MM-DD

            # Fetch all active projects with progress
            projects_raw = paginate(
                "/projects",
                {
                    "includeFields": "progressPercentage,currentPhase",
                    "includeAllFields": "false",
                },
                api_key,
            )

            # Fetch custom fields index to find Go Live Date and CompanyID field IDs
            fields_raw = rl_get("/fields", {}, api_key)
            fields_list = fields_raw.get("data") or fields_raw.get("result") or []
            go_live_field_id = None
            company_id_field_id = None
            for f in fields_list:
                label = (f.get("name") or f.get("label") or "").strip()
                if label.lower() == "go live date":
                    go_live_field_id = f.get("id")
                if label.lower() == "companyid":
                    company_id_field_id = f.get("id")

            results = []
            for p in projects_raw:
                pid = str(p.get("id") or p.get("projectId") or "")
                name = p.get("name") or p.get("projectName") or ""
                customer = p.get("customerCompanyName") or p.get("companyName") or name
                status = p.get("status") or p.get("statusLabel") or "In Progress"
                progress = p.get("progressPercentage") or 0

                # Skip test/template projects
                skip_words = ["test", "template", "mock", "trainer", "journey", "acme"]
                if any(w in name.lower() for w in skip_words):
                    continue
                if any(w in (customer or "").lower() for w in ["test", "acme"]):
                    continue

                # Extract custom fields from the project object
                custom_fields = p.get("customFields") or p.get("fields") or []
                go_live_date = None
                company_id_val = None
                for cf in custom_fields:
                    cf_id  = str(cf.get("fieldId") or cf.get("id") or "")
                    cf_val = cf.get("value") or ""
                    if go_live_field_id and cf_id == str(go_live_field_id):
                        go_live_date = cf_val
                    if company_id_field_id and cf_id == str(company_id_field_id):
                        company_id_val = cf_val

                # Fall back to dueDate if no custom go-live field found
                if not go_live_date:
                    go_live_date = p.get("dueDate") or p.get("endDate") or ""

                # Filter by window
                if go_live_date and window_start and window_end:
                    if not (window_start <= go_live_date[:10] <= window_end):
                        continue

                results.append({
                    "id": pid,
                    "name": name,
                    "customer_company_name": customer,
                    "status_label": status,
                    "progress_percentage": progress,
                    "go_live_date": go_live_date[:10] if go_live_date else None,
                    "company_id": company_id_val or "",
                    # pre_gl_total/done filled by getTaskCounts call
                    "pre_gl_total": 0,
                    "pre_gl_done": 0,
                })

            return func.HttpResponse(
                json.dumps({"status": {"state": "SUCCEEDED"}, "projects": results}),
                status_code=200,
                mimetype="application/json",
            )

        # ── GET TEAM MEMBERS ──────────────────────────────────────────────────
        # Returns all team members for a list of project IDs.
        elif operation == "getTeamMembers":
            project_ids = body.get("projectIds", [])
            team_map = {}
            for pid in project_ids:
                try:
                    data = rl_get(f"/projects/{pid}", {"includeFields": "teamMembers"}, api_key)
                    members = (
                        data.get("teamMembers")
                        or data.get("data", {}).get("teamMembers")
                        or []
                    )
                    team_map[str(pid)] = [
                        {
                            "project_id": pid,
                            "first_name": m.get("firstName") or (m.get("name") or "").split()[0],
                            "last_name":  m.get("lastName")  or (" ".join((m.get("name") or "").split()[1:]) if len((m.get("name") or "").split()) > 1 else ""),
                            "email_id":   (m.get("email") or m.get("emailId") or "").lower().strip(),
                        }
                        for m in members
                        if m.get("email") or m.get("emailId")
                    ]
                except Exception as e:
                    logging.warning(f"Could not fetch team for project {pid}: {e}")
                    team_map[str(pid)] = []

            return func.HttpResponse(
                json.dumps({"status": {"state": "SUCCEEDED"}, "teamMap": team_map}),
                status_code=200,
                mimetype="application/json",
            )

        # ── GET BANK READINESS TASKS ─────────────────────────────────────────
        # Returns Integrations-phase tasks and their subtasks for a list of project IDs.
        elif operation == "getBankReadiness":
            project_ids = body.get("projectIds", [])
            br_map = {}

            for pid in project_ids:
                try:
                    # Get all tasks for this project
                    tasks = paginate(
                        "/tasks",
                        {"projectId": pid, "includeFields": "parentTask,phase,startDate,status"},
                        api_key,
                    )

                    # Index parent tasks in the Integrations phase
                    integrations_parents = {}
                    all_tasks_by_id = {}
                    for t in tasks:
                        tid = str(t.get("id") or t.get("taskId") or "")
                        all_tasks_by_id[tid] = t
                        phase_name = (t.get("phase") or {}).get("name") or t.get("phaseName") or ""
                        parent_id  = t.get("parentTaskId") or (t.get("parentTask") or {}).get("id")
                        if "integrations" in phase_name.lower() and not parent_id:
                            integrations_parents[tid] = {
                                "name":      t.get("name") or t.get("taskName") or "(unnamed)",
                                "start":     t.get("startDate") or "",
                                "status":    t.get("status") or t.get("statusLabel") or "Not Started",
                                "subtasks":  [],
                            }

                    # Attach subtasks
                    for t in tasks:
                        parent_id = str(t.get("parentTaskId") or (t.get("parentTask") or {}).get("id") or "")
                        if parent_id and parent_id in integrations_parents:
                            integrations_parents[parent_id]["subtasks"].append({
                                "id":       str(t.get("id") or t.get("taskId") or ""),
                                "name":     t.get("name") or t.get("taskName") or "(unnamed)",
                                "rlStatus": t.get("status") or t.get("statusLabel") or "Not Started",
                            })

                    # Build br_map entry
                    br_map[str(pid)] = {
                        bank_task["name"]: {
                            "rlTaskId":  tid,
                            "taskStart": bank_task["start"] or None,
                            "items":     bank_task["subtasks"],
                        }
                        for tid, bank_task in integrations_parents.items()
                    }

                except Exception as e:
                    logging.warning(f"Could not fetch tasks for project {pid}: {e}")
                    br_map[str(pid)] = {}

            return func.HttpResponse(
                json.dumps({"status": {"state": "SUCCEEDED"}, "brMap": br_map}),
                status_code=200,
                mimetype="application/json",
            )

        # ── GET TASK COUNTS (pre-go-live) ────────────────────────────────────
        # Returns total/done pre-go-live task counts for each project.
        elif operation == "getTaskCounts":
            project_ids   = body.get("projectIds", [])
            go_live_dates = body.get("goLiveDates", {})  # { projectId: "YYYY-MM-DD" }
            counts = {}

            for pid in project_ids:
                try:
                    go_live = go_live_dates.get(str(pid))
                    tasks = paginate(
                        "/tasks",
                        {"projectId": pid},
                        api_key,
                    )
                    total = 0
                    done  = 0
                    for t in tasks:
                        parent_id = t.get("parentTaskId") or (t.get("parentTask") or {}).get("id")
                        if parent_id:
                            continue  # skip subtasks
                        due = t.get("dueDate") or t.get("endDate") or ""
                        if go_live and due and due[:10] >= go_live:
                            continue  # only count pre-go-live tasks
                        total += 1
                        st = (t.get("status") or t.get("statusLabel") or "").lower()
                        if st in ("completed", "complete", "done"):
                            done += 1
                    counts[str(pid)] = {"total": total, "done": done}
                except Exception as e:
                    logging.warning(f"Could not fetch task counts for project {pid}: {e}")
                    counts[str(pid)] = {"total": 0, "done": 0}

            return func.HttpResponse(
                json.dumps({"status": {"state": "SUCCEEDED"}, "counts": counts}),
                status_code=200,
                mimetype="application/json",
            )

        # ── CREATE TASK (Integrations phase) ────────────────────────────────────
        # Creates a new task under the Integrations phase of a given project.
        elif operation == "createTask":
            project_id = str(body.get("projectId", "")).strip()
            task_name  = str(body.get("taskName",  "")).strip()
            task_start = body.get("taskStart")   # YYYY-MM-DD or None

            if not project_id or not task_name:
                return func.HttpResponse(
                    json.dumps({"error": "Missing projectId or taskName"}),
                    status_code=400,
                    mimetype="application/json",
                )

            # Resolve Integrations phase ID
            integrations_phase_id = None
            try:
                proj_data = rl_get(f"/projects/{project_id}", {"includeFields": "phases"}, api_key)
                phases = (
                    proj_data.get("phases")
                    or proj_data.get("data", {}).get("phases")
                    or []
                )
                for ph in phases:
                    ph_name = (ph.get("name") or "").lower()
                    if "integrations" in ph_name:
                        integrations_phase_id = ph.get("id") or ph.get("phaseId")
                        break
            except Exception as e:
                logging.warning(f"Could not fetch phases for project {project_id}: {e}")

            rl_headers = {
                "api-key": api_key,
                "Accept": "application/json",
                "Content-Type": "application/json",
            }
            task_payload: dict = {
                "projectId": int(project_id),
                "name":      task_name,
            }
            if integrations_phase_id:
                task_payload["phaseId"] = integrations_phase_id
            if task_start:
                task_payload["startDate"] = task_start

            resp = requests.post(
                f"{RL_BASE}/tasks",
                json=task_payload,
                headers=rl_headers,
                timeout=30,
            )
            resp.raise_for_status()
            data    = resp.json()
            task_id = str(
                data.get("id")
                or (data.get("data") or {}).get("id")
                or ""
            )
            return func.HttpResponse(
                json.dumps({"status": {"state": "SUCCEEDED"}, "taskId": task_id, "name": task_name}),
                status_code=201,
                mimetype="application/json",
            )

        else:
            return func.HttpResponse(
                json.dumps({"error": f"Unknown operation: {operation}"}),
                status_code=400,
                mimetype="application/json",
            )

    except requests.exceptions.RequestException as e:
        logging.error(f"Rocketlane API error: {e}", exc_info=True)
        return func.HttpResponse(
            json.dumps({"error": "Upstream API error"}),
            status_code=502,
            mimetype="application/json",
        )
    except Exception as e:
        logging.error(f"Error in Rocketlane function: {e}", exc_info=True)
        return func.HttpResponse(
            json.dumps({"error": "Internal server error"}),
            status_code=500,
            mimetype="application/json",
        )
