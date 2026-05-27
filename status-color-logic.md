# Status Color Logic — Full Specification

## Overview

The dashboard uses milestone-based logic to determine each client's integration status color. Each milestone has an expected completion window relative to the go-live date. If a milestone falls behind, the client's status escalates.

**Who updates colors:** The Manager (Kevin) applies color coding in pre-meeting review. PMs do NOT self-assign colors.

---

## Color Definitions

| Color | Label | Meaning | Meeting Behavior | Owner |
|-------|-------|---------|-----------------|-------|
| 🟩 Green | Complete | Readiness task complete | Skip during meeting | PM/INT |
| 🟧 Orange | Outstanding | Item < 10 days from due date | PM prepares quick update | PM |
| 🟥 Red | Past Due | Milestone is overdue | PM + Manager highlight and discuss | PM + Manager |
| ⬜ White/Blank | Future | Task not yet due | Track for upcoming milestone | PM |

---

## Milestone-to-Threshold Mapping

These thresholds define when a milestone transitions from Green → Yellow → Red. "Days before go-live" is the expected completion deadline. Overdue = past that deadline without completion.

| Milestone | Expected Complete By | Yellow Trigger | Red Trigger |
|-----------|---------------------|---------------|-------------|
| JIRA Created & Accurate | 5 biz days after discovery | 3+ days overdue | 7+ days overdue |
| Client Permission Email Sent | 5 biz days after JIRA creation | 3+ days overdue | 7+ days overdue |
| Transition Meeting Held | 45 days before go-live | < 40 days to go-live and not held | < 35 days to go-live and not held |
| Readiness Validation Complete | 30 days before go-live | < 25 days to go-live and not complete | < 20 days to go-live and not complete |
| Credentials Received | 15 days before go-live | < 12 days to go-live and not received | < 10 days to go-live and not received |
| Testing Complete | 7 days before go-live | < 5 days to go-live and not complete | < 3 days to go-live and not complete |
| Settings > Interfaces Audited | 5 days before go-live | < 3 days to go-live and not audited | Day before go-live and not audited |
| Ready for Go-Live | 3 days before go-live | < 2 days and not ready | Go-live day and not ready |
| Post Go-Live Testing | 1–4 days after go-live | > 4 days post go-live and not done | > 7 days post go-live and not done |
| API Form (Zendesk) | 14 days after implementation start | 7+ days overdue | 14+ days overdue |

**⚠️ Action needed:** Ashley and Kevin to review these thresholds and adjust based on actual process. These are starting points derived from the transcript, Guru cards, and INT Steps + Timeline tab.

---

## Stale Jira Detection

**Rule:** If a Jira ticket has no status change or comment in **7+ business days** while the integration is in an active phase (i.e., between JIRA Created and Go-Live Ready), it auto-flags as Yellow regardless of milestone timing.

**Implementation:** Query Jira MCP for `updated` timestamp on each ticket. Compare against current date. If delta > 7 business days → flag stale.

---

## Overall Client Status Color

A client's **overall** status color is the worst (most severe) color across all their integrations:
- If ANY integration is Red → Client is Red
- If ANY integration is Orange (and none Red) → Client is Orange
- If ALL integrations are Green → Client is Green
- If no milestones are due yet → Client is White/Blank

---

## Rapid-Fire Cadence Trigger

The rapid-fire meeting cadence begins **10 days before the 30-day Bank Readiness milestone** (so ~40 days before go-live). During this window:
- Only Orange and Red items are discussed in meetings
- PMs give 1-line updates only for outstanding items
- Green items are skipped entirely

---

## Enterprise Timing Adjustments

Enterprise clients follow an extended timeline:
- Early Readiness phase: 90–80 days out (vs 60–40 for PRO)
- Bank Readiness milestone: Week 8 (vs Week 4 for PRO)
- Phase 1 starts Week 1, Phase 2 starts Week 2

The dashboard should recognize ENT vs PRO plan type and adjust milestone deadlines accordingly.

---

## Post-Go-Live Status

After go-live, status colors shift to monitor:
- Are transactions flowing? (checked within 1–4 days)
- Are lockboxes delivering? (checked within first week)
- Any post-go-live escalations? (tracked in separate section)

Post-go-live escalations get their own status tracking and are NOT mixed into the pre-go-live lifecycle checklist.
