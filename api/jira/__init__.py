import azure.functions as func
import json
import os
import logging
import requests
from requests.auth import HTTPBasicAuth

def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Jira function triggered')

    try:
        # Get request parameters
        req_body = req.get_json()
        operation = req_body.get('operation')

        # Get Jira connection details from environment variables
        jira_url = os.environ.get('JIRA_URL', 'https://vantaca.atlassian.net')
        jira_email = os.environ.get('JIRA_EMAIL')
        jira_api_token = os.environ.get('JIRA_API_TOKEN')

        if not all([jira_email, jira_api_token]):
            return func.HttpResponse(
                json.dumps({"error": "Missing Jira configuration"}),
                status_code=500,
                mimetype="application/json"
            )

        auth = HTTPBasicAuth(jira_email, jira_api_token)
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json"
        }

        # Handle different operations
        if operation == 'searchJiraIssuesUsingJql':
            jql = req_body.get('jql')
            if not jql:
                return func.HttpResponse(
                    json.dumps({"error": "Missing 'jql' parameter"}),
                    status_code=400,
                    mimetype="application/json"
                )

            # Search Jira issues using JQL
            search_url = f"{jira_url}/rest/api/3/search"
            payload = {
                "jql": jql,
                "maxResults": req_body.get('maxResults', 100),
                "fields": req_body.get('fields', ['*all'])
            }

            response = requests.post(search_url, json=payload, headers=headers, auth=auth)
            response.raise_for_status()

            return func.HttpResponse(
                json.dumps(response.json()),
                status_code=200,
                mimetype="application/json"
            )

        elif operation == 'getJiraIssue':
            issue_key = req_body.get('issueKey')
            if not issue_key:
                return func.HttpResponse(
                    json.dumps({"error": "Missing 'issueKey' parameter"}),
                    status_code=400,
                    mimetype="application/json"
                )

            issue_url = f"{jira_url}/rest/api/3/issue/{issue_key}"
            response = requests.get(issue_url, headers=headers, auth=auth)
            response.raise_for_status()

            return func.HttpResponse(
                json.dumps(response.json()),
                status_code=200,
                mimetype="application/json"
            )

        elif operation == 'addCommentToJiraIssue':
            issue_key = req_body.get('issueKey')
            comment_body = req_body.get('body')

            if not issue_key or not comment_body:
                return func.HttpResponse(
                    json.dumps({"error": "Missing 'issueKey' or 'body' parameter"}),
                    status_code=400,
                    mimetype="application/json"
                )

            comment_url = f"{jira_url}/rest/api/3/issue/{issue_key}/comment"
            payload = {
                "body": {
                    "type": "doc",
                    "version": 1,
                    "content": [
                        {
                            "type": "paragraph",
                            "content": [
                                {
                                    "type": "text",
                                    "text": comment_body
                                }
                            ]
                        }
                    ]
                }
            }

            response = requests.post(comment_url, json=payload, headers=headers, auth=auth)
            response.raise_for_status()

            return func.HttpResponse(
                json.dumps(response.json()),
                status_code=201,
                mimetype="application/json"
            )

        elif operation == 'atlassianUserInfo':
            # Get current user info
            myself_url = f"{jira_url}/rest/api/3/myself"
            response = requests.get(myself_url, headers=headers, auth=auth)
            response.raise_for_status()

            return func.HttpResponse(
                json.dumps(response.json()),
                status_code=200,
                mimetype="application/json"
            )

        else:
            return func.HttpResponse(
                json.dumps({"error": f"Unknown operation: {operation}"}),
                status_code=400,
                mimetype="application/json"
            )

    except requests.exceptions.RequestException as e:
        logging.error(f"Jira API error: {str(e)}")
        return func.HttpResponse(
            json.dumps({"error": f"Jira API error: {str(e)}"}),
            status_code=500,
            mimetype="application/json"
        )
    except Exception as e:
        logging.error(f"Error in Jira function: {str(e)}")
        return func.HttpResponse(
            json.dumps({"error": str(e)}),
            status_code=500,
            mimetype="application/json"
        )
