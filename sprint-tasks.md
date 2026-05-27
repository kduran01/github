# Sprint Task Breakdown — AI Sprint #1

## Sprint Window
- **Start:** May 12, 2026
- **Mid-Sprint Check-in:** May 19, 2026
- **Final Demo/Review:** May 26, 2026
- **Build Environment:** Cowork

---

## Workstream 1: Milestone & Status Logic Definition

Define the business logic layer that drives status colors on the dashboard.

| Task | Owner | Due Date | Status |
|------|-------|----------|--------|
| Finalize the 10-step integration lifecycle milestones. Confirm this is the standard for all clients going forward (based on Oct 2025+ format). | Ashley + Kevin | May 14 | |
| Define expected timeline for each milestone relative to go-live date (e.g., Readiness Validation = 30 days before go-live). | Ashley + Kevin | May 14 | |
| Define status trigger rules: which milestone + how many days overdue = Yellow or Red. Review the proposed thresholds and adjust. | Ashley + Kevin | May 15 | |
| Define status color logic: what combination of milestone completion and timing = Green / Yellow / Red for each client. | Ashley + Kevin | May 15 | |
| Define the banking sub-checklist: which items are required for which bank types (SFTP vs API vs Global Credential). Not all banks need all 14 items. | Ashley | May 16 | |
| Document non-integrated bank tracking requirements. How should these appear on the dashboard? | Kevin | May 16 | |

---

## Workstream 2: Dashboard Design & Build (in Cowork)

Design and build the standalone React dashboard using Cowork. Two main views: summary and client detail.

| Task | Owner | Due Date | Status |
|------|-------|----------|--------|
| Wireframe dashboard layout: Summary page (all clients, status colors, at-risk count, upcoming go-lives) + Client detail page (per-client checklist, Jira links, notes, banking sub-checklist). | Ashley + Supports | May 15 | |
| Build React app shell: navigation, layout, Databricks API connection. | Ashley + Supports | May 16 | |
| Build Summary View: Client list with integration count, overall status color, go-live date, PM assigned, INT assigned. Sortable/filterable. | Ashley + Supports | May 19 | |
| Build Client Detail View: 10-step checklist with completion dates, banking sub-checklist per bank, Jira links (clickable), risk/blocker notes, status color. | Ashley + Supports | May 20 | |
| Build Post-Go-Live section: QA status, lockbox confirmation, transaction monitoring status. Separate tab or section. | Ashley + Supports | May 21 | |
| Implement status color logic and visual indicators (Green/Yellow/Red per client and per milestone). | Ashley + Supports | May 21 | |

---

## Workstream 3: Testing, Validation & Rollout

Validate the dashboard works, then get the team using it.

| Task | Owner | Due Date | Status |
|------|-------|----------|--------|
| Full validation: Ashley and Kevin compare dashboard output against current spreadsheet for all May and June clients. Log every discrepancy. | Ashley + Kevin | May 22 | |
| Write a 1-page user guide: how to access, how to read it, what the colors mean, and how to interpret the dashboard. | Ashley | May 23 | |
| Demo to full integration + PM team. Walkthrough of dashboard. | Ashley + Kevin | May 26 | |
| Decision: officially retire the spreadsheet or run in parallel for 1 month. | Ashley + Kevin | May 26 | |
| Reduce status meetings from 2x/week to 1x/week starting the week of May 26. | Ashley + Kevin | May 26 | |

---

## Definition of Done

A live, standalone React dashboard that:
- Shows integration status for all clients going live in the current and next month
- Displays milestone completion, status colors, risk/blocker notes, and Jira links for every active integration
- Replaces the current Excel spreadsheet as the primary integration tracking tool
- Enables status meetings to move from 2x/week to 1x/week

---

## Open Questions (Resolve This Sprint)

| Question | Owner | Status |
|----------|-------|--------|
| Banking sub-checklist scope: Use newer simplified format or older 9–11 item format? | Ashley | TBD |
| Post-go-live escalation tracking: Fold into dashboard or keep separate? | Ashley + Kevin | TBD |
| Non-integrated banks: Include in V1 or defer? | Ashley + Kevin | TBD |

---

## V2 Parking Lot (Not in This Sprint)

These items are out of scope for the 2-week sprint. They go on the backlog for future sprints.

1. **Teams Alert System** — Automated alerts to Teams channel when milestones are overdue
2. **Gong Integration** — Auto-extract integration status from project plan calls
3. **Account Number Validation** — Pre-go-live check against bank records
4. **Automated Jira Creation** — Auto-create Jira ticket when integration identified in Rocketlane
5. **Guru Card Linking** — Link Rachel's bank-specific Guru cards per integration type
6. **Late Integration Alerts** — Alert when client adds integration < 30 days from go-live
7. **Integration QA Agent Tie-in** — Connect Ashley and Kendra's QA automation to post-go-live section
8. **Go-Live Date Shift Detection** — Auto-flag integrations when go-live date changes in Rocketlane
9. **Historical Analytics** — Track avg time-to-completion per milestone, per bank, per integration type
10. **Teams Chat Monitoring** — Pull context from integration-specific Teams chats (WAB, CNB, etc.)
11. **Zendesk API Form Tracking** — Auto-check Zendesk for submitted API forms, flag missing ones
