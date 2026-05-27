# Dashboard UI Specification

## Architecture

**Type:** Standalone React application
**Build Environment:** Cowork
**Data Layer:** REST API calls to Databricks (Rocketlane) + Jira MCP connector (Atlassian)
**Scope:** Rolling 2-month window (current + next month go-lives)
**Users:** Integration team (Ashley, Peter, Nancy), PM team (7 PMs), PM Manager (Kevin)

---

## Navigation Structure

```
┌─────────────────────────────────────────────┐
│  Integration Status Dashboard               │
│  [Current Month ▼] [Next Month]  [Post-GL]  │
├─────────────────────────────────────────────┤
│  Summary View (default)                      │
│  └── Click client row → Client Detail View   │
│       └── Post-Go-Live tab/section           │
└─────────────────────────────────────────────┘
```

Two main views + one sub-section:
1. **Summary View** — All clients at a glance (default landing page)
2. **Client Detail View** — Per-client deep dive (click into from Summary)
3. **Post-Go-Live Section** — Within Client Detail, or as a separate tab

---

## Summary View (Main Page)

### Header Bar
- Dashboard title: "Integration Status Dashboard"
- Month toggle: [Current Month] [Next Month] — shows go-live month
- Last refreshed timestamp
- At-risk badge: "X clients at risk" (count of Orange + Red)

### Filters Bar
- Filter by: PM Assigned, INT Assigned, Status Color, Integration Type, Plan Type (PRO/ENT)
- Search: Client name or client code
- Sort: Click any column header

### Client Table

| Column | Description | Sortable |
|--------|-------------|----------|
| Status | Overall status color dot (🟩🟧🟥⬜) | ✅ |
| Client Name | Full client name | ✅ |
| Client Code | Short code (e.g., "TPAM", "allied") | ✅ |
| Plan Type | PRO or ENT | ✅ |
| Go-Live Date | Target go-live date | ✅ (default sort) |
| PM Assigned | Implementation PM name | ✅ |
| INT Assigned | Integration team member | ✅ |
| Integration Count | Total integrations for this client | ✅ |
| Milestones Complete | e.g., "6/10" — count of completed lifecycle steps | ✅ |
| Risk/Blocker | Truncated first line of risk notes (hover for full) | No |

### Row Behavior
- Click any row → navigates to Client Detail View
- Row background color = faint tint of status color
- Hover shows tooltip with risk/blocker summary

### Upcoming Go-Lives Widget (Optional Sidebar or Top Section)
- Countdown cards for clients going live within next 7 days
- Shows: Client name, days until go-live, status color, incomplete milestone count

---

## Client Detail View

### Header
- Back arrow ← to Summary View
- Client name + Client Code
- Plan Type badge (PRO / ENT)
- Go-Live Date (with countdown: "X days away")
- Overall Status Color (large indicator)
- PM Assigned + INT Assigned

### Integration List
Each integration for this client displayed as an expandable card or section:

```
┌─────────────────────────────────────────────┐
│ 🟧 Alliance Bank (Banking)                  │
│ Jira: INT-10943  [Open in Jira ↗]          │
│ INT Assigned: Nancy                          │
├─────────────────────────────────────────────┤
│ 10-Step Lifecycle Checklist                  │
│ ✅ JIRA Created & Accurate      2026-03-12  │
│ ✅ Client Permission Email Sent  2026-03-01  │
│ ✅ Transition Meeting Held       2026-03-10  │
│ ✅ Readiness Validation Complete 2026-03-16  │
│ ✅ Credentials Received          2026-04-15  │
│ ⬜ Testing Complete              —           │
│ ⬜ Settings > Interfaces Audited —           │
│ ⬜ Ready for Go-Live             —           │
│ ⬜ Post Go-Live Testing          —           │
│ ✅ API Form (Zendesk)            2026-03-05  │
├─────────────────────────────────────────────┤
│ ▸ Banking Sub-Checklist (expand)             │
├─────────────────────────────────────────────┤
│ Risk/Blocker: Bank Accounts Pending: 5 accts │
│ Next Steps: Waiting on bank confirmation      │
└─────────────────────────────────────────────┘
```

