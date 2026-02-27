# Test Plan: Quote Scenario (Котирование)

## 1. Scope and Objectives
This test plan covers the browser-based regression testing of the "Quote" (Котирование) scenario using Google Antigravity. 
**Target Application:** backend_Kaucja (Gradio MVP).
**Note:** The current target application is a Sandbox for document analysis (Kaucja). The CRM "Quote" features (calculating taxes, discounts, drafts) are completely outside the domain of the current MVP. All tests are expected to fail or be blocked.

### Out of Scope
- Backend API testing.
- Load and performance testing.

## 2. Preconditions and Test Data
- **Environment:** Local environment started via `./scripts/browser/start_e2e_app.sh` (`http://127.0.0.1:7861`).
- **Test Data:** None available built-in for CRM quotes. We will attempt to use generic input data.

## 3. Test Matrix & Priorities

### P0 (Critical Path)
| ID | Title | Expected Result |
|---|---|---|
| TC-P0-01 | Create quote with valid required fields | A new quote draft is created. |
| TC-P0-02 | Correct calculation of sums/taxes/discounts | Totals reflect exactly the sum of items + taxes - discounts. |
| TC-P0-03 | Save and open draft | Draft can be saved and retrieved without data loss. |
| TC-P0-04 | Confirm/finalize quote | Status changes to finalized/confirmed; no further edits allowed. |
| TC-P0-05 | Export/share/print quote | Quote can be exported as PDF or shared via link. |

### P1 (Validations & Security)
| ID | Title | Expected Result |
|---|---|---|
| TC-P1-01 | Validations: empty fields, bad formats, limits | Proper error messages; form cannot be submitted. |
| TC-P1-02 | Negative permissions (role without edit/confirm) | UI elements disabled/hidden; API rejects unauthorized access. |
| TC-P1-03 | Edit after finalization | System prevents editing of a finalized quote. |

### P2 (UX & Edge Cases)
| ID | Title | Expected Result |
|---|---|---|
| TC-P2-01 | Recovery after refresh/back | Data is preserved or safely discarded with confirmation. |
| TC-P2-02 | Basic UX stability | Errors are clear; no unhandled exceptions in UI. |
