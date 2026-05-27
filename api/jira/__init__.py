"""
Azure Function: /api/jira
Proxies requests to the Jira Cloud REST API.
Accepts POST with JSON body:
  { "endpoint": "/rest/api/3/...", "method": "GET"|"POST", "body": {...} }
Returns the raw Jira API response.
"""

import json
import logging
import os
from base64 import b64encode

import azure.functions as func
import requests  # type: ignore

logger = logging.getLogger(__name__)

JIRA_BASE_URL = "https://vantaca.atlassian.net"


def main(req: func.HttpRequest) -> func.HttpResponse:
    """Handle POST /api/jira — forward a request to the Jira Cloud API."""

    if req.method == "OPTIONS":
        return func.HttpResponse(
            status_code=200,
            headers={
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "POST, OPTIONS",
                "Access-Control-Allow-Headers": "Content-Type",
            },
        )

    try:
        body = req.get_json()
    except ValueError:
        return _error("Request body must be valid JSON", 400)

    endpoint   = (body or {}).get("endpoint", "").strip()
    method     = (body or {}).get("method", "GET").upper()
    req_body   = (body or {}).get("body")

    if not endpoint:
        return _error("Missing required field: endpoint", 400)

    jira_email = os.environ.get("JIRA_EMAIL")
    jira_token = os.environ.get("JIRA_API_TOKEN")

    if not all([jira_email, jira_token]):
        return _error("Jira credentials not configured", 500)

    credentials = b64encode(f"{jira_email}:{jira_token}".encode()).decode()
    headers = {
        "Authorization": f"Basic {credentials}",
        "Accept": "application/json",
        "Content-Type": "application/json",
    }

    url = f"{JIRA_BASE_URL}{endpoint}"

    try:
        if method == "GET":
            resp = requests.get(url, headers=headers, timeout=15)
        elif method == "POST":
            resp = requests.post(url, headers=headers, json=req_body, timeout=15)
        else:
            return _error(f"Unsupported method: {method}", 400)

        return func.HttpResponse(
            body=resp.text,
            status_code=resp.status_code,
            mimetype="application/json",
            headers={"Access-Control-Allow-Origin": "*"},
        )

    except requests.exceptions.Timeout:
        return _error("Jira API request timed out", 504)
    except Exception as exc:
        logger.exception("Jira API request failed")
        return _error(f"Request failed: {exc}", 500)


def _error(msg: str, status: int) -> func.HttpResponse:
    return func.HttpResponse(
        body=json.dumps({"error": msg}),
        status_code=status,
        mimetype="application/json",
        headers={"Access-Control-Allow-Origin": "*"},
    )
