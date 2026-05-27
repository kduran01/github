# Integration Status Dashboard - Deployment Guide

This guide will help you deploy the Integration Status Dashboard to Azure Static Web Apps with Azure Functions backend.

## Prerequisites

1. **Azure Account** with an active subscription
2. **Azure CLI** installed ([Install Guide](https://docs.microsoft.com/en-us/cli/azure/install-azure-cli))
3. **Azure Functions Core Tools** v4.x installed ([Install Guide](https://docs.microsoft.com/en-us/azure/azure-functions/functions-run-local))
4. **Python 3.9 or higher** installed
5. **Git** installed

## Required Credentials

Before deploying, gather these credentials:

### Databricks
- **Server Hostname**: Your Databricks workspace hostname (e.g., `adb-xxxxx.azuredatabricks.net`)
- **HTTP Path**: Your SQL warehouse HTTP path (e.g., `/sql/1.0/warehouses/xxxxx`)
- **Access Token**: Databricks personal access token

### Jira
- **Jira URL**: `https://vantaca.atlassian.net`
- **Jira Email**: Your Atlassian account email
- **API Token**: Jira API token ([Create one here](https://id.atlassian.com/manage-profile/security/api-tokens))

## Deployment Steps

### Option 1: Deploy via Azure Portal (Recommended for first deployment)

#### Step 1: Create Azure Static Web App

1. Go to [Azure Portal](https://portal.azure.com)
2. Click **Create a resource** > Search for **Static Web App**
3. Click **Create**
4. Fill in the details:
   - **Subscription**: Select your subscription
   - **Resource Group**: Create new or select existing
   - **Name**: `integration-status-dashboard` (or your preferred name)
   - **Plan type**: Standard (required for Azure Functions API)
   - **Region**: Select closest to you
   - **Deployment source**: Select **Other** for now
5. Click **Review + Create** > **Create**
6. Wait for deployment to complete

#### Step 2: Configure Environment Variables

1. Once deployed, go to your Static Web App resource
2. In the left menu, click **Configuration**
3. Click **+ Add** and add these application settings:

| Name | Value |
|------|-------|
| `DATABRICKS_SERVER_HOSTNAME` | Your Databricks hostname |
| `DATABRICKS_HTTP_PATH` | Your Databricks HTTP path |
| `DATABRICKS_ACCESS_TOKEN` | Your Databricks token |
| `JIRA_URL` | `https://vantaca.atlassian.net` |
| `JIRA_EMAIL` | Your Jira email |
| `JIRA_API_TOKEN` | Your Jira API token |

4. Click **Save**

#### Step 3: Get Deployment Token

1. In your Static Web App, click **Manage deployment token**
2. Copy the token - you'll need it for deployment

#### Step 4: Deploy Using Azure CLI

Open a terminal and run:

```bash
# Login to Azure
az login

# Install the Static Web Apps CLI
npm install -g @azure/static-web-apps-cli

# Navigate to your project directory
cd "C:\Users\AshleyByrd\OneDrive - Vantaca, LLC\5. Integrations\Integrations Status"

# Deploy using the token (replace YOUR_DEPLOYMENT_TOKEN with the token from Step 3)
swa deploy --deployment-token YOUR_DEPLOYMENT_TOKEN --app-location . --api-location api
```

### Option 2: Deploy via GitHub Actions (Recommended for ongoing updates)

#### Step 1: Create GitHub Repository

1. Create a new repository on GitHub
2. Push your code:

```bash
cd "C:\Users\AshleyByrd\OneDrive - Vantaca, LLC\5. Integrations\Integrations Status"
git init
git add .
git commit -m "Initial commit: Integration Status Dashboard"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/integration-status-dashboard.git
git push -u origin main
```

#### Step 2: Create Azure Static Web App with GitHub

1. Go to [Azure Portal](https://portal.azure.com)
2. Create a Static Web App (same as Option 1, Step 1)
3. For **Deployment source**, select **GitHub**
4. Authorize Azure to access your GitHub account
5. Select your repository and branch
6. Build Presets: Select **Custom**
7. App location: `/`
8. Api location: `api`
9. Output location: leave empty
10. Click **Review + Create** > **Create**

This will automatically create a GitHub Actions workflow that deploys on every push to main.

#### Step 3: Configure Environment Variables

Follow Option 1, Step 2 to add environment variables in Azure Portal.

### Option 3: Local Testing Before Deployment

To test the dashboard locally before deploying:

#### Step 1: Set Up Local Environment

1. Install Python dependencies:

```bash
cd "C:\Users\AshleyByrd\OneDrive - Vantaca, LLC\5. Integrations\Integrations Status\api"
pip install -r requirements.txt
```

2. Update `api/local.settings.json` with your credentials:

```json
{
  "IsEncrypted": false,
  "Values": {
    "AzureWebJobsStorage": "",
    "FUNCTIONS_WORKER_RUNTIME": "python",
    "DATABRICKS_SERVER_HOSTNAME": "your-databricks-hostname",
    "DATABRICKS_HTTP_PATH": "/sql/1.0/warehouses/your-warehouse-id",
    "DATABRICKS_ACCESS_TOKEN": "your-databricks-token",
    "JIRA_URL": "https://vantaca.atlassian.net",
    "JIRA_EMAIL": "your-email@vantaca.com",
    "JIRA_API_TOKEN": "your-jira-api-token"
  },
  "Host": {
    "CORS": "*"
  }
}
```

#### Step 2: Run Locally

```bash
# From the project root directory
cd "C:\Users\AshleyByrd\OneDrive - Vantaca, LLC\5. Integrations\Integrations Status"

# Start Azure Functions and serve static content
swa start . --api-location api
```

3. Open browser to `http://localhost:4280`

## Updating the Dashboard

### If using Azure Portal deployment:

```bash
cd "C:\Users\AshleyByrd\OneDrive - Vantaca, LLC\5. Integrations\Integrations Status"
swa deploy --deployment-token YOUR_DEPLOYMENT_TOKEN --app-location . --api-location api
```

### If using GitHub Actions:

Simply push your changes:

```bash
git add .
git commit -m "Update dashboard"
git push
```

The GitHub Action will automatically deploy your changes.

## Troubleshooting

### Dashboard shows "API call timed out" error

- Check that environment variables are correctly set in Azure Portal
- Verify Databricks token hasn't expired
- Check Azure Functions logs in Azure Portal > Your Static Web App > Functions > Monitor

### Jira data not loading

- Verify JIRA_EMAIL and JIRA_API_TOKEN are correct
- Test Jira API token: https://id.atlassian.com/manage-profile/security/api-tokens
- Check Azure Functions logs for detailed error messages

### Functions not found (404 errors on /api/*)

- Ensure `api-location` is set to `api` in deployment
- Verify `staticwebapp.config.json` is in the root directory
- Check that Python dependencies are installed (requirements.txt)

### Databricks connection errors

- Verify your Databricks workspace is accessible
- Check that the access token has the required permissions
- Ensure SQL warehouse is running

## Security Notes

1. **Never commit `local.settings.json`** to version control (it's in .gitignore)
2. **Rotate credentials regularly** - Update tokens in Azure Portal Configuration
3. **Use separate tokens** for production vs development/testing
4. **Monitor function executions** in Azure Portal for suspicious activity

## Cost Considerations

- **Azure Static Web Apps Standard**: ~$9/month (required for API support)
- **Azure Functions**: Pay-per-execution (typically very low cost for dashboard usage)
- **Databricks**: Based on your existing cluster/warehouse usage

## Support

For issues or questions:
- Check Azure Portal logs: Your Static Web App > Functions > Monitor
- Review Azure Functions documentation: https://docs.microsoft.com/en-us/azure/azure-functions/
- Contact IT team for credential/access issues
