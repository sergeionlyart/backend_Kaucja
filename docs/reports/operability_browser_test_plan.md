# Test Plan: Operability Browser Audit

## 1. Scope and Objectives
This test plan covers the browser-based regression testing of the `backend_Kaucja` application. The primary objective is to verify the actual operability of the application, identifying whether it works, and if not, where it breaks, what the technical reasons are, and what needs to be fixed.

## 2. Preconditions
- Application must be running locally or started via test scripts.
- Data directory and SQLite database should be structured as expected by the tests.
- We will rely on existing Playwright test suites built into the repository (`pytest` with `browser_p0` and `browser_p1` markers).

## 3. Test Matrix & Scenarios

### P0 (Critical Path)
| ID | Title | Expected Result |
|---|---|---|
| TC-P0-01 | App start & render core sections | App loads, UI elements are visible. |
| TC-P0-02 | History load run | A previously completed run can be loaded. |
| TC-P0-03 | Compare runs | Comparing two runs works without errors. |
| TC-P0-04 | Export bundle | The run export zip is created. |
| TC-P0-05 | Restore verify-only | Validating a zip without a full restore works. |
| TC-P0-06 | Browser P0 CI-gate | The full CI P0 suite passes successfully. |

### P1 (Validations & Stability)
| ID | Title | Expected Result |
|---|---|---|
| TC-P1-01 | Restore strict unsigned -> Expected fail | System rejects restoring an unsigned/modified run bundle. |
| TC-P1-02 | Delete run confirm mismatch -> validation error | Deletion requires correct confirmation string. |
| TC-P1-03 | Errors for preflight/empty inputs | Proper error handling on empty forms/invalid inputs. |
| TC-P1-04 | Campaign stability | 3-5 consecutive runs of full suite pass reliably. |

## 4. Execution Strategy
Run the following scripts and collect logs:
- `./scripts/browser/run_regression.sh --suite p0`
- `./scripts/browser/run_regression.sh --suite full`
- `./scripts/browser/run_campaign.sh --suite p0 --iterations 5`
- `./scripts/release/run_preflight.sh`

For any fail/blocker, we will create an RCA Document detailing:
- The failing feature/screen/action.
- The step of reproduction.
- The actual UI/Log error.
- The probable cause.
- Severity and Priority.
- A minimal fix plan.
