# Integration Status Dashboard

Live dashboard for tracking Vantaca integration status across May-June 2026 go-live clients. Pulls data from Databricks (Rocketlane projects) and Jira (INT tickets).

## Features

- **Live Data**: Refreshes data from Databricks and Jira on demand
- **10-Step Milestone Tracking**: Visual timeline for each client integration
- **Team Assignments**: Shows PM and Integration team member assignments
- **Jira Integration**: Clickable tickets with stale-ticket alerts
- **Sortable & Filterable**: Client table with multiple filter options
- **Color-Coded Status**: Green/Orange/Red status indicators based on project health

## Project Structure

```
Integration Status/
├── index.html                  # Main dashboard UI
├── api/                        # Azure Functions backend
│   ├── databricks/            # Function for Databricks queries
│   │   ├── __init__.py
│   │   └── function.json
│   ├── jira/                  # Function for Jira API calls
│   │   ├── __init__.py
│   │   └── function.json
│   ├── host.json              # Azure Functions host config
│   ├── requirements.txt       # Python dependencies
│   ├── local.settings.json    # Local environment variables (not in git)
│   └── .gitignore
├── staticwebapp.config.json   # Azure Static Web Apps routing config
├── DEPLOYMENT.md              # Detailed deployment instructions
├── dashboard-ui-spec.md       # Original UI specification
├── banking-sub-checklist.md   # Banking checklist reference
├── sprint-tasks.md            # Sprint planning tasks
└── status-color-logic.md      # Status color calculation logic
```

## Quick Start

See [DEPLOYMENT.md](DEPLOYMENT.md) for detailed deployment instructions.

### Local Development

1. Install dependencies:
   ```bash
   cd api
   pip install -r requirements.txt
   ```

2. Configure `api/local.settings.json` with your credentials

3. Run locally:
   ```bash
   npm install -g @azure/static-web-apps-cli
   swa start . --api-location api
   ```

4. Open http://localhost:4280

## Technology Stack

- **Frontend**: Vanilla JavaScript, HTML5, CSS3
- **Backend**: Azure Functions (Python 3.9+)
- **Data Sources**:
  - Databricks SQL (Rocketlane data)
  - Jira Cloud API (Integration tickets)
- **Hosting**: Azure Static Web Apps

## Data Sources

### Databricks (Rocketlane)
- Project details and go-live dates
- Team member assignments
- Task completion status
- Pre-go-live task tracking

### Jira
- INT ticket status and assignments
- Ticket comments and updates
- User information

## Configuration

Environment variables required (set in Azure Portal or local.settings.json):

- `DATABRICKS_SERVER_HOSTNAME`
- `DATABRICKS_HTTP_PATH`
- `DATABRICKS_ACCESS_TOKEN`
- `JIRA_URL`
- `JIRA_EMAIL`
- `JIRA_API_TOKEN`

## Security

- All credentials stored as environment variables
- Jira comments include structured tags for dashboard sync
- Read-only Databricks access
- Function-level authentication on Azure Functions

## Contributing

1. Make changes locally
2. Test with `swa start`
3. Deploy via Azure CLI or push to GitHub (if using GitHub Actions)

## Support

For issues or questions, contact the Integration team or refer to DEPLOYMENT.md troubleshooting section.
