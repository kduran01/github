---
name: integration-status-dashboard
description: Build and iterate on the Vantaca Integration Status Dashboard — a standalone React app that replaces the current Excel-based integration tracking spreadsheet. Use this skill whenever the user mentions "integration dashboard," "INT status dashboard," "integration tracker," "Ashley's dashboard," "integration sprint," status colors for integrations, milestone logic for bank readiness, banking sub-checklists, or any work related to the AI Sprint #1 dashboard project. Also trigger when the user asks about integration go-live readiness views, Jira integration tracking, or building React dashboards sourced from Databricks and Jira. This skill contains the full business logic, UI spec, data model, and sprint plan needed to build and maintain the dashboard.
---

# Integration Status Dashboard — Build Skill

## Project Overview

**What:** A standalone React dashboard replacing the Excel-based "Integrations Tickets" spreadsheet as the primary tool for tracking integration readiness across all Vantaca implementation go-lives.

**Why:** The spreadsheet has grown to 25+ monthly tabs with inconsistent formats. The Oct 2025+ format stabilized into a clean checklist structure. The dashboard standardizes on that format, adds automated status color logic, and reduces INT/PM status meetings from 2x/week to 1x/week.

**Build Environment:** Cowork (Anthropic's desktop automation tool). The dashboard will be scaffolded and iterated on within Cowork, which provides file system access, subagent capabilities, and the ability to create and manage project files directly. Ashley will use Cowork to build the React app, connect to data sources, and iterate on the dashboard with Claude's assistance.

**Who:**
- **Project Lead:** Ashley Byrd (Integrations Manager)
- **Sponsor / Co-owner:** Kevin (PM Manager)
- **INT Team:** Peter, Nancy, and Ashley's integration specialists
- **PM Team:** Bill Goodwin, Cameron Williams, Kalika Shelar, Victor Majano, Alex Elliott, Janelle James + 1 additional PM

**Sprint Window:** May 12–26, 2026 | Mid-Sprint Check-in: May 19 | Final Demo: May 26

---

## Data Sources

### Rocketlane (via Databricks)
Rocketlane data lives in `is_prod.rocketlane`. Key tables:

| Table | Purpose |
|-------|---------|
| `project` | Client projects — `name`, `customer_company_name`, `due_date` (go-live), `status_label`, `start_date` |
| `task` | Project tasks — `name`, `status_label`, `due_date`, `phase_name`, `project_id`, `at_risk` |
| `task_assignee_member` | Who owns each task |
| `project_field` | Custom fields including **Go Live Date**, **CompanyID** |
| `field` | Field definitions — `label`, `type`, `enabled` |
| `phase` | Project phases |
| `project_team_member` | PM assignments |
| `users` | User lookup |

**Key custom fields in Rocketlane:** Go Live Date, CompanyID, Deliverables Status, Data Status, Customer Sentiment, Confidence Level.

### Jira (via Jira MCP Connector)
Jira is **not** available in Databricks. Use the Jira MCP connector (Atlassian MCP at `https://mcp.atlassian.com/v1/sse`) for:
- INT ticket status, comments, assignees
- Ticket creation dates and last-updated timestamps
- Links and attachments (e.g., API forms on Zendesk)

Jira project: **INT board** — tickets follow naming convention: `ClientCode – GoLiveDate – BankName` (e.g., `AMS - 10/1 - Alliance Bank`)

### Dashboard Scope
Rolling 2-month window: **current month go-lives + next month go-lives**. Past months archive automatically.

---

## Integration Lifecycle Milestones (Standard — Oct 2025+ Format)

The dashboard tracks a **10-step lifecycle** for every integration. Steps 1–4 are PM-owned; steps 5–9 are INT-owned; step 10 is shared.

| # | Milestone | Owner | Expected Timeline (relative to go-live) |
|---|-----------|-------|----------------------------------------|
| 1 | JIRA Created & Accurate | PM | Within 5 business days of integration identified in discovery; all TBDs resolved by Week 2 |
| 2 | Client Permission Email Sent | PM | Within 5 business days of JIRA creation (at Kickoff stage) |
| 3 | Transition Meeting Held | PM | By 45 days before go-live (PRO Week 2 / ENT Week 2) |
| 4 | Readiness Validation Complete | PM | By 30 days before go-live (PRO Week 4 / ENT Week 8) — this is the **Bank Readiness Key Deliverable** |
| 5 | Credentials Received | INT | By 15 days before go-live |
| 6 | Testing Complete | INT | By 7 days before go-live |
| 7 | Settings > Interfaces Audited | INT/PM | By 5 days before go-live (week before) |
| 8 | Ready for Go-Live | INT | By 3 days before go-live |
| 9 | Post Go-Live Testing Completed | INT | 1–4+ days after go-live |
| 10 | API Form (Zendesk) | PM/INT | Attachment on Jira within 14 days of implementation start |

**Enterprise timing adjustment:** ENT clients start Phase 1 in Week 1, Phase 2 in Week 2, with Bank Readiness Complete by Week 8 (vs Week 4 for PRO).

---

## Status Color Logic

For the full status trigger rules and color definitions, read: `references/status-color-logic.md`

**Summary of the color model:**

| Color | Meaning | Meeting Action |
|-------|---------|----------------|
| 🟩 Green | All milestones on track or complete | Skip during meeting |
| 🟧 Orange/Yellow | Outstanding item < 10 days from due | PM prepares quick update |
| 🟥 Red | Milestone past due | PM + Manager discuss and escalate |
| ⬜ White/Blank | Future task, not yet due | Track for upcoming milestone |

**Stale Jira rule:** No status change or comment in 7+ business days while in active phase → auto-flag Yellow.

**Manager updates colors** based on pre-meeting review. PMs do not self-assign colors.

---

## Banking Sub-Checklist

Each bank integration gets a sub-checklist in addition to the 10-step lifecycle. Items vary by bank type. For the full matrix, read: `references/banking-sub-checklist.md`

**Standard banking items (up to 15):**

| Item | Pre/Post | Required For |
|------|----------|-------------|
| ACH IDs requested/imported | Pre | All integrated banks |
| Transactions pulling | Pre | All SFTP/API banks |
| Balances pulling | Pre/Post | All (some banks post-only) |
| Validation file sent | Pre | All with operating accounts |
| SSO to bank portal | Pre | Banks with portal access |
| Lockbox & images | Post | All with lockbox service |
| Delete prior month interest | Post | All |
| Delete prior month transactions | Post | All |
| ACH files success | Post | All with ACH |
| Positive Pay | Post | Banks that support it |
| Statements | Post | All |
| Returns | Post | All |
| Stop checks | Post | All |
| New bank account requests | Post | PPB & AAB only |

**Bank type categories:**
- **Global Credential Banks** (Alliance/AAB, FCB): Can be set up early in the month; credentials are shared across clients
- **Non-Global / SFTP Banks** (BankUnited, Enterprise, Popular, etc.): Require client-specific credentials; setup begins mid-month
- **API Banks** (varies): Wait for signed API form before creating credentials
- **Non-Integrated Banks**: Tracked separately — dashboard shows count per client + percentage of portfolio on non-integrated banks

**Easiest banks** (per Ashley): Western Alliance (AAB), First Citizens Bank (FCB), SunWest — proactive and responsive.
**Most problematic integrations:** ClickPay, Avid, and some smaller banks.

---

## Dashboard UI Requirements

For the full wireframe spec, read: `references/dashboard-ui-spec.md`

### Summary View (Main Page)
- Client list with columns: Client Name, Client Code, Plan Type (PRO/ENT), Go-Live Date, PM Assigned, INT Assigned, Integration Count, Overall Status Color
- Sortable by any column; filterable by PM, INT member, status color, go-live month
- At-risk count badge at top
- Upcoming go-lives countdown section
- Toggle between Current Month and Next Month views

### Client Detail View
- 10-step milestone checklist with completion dates and TRUE/FALSE status
- Per-bank banking sub-checklist (expandable per bank)
- Jira links (clickable, opening in new tab)
- Risk/Blocker notes + Next Steps field
- Status color per integration and overall client status
- Non-integrated bank section: bank name, association count, account type (Operating/Other), % of portfolio

### Post-Go-Live Section
- QA status per integration
- Lockbox confirmation status
- Transaction monitoring status (are transactions coming in? Are lockboxes working?)
- Separate tab or collapsible section below main checklist
- Ties to Post GoLive Escalations tracking (currently a separate spreadsheet tab)

---

## Sprint Plan & Task Assignments

For the full task breakdown with owners and due dates, read: `references/sprint-tasks.md`

### Workstream Summary

**WS1: Milestone & Status Logic Definition (May 14–16)**
- Finalize 10-step lifecycle milestones — Ashley + Kevin
- Define expected timelines per milestone — Ashley + Kevin
- Define status trigger rules (Yellow/Red thresholds) — Ashley + Kevin
- Define banking sub-checklist per bank type — Ashley
- Document non-integrated bank tracking — Kevin

**WS2: Dashboard Design & Build in Cowork (May 15–21)**
- Wireframe layout — Ashley + Supports
- React app shell + Databricks API connection (built in Cowork) — Ashley + Supports
- Summary View build — Ashley + Supports (May 19)
- Client Detail View build — Ashley + Supports (May 20)
- Post-Go-Live section — Ashley + Supports (May 21)
- Status color logic + visual indicators — Ashley + Supports (May 21)

**WS3: Testing, Validation & Rollout (May 22–26)**
- Full validation against current spreadsheet — Ashley + Kevin (May 22)
- 1-page user guide — Ashley (May 23)
- Demo to full INT + PM team — Ashley + Kevin (May 26)
- Decision: retire spreadsheet or run parallel for 1 month — Ashley + Kevin (May 26)
- Reduce status meetings to 1x/week — Ashley + Kevin (May 26)

### V2 Parking Lot (Out of Sprint Scope)
- Teams alert system (automated overdue milestone alerts)
- Gong integration (auto-extract status from call transcripts)
- Account number validation (pre-go-live check)
- Automated Jira creation from Rocketlane
- Guru card linking per integration type
- Late integration request alerts (< 30 days to go-live)
- Integration QA Agent tie-in
- Go-live date shift detection + milestone recalculation
- Historical analytics (avg time-to-completion per milestone/bank)
- Teams chat monitoring
- Zendesk API form tracking

### Open Questions (Resolve This Sprint)
1. Banking sub-checklist scope: Use newer simplified format or older 9–11 item format? → **Ashley to confirm**
2. Post-go-live escalation tracking: Fold into dashboard or keep separate? → **TBD**
3. Non-integrated banks: Include in V1 or defer? → **TBD**

---

## Guru Card References

These three Guru cards define the current PM/INT bank readiness process. The dashboard must align with these processes:

1. **Bank Readiness Tracker & INT Status Meeting Cadence** (`ibgEd6XT`)
   - Defines the bi-weekly meeting structure (Track 1: Current Month, Track 2: Next Month)
   - Rapid-fire cadence begins 10 days before 30-day milestone
   - Color status legend (Green/Orange/Red/White)
   - PM update cadence: Every Monday & Wednesday by EOD

2. **Phase 1: Client Transition Email & Transition Meeting** (`iMqybBxT`)
   - PM provides client-bank credential permissions email template at kickoff
   - 48-hour follow-up rule if client hasn't sent email
   - PM schedules Bank–Client–Vantaca Transition Meeting within 2 business days of bank response
   - ENT clients: Step 1 in Week 1, Step 2 in Week 2

3. **Phase 2: JIRA & PM Bank Readiness Rocketlane Task** (`TLrRnbzc`)
   - JIRA ticket creation by Week 1 per bank; all TBDs resolved by Week 2
   - Naming convention: `CompanyCode – GoLiveDate – BankName`
   - Bank Readiness Complete = 30-day milestone (PRO Week 4 / ENT Week 8)
   - Final 14-day guardrail: JIRA asks acknowledged same day, resolved in 2–3 business days
   - Final week verification: all tools cross-checked, blockers escalated immediately

---

## How to Use This Skill

This skill is designed for use in **Cowork**. When building or iterating on the dashboard:

1. **For data queries:** Use Databricks (`is_prod.rocketlane.*`) for Rocketlane data and the Jira MCP connector (Atlassian MCP at `https://mcp.atlassian.com/v1/sse`) for ticket data. Jira is NOT in Databricks.
2. **For milestone logic:** Reference the 10-step lifecycle and status color rules in this file and `references/status-color-logic.md`.
3. **For banking details:** Reference `references/banking-sub-checklist.md` for which items apply to which bank types.
4. **For UI decisions:** Reference `references/dashboard-ui-spec.md` for layout, components, and interaction patterns.
5. **For sprint tracking:** Reference `references/sprint-tasks.md` for who owns what and when it's due.
6. **For process alignment:** Fetch the three Guru cards listed above (using the Guru MCP connector at `https://mcp.api.getguru.com/mcp`) to verify the dashboard matches current PM/INT workflows.

### Cowork Build Notes
- Use Cowork's file system to scaffold the React project, write components, and manage build files
- Cowork can run subagents for parallel tasks (e.g., building multiple views simultaneously)
- For data layer: Cowork can create API service files that call Databricks REST API and Jira MCP endpoints
- For testing: Build locally and iterate — Cowork can create, modify, and run files directly
- Output the dashboard as a standalone React app that can be deployed to an internal URL or run locally

When answering questions about the project, always ground responses in the actual spreadsheet format (Oct 2025+ / May–Aug 2026 tabs are the standard) and the Guru-defined processes.
