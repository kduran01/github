# Banking Sub-Checklist — Full Specification

## Overview

Each bank integration includes a sub-checklist of items beyond the 10-step lifecycle. Not all items apply to all bank types. This reference defines which items are required for each bank category.

---

## Bank Type Categories

### Global Credential Banks
Banks where Vantaca holds shared/global credentials. Setup can begin early in the month.

**Banks:** Alliance Bank (AAB), First Citizens Bank (FCB)

**Notes:** Easiest to work with. Credentials already available. Can be configured at beginning of go-live month.

### SFTP Banks
Banks using SFTP file transfer. Require client-specific credentials from the bank.

**Banks:** BankUnited, Enterprise Bank, Pacific Premier Bank (PPB), Popular Bank, Valley National Bank (VNB), Wintrust, SunWest, South State Bank, Truist, Pinnacle Bank, City National Bank (CNB), Banc of California

**Notes:** Credentials typically not available until mid-month. Setup begins mid-month as credentials arrive.

### API Partners
Third-party integrations using API connections. Require signed API forms first.

**Partners:** Avid (Strongroom AP), ClickPay (Lockbox/Payments), HomeWise (Closings), CondoCerts (Closings), South Data / Optimal Outsource (Printing), HOA Mailers (Printing), Zego (Payments), BuildingLink (Portal), FrontSteps (Portal), Axela (Collections), Stan AI, Association Ready / ReadyResale, TenantEvaluation, Landing Rock, Vantaca Pay

**Notes:** Wait for signed API form before creating credentials. If created too early, credentials sent before forms are signed.

### Non-Integrated Banks
Banks with NO direct Vantaca integration. Tracked separately for portfolio visibility.

**Dashboard fields:** Bank Name, Number of Associations, Account Type (Operating/Other), Total count, % of portfolio on non-integrated banks.

---

## Sub-Checklist Items — Bank Integration Matrix

| # | Item | Pre/Post | Global Cred | SFTP | API Partner | Notes |
|---|------|----------|------------|------|-------------|-------|
| 1 | ACH IDs requested/imported | Pre | ✅ | ✅ | N/A | Import into system before go-live |
| 2 | Transactions pulling | Pre | ✅ | ✅ | N/A | Verify BAI files in SFTP or API pulling |
| 3 | Balances pulling | Pre/Post | ✅ | ✅ | N/A | Some banks post-only |
| 4 | Validation file sent | Pre | ✅ | ✅ | N/A | Sent via VLB or direct |
| 5 | SSO to bank portal | Pre | ✅ | ✅ | N/A | Mark N/A if no homeowners with logins |
| 6 | Lockbox & images | Post | ✅ | ✅ | N/A | Verify files delivering post go-live |
| 7 | Delete prior month interest | Post | ✅ | ✅ | N/A | Clean up pre-go-live data |
| 8 | Delete prior month transactions | Post | ✅ | ✅ | N/A | Clean up pre-go-live data |
| 9 | ACH files success | Post | ✅ | ✅ | N/A | Verify ACH payments processing |
| 10 | Positive Pay | Post | ✅ | ✅ | N/A | Mark N/A if bank doesn't support |
| 11 | Statements | Post | ✅ | ✅ | N/A | Bank statement delivery |
| 12 | Returns | Post | ✅ | ✅ | N/A | ACH return processing |
| 13 | Stop checks | Post | ✅ | ✅ | N/A | Stop check processing |
| 14 | New bank account requests | Post | AAB & PPB only | PPB only | N/A | Only for AAB and PPB |

### API Partner Checklist (Simplified)

| Item | When |
|------|------|
| API form signed and received | Pre (within 14 days of implementation start) |
| API user credentials created | Pre (15–10 days before go-live) |
| Credentials sent to partner | Pre (15–10 days before go-live) |
| Connection tested / confirmed | Pre (7–5 days before go-live) |
| Interface marked active | Pre (3 days before go-live) |
| Post-go-live API calls verified | Post (1–4 days after go-live) |

---

## API Integration Go-Live Steps (from INT Steps + Timeline tab)

| Step | Timing | Details | Success Check |
|------|--------|---------|---------------|
| Credentials | 15–10 days | Create API user creds and share with partner | Keys Tested |
| Connection setup | 15–10 days | Configure interface in front end | Setup Complete |
| Pre-Go-Live status | 7–5 days | Check unaccepted creds + confirm ACH testing | Share in Status Mtg |
| Go-Live Ready | 3 days | Set interface Active | PM Notified |
| Post-Go-Live | 1–4+ days | Check for API calls; integration complete if calls successful | Monitored |

**INT team note:** "We validate all credentials and API connectivity prior to go-live, but full production data flow can only be confirmed once the system is live."

---

## KPIs to Track (from Banking Integration Template tab)

| KPI | Pre/Post | Description |
|-----|----------|-------------|
| % INT Go-Live Ready Complete | Pre | Goal: 5 days prior to go-live |
| # Issues within First 30/60/90 days | Post | Track post-go-live issue volume |
| Resolution Time to Errors Fixed | Post | Turnaround from identified to fixed |
| % Transactions Success Rate | Post | Post-go-live transaction accuracy |
| Support Ticket Volume 30/60/90 | Post | Track what is truly INT vs not |

---

## Bank-Specific Notes

| Bank | Rating | Notes |
|------|--------|-------|
| Western Alliance (AAB) | ⭐ Best | Global credentials. Proactive. |
| First Citizens Bank (FCB) | ⭐ Best | Global credentials. Reliable. |
| SunWest | ⭐ Excellent | Extremely proactive. "Amazing to work with." |
| ClickPay | ⚠️ Problematic | Causes most problems and confusion. Lockbox + Payments. |
| Avid | ⚠️ Problematic | IP issues, credential delays, recurring post-go-live escalations. |
| Enterprise Bank | Mixed | Some post-go-live escalations observed. |
| Popular Bank | Neutral | Standard SFTP bank. |
| Valley National Bank (VNB) | Neutral | Standard SFTP bank. |
| Wintrust | Mixed | Some issues observed (VantacaPay confusion). |
| City National Bank (CNB) | Mixed | Dependent on Fiserv for some services; can delay. |
| Truist | Neutral | No dedicated bank rep; email to generic inbox. |