### 10-Step Lifecycle Checklist
- Each milestone shown with: checkbox (✅/⬜), milestone name, owner tag (PM/INT/INT-PM), completion date or "—"
- Color-code each milestone row based on its individual status (Green/Orange/Red/White)
- Show expected due date alongside actual completion date

### Banking Sub-Checklist (Expandable per Bank)
- Only shown for bank integrations (not API partners)
- Shows all applicable items from the banking matrix
- Each item: Pre/Post tag, status (✅/⬜/N/A), notes
- Items marked N/A should be greyed out, not hidden

### API Partner Checklist (for non-bank integrations)
- Simplified 6-item checklist
- Same visual pattern as banking sub-checklist

### Jira Link
- Clickable link opening Jira ticket in new tab
- Format: `https://vantaca.atlassian.net/browse/INT-XXXXX`

### Risk/Blocker Notes
- Free-text field showing current risk or blocker
- Next steps field
- Editable in future versions (V1 = read-only from data source)

### Non-Integrated Banks Section
Displayed below all integrations for the client:

```
┌─────────────────────────────────────────────┐
│ Non-Integrated Banks                         │
│ 168 total associations (X% of portfolio)     │
├──────────────────┬───────┬──────────────────┤
│ Bank Name        │ Assoc │ Account Type      │
├──────────────────┼───────┼──────────────────┤
│ Cadence Bank     │ 13    │ Operating         │
│ Community Bank   │ 12    │ Operating         │
│ Capital City     │ 53    │ Operating         │
│ ...              │       │                   │
└──────────────────┴───────┴──────────────────┘
```

---

## Post-Go-Live Section

Separate tab or collapsible section within Client Detail View. Tracks post-go-live health for each integration.

### Post-Go-Live Checklist (per integration)
| Item | Status | Notes |
|------|--------|-------|
| Transactions flowing | ✅/⬜ | Checked within 1–4 days |
| Lockbox delivering | ✅/⬜ | Checked within first week |
| ACH files processing | ✅/⬜ | Checked within first week |
| Prior month cleanup done | ✅/⬜ | Interest + transactions deleted |
| Monitoring complete | ✅/⬜ | All post-go-live items verified |

### Post-Go-Live Escalations
- Separate list of escalation tickets
- Columns: Client, Integration, Jira Card, Status (To Do / In Progress / Done), Notes
- Source: Currently tracked in "Post GoLive Escalations" spreadsheet tab
- **Open question:** Fold into dashboard or keep separate? (TBD by Ashley + Kevin)

---

## Visual Design Guidelines

### Status Colors (CSS)
```css
--status-green: #4CAF50;   /* Complete / On Track */
--status-orange: #FF9800;  /* Outstanding, < 10 days from due */
--status-red: #F44336;     /* Past Due */
--status-white: #FFFFFF;   /* Future / Not Yet Due */
--status-green-bg: #E8F5E9;
--status-orange-bg: #FFF3E0;
--status-red-bg: #FFEBEE;
```

### Typography
- Headers: Bold, larger size for client names and section titles
- Body: Clean sans-serif (system font stack or Inter/Roboto)
- Monospace for client codes and Jira ticket numbers

### Layout
- Responsive but optimized for desktop (primary use in status meetings)
- Card-based layout for integration items
- Collapsible sections to manage information density
- Sticky header with filters when scrolling

### Interaction Patterns
- Click row → drill into detail
- Expand/collapse banking sub-checklists
- Hover for risk note tooltips
- External links (Jira) open in new tab
- Month toggle switches data context without page reload

---

## Data Refresh Strategy

### V1 (This Sprint)
- Manual refresh: "Refresh Data" button pulls latest from Databricks + Jira
- Timestamp shows last refresh time
- Acceptable for 1x/week meeting cadence

### V2 (Future)
- Auto-refresh on configurable interval (e.g., every 30 minutes)
- Webhook-based updates from Jira status changes
- Teams alert integration for overdue milestones
