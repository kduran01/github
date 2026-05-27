"""
Azure Function: /api/databricks
Proxies SQL queries to Databricks SQL warehouse using DBSQL connector.
Accepts POST with JSON body: { "sql": "SELECT ..." }
Returns JSON result set.
"""

import json
import logging
import os

import azure.functions as func

logger = logging.getLogger(__name__)


def main(req: func.HttpRequest) -> func.HttpResponse:
    """Handle POST /api/databricks — execute a read-only SQL query."""

    # CORS preflight
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

    sql = (body or {}).get("sql", "").strip()
    if not sql:
        return _error("Missing required field: sql", 400)

    # Safety guard — only allow SELECT statements
    if not sql.upper().lstrip().startswith("SELECT"):
        return _error("Only SELECT statements are permitted", 403)

    server_hostname = os.environ.get("DATABRICKS_SERVER_HOSTNAME")
    http_path       = os.environ.get("DATABRICKS_HTTP_PATH")
    access_token    = os.environ.get("DATABRICKS_ACCESS_TOKEN")

    if not all([server_hostname, http_path, access_token]):
        return _error("Databricks credentials not configured", 500)

    try:
        from databricks import sql as dbsql  # type: ignore

        with dbsql.connect(
            server_hostname=server_hostname,
            http_path=http_path,
            access_token=access_token,
        ) as connection:
            with connection.cursor() as cursor:
                cursor.execute(sql)
                columns = [desc[0] for desc in cursor.description] if cursor.description else []
                rows    = cursor.fetchall()
                result  = [dict(zip(columns, row)) for row in rows]

        return func.HttpResponse(
            body=json.dumps({"columns": columns, "rows": result, "count": len(result)}),
            mimetype="application/json",
            headers={"Access-Control-Allow-Origin": "*"},
        )

    except Exception as exc:
        logger.exception("Databricks query failed")
        return _error(f"Query failed: {exc}", 500)


def _error(msg: str, status: int) -> func.HttpResponse:
    return func.HttpResponse(
        body=json.dumps({"error": msg}),
        status_code=status,
        mimetype="application/json",
        headers={"Access-Control-Allow-Origin": "*"},
    )
