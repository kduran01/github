import azure.functions as func
import json
import os
import re
import logging
import requests
from requests.auth import HTTPBasicAuth

_ISSUE_KEY_RE = re.compile(r'^[A-Z][A-Z0-9]+-\d+$')
_ALLOWED_OPERATIONS = {'searchJiraIssuesUsingJql', 'getJiraIssue', 'addCommentToJiraIssue', 'atlassianUserInfo'}
_JQL_REQUIRED_SCOPE = 'project = "INT"'


def _validate_issue_key(key: str) -> bool:
    return bool(key and _ISSUE_KEY_RE.match(key))


def _enforce_jql_scope(jql: str) -> str:
    """Ensure JQL is scoped to the INT project only."""
    if not jql:
        raise ValueError("Missing jql")
    normalized = jql.strip()
    if 'project = "INT"' not in normalized and "project = 'INT'" not in normalized:
        raise ValueError("JQL must be scoped to project = \"INT\"")
    return normalized


def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Jira function triggered')

    try:
        req_body  = req.get_json()
        operation = req_body.get('operation')

        if operation not in _ALLOWED_OPERATIONS:
            return func.HttpResponse(
                json.dumps({"error": "Unknown or disallowed operation"}),
                status_code=400,
                mimetype="application/json"
            )

        jira_url      = os.environ.get('JIRA_URL', 'https://vantaca.atlassian.net')
        jira_email    = os.environ.get('JIRA_EMAIL')
        jira_api_token = os.environ.get('JIRA_API_TOKEN')

        if not all([jira_email, jira_api_token]):
            logging.error("Missing Jira configuration env vars")
            return func.HttpResponse(
                json.dumps({"error": "Server configuration error"}),
                status_code=500,
                mimetype="application/json"
            )

        auth = HTTPBasicAuth(jira_email, jira_api_token)
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json"
        }

        if operation == 'searchJiraIssuesUsingJql':
            try:
                jql = _enforce_jql_scope(req_body.get('jql', ''))
            except ValueError as e:
                return func.HttpResponse(
                    json.dumps({"error": str(e)}),
                    status_code=400,
                    mimetype="application/json"
                )

            payload = {
                "jql":        jql,
                "maxResults": min(int(req_body.get('maxResults', 100)), 200),
                "fields":     req_body.get('fields', ['*all'])
            }
            response = requests.post(
                f"{jira_url}/rest/api/3/search",
                json=payload, headers=headers, auth=auth, timeout=30
            )
            response.raise_for_status()
            return func.HttpResponse(
                json.dumps(response.json()), status_code=200, mimetype="application/json"
            )

        elif operation == 'getJiraIssue':
            issue_key = req_body.get('issueKey', '')
            if not _validate_issue_key(issue_key):
                return func.HttpResponse(
                    json.dumps({"error": "Invalid or missing issueKey"}),
                    status_code=400,
                    mimetype="application/json"
                )
            response = requests.get(
                f"{jira_url}/rest/api/3/issue/{issue_key}",
                headers=headers, auth=auth, timeout=30
            )
            response.raise_for_status()
            return func.HttpResponse(
                json.dumps(response.json()), status_code=200, mimetype="application/json"
            )

        elif operation == 'addCommentToJiraIssue':
            issue_key    = req_body.get('issueKey', '')
            comment_body = req_body.get('body', '')

            if not _validate_issue_key(issue_key):
                return func.HttpResponse(
                    json.dumps({"error": "Invalid or missing issueKey"}),
                    status_code=400,
                    mimetype="application/json"
                )
            if not comment_body or not isinstance(comment_body, str):
                return func.HttpResponse(
                    json.dumps({"error": "Missing or invalid comment body"}),
                    status_code=400,
                    mimetype="application/json"
                )
            if len(comment_body) > 10000:
                return func.HttpResponse(
                    json.dumps({"error": "Comment body too long"}),
                    status_code=400,
                    mimetype="application/json"
                )

            payload = {
                "body": {
                    "type": "doc", "version": 1,
                    "content": [{"type": "paragraph", "content": [{"type": "text", "text": comment_body}]}]
                }
            }
            response = requests.post(
                f"{jira_url}/rest/api/3/issue/{issue_key}/comment",
                json=payload, headers=headers, auth=auth, timeout=30
            )
            response.raise_for_status()
            return func.HttpResponse(
                json.dumps(response.json()), status_code=201, mimetype="application/json"
            )

        elif operation == 'atlassianUserInfo':
            response = requests.get(
                f"{jira_url}/rest/api/3/myself",
                headers=headers, auth=auth, timeout=30
            )
            response.raise_for_status()
            return func.HttpResponse(
                json.dumps(response.json()), status_code=200, mimetype="application/json"
            )

    except requests.exceptions.RequestException as e:
        logging.error(f"Jira upstream error: {e}", exc_info=True)
        return func.HttpResponse(
            json.dumps({"error": "Upstream API error"}),
            status_code=502,
            mimetype="application/json"
        )
    except Exception as e:
        logging.error(f"Jira function error: {e}", exc_info=True)
        return func.HttpResponse(
            json.dumps({"error": "Internal server error"}),
            status_code=500,
            mimetype="application/json"
        )
