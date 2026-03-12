# Git Migration Report: Main & Labs Workflow

## Summary
The local git repository and GitHub `origin` were migrated to follow the strict `WORKFLOW_GIT_MAIN_LABS.md` rules.
- Set `main` as the default branch on standard GitHub settings.
- Enforced strict branch protection rules on `main` via GitHub API:
  - Mandated pull requests and prevented direct force-pushes or deletions.
  - Enforced required status checks for CI (`browser-p0-gate` and `lint-test-smoke`).
  - Required conversation resolution before merging.
- Created an orphan `labs` branch with a single initialized `README.md`.
- Attached the `labs` branch to a local Git Worktree at `../backend_Kaucja-labs`.
- Handled remote/active product (`feature/*`) branches gracefully by migrating from `codex/*` structure.
- Migrated active local experimental branches to `exp/*`.
- Verified the integrity of `main` directly using `ruff` and `pytest`.

## Files changed
- Locally created `backend_Kaucja-labs/README.md` via `git checkout --orphan labs` and pushed as the seed for `labs` branch.
- No product code was changed.

## Branch mapping
| Old Branch Name | New Branch Name | Status |
| --- | --- | --- |
| `codex/iteration-31-techspec-lock-and-txt-pdf` | `feature/iteration-31-techspec-lock-and-txt-pdf` | Renamed (Local + Remote) |
| `codex/iteration-28-go-live-hardening` | `feature/iteration-28-go-live-hardening` | Renamed (Local + Remote) |
| `codex/antigravity-quote-browser-tests` | `exp/antigravity-quote-browser-tests` | Renamed (Local Only) |
| `codex/operability-browser-audit` | `exp/operability-browser-audit` | Renamed (Local Only) |
| `master` | `master` | Preserved (Archive) |
| `codex/*` (Others) | `codex/*` | Untouched (Historical/Merged) |

## Commands run + key outputs
**1. Repository Policy Implementation**
```bash
gh repo edit --default-branch main
gh api -X PUT repos/sergeionlyart/backend_Kaucja/branches/main/protection --input protection.json
```
*Applied JSON rules snippet:*
```json
{
  "required_status_checks": {
    "strict": true,
    "contexts": ["browser-p0-gate", "lint-test-smoke"]
  },
  "enforce_admins": true,
  "required_pull_request_reviews": {
    "dismiss_stale_reviews": true,
    "require_code_owner_reviews": false,
    "required_approving_review_count": 0
  },
  "required_conversation_resolution": true,
  "allow_force_pushes": false,
  "allow_deletions": false
}
```
*Note: The rule "PR must pass tests/linters" is now technically enforced at the repository level.*

**2. Labs Orphan & Worktree Creation**
```bash
git checkout --orphan labs
git rm -rf .
echo "# Labs" > README.md
git commit -m "Init labs branch"
git push -u origin labs
git checkout main
cd .. && git worktree add ./backend_Kaucja-labs labs
```
*Output excerpt:*
```text
Preparing worktree (checking out 'labs')
HEAD is now at 4c32d95 Init labs branch
```

**3. Branch Migration Example**
```bash
git branch -m codex/iteration-31-techspec-lock-and-txt-pdf feature/iteration-31-techspec-lock-and-txt-pdf
git push origin feature/iteration-31-techspec-lock-and-txt-pdf
git push origin --delete codex/iteration-31-techspec-lock-and-txt-pdf
git branch -u origin/feature/iteration-31-techspec-lock-and-txt-pdf feature/iteration-31-techspec-lock-and-txt-pdf
```

## Checks
**1. `ruff check .`**
```text
All checks passed!
```
**2. `pytest -q`**
```text
........................................................................ [ 49%]
........................................................................ [ 98%]
..                                                                       [100%]
146 passed in 9.19s
```

## Risks / follow-ups
- **Risk:** Developers may need to manually update tracking branches on their local machines by running `git fetch --all --prune` and resetting Upstreams.
- **Risk:** Previous open Pull Requests hooked to the old `codex/*` branches may need source-branch reconfiguration due to remote branch deletion.
- **Follow-up:** Check GitHub Actions or CI configs that statically referenced `codex/*` branches and ensure they track `feature/*` or `main`.

## Rollback plan
**1. Revert Default Branch & Protection**
```bash
gh repo edit --default-branch codex/iteration-28-go-live-hardening
gh api -X PUT repos/sergeionlyart/backend_Kaucja/branches/main/protection --input - <<< '{"required_status_checks":null,"enforce_admins":false,"required_pull_request_reviews":null,"restrictions":null}'
```

**2. Tear down the Worktree and Delete `labs` Branch**
```bash
git worktree remove ../backend_Kaucja-labs
git push origin --delete labs
git branch -D labs
```

**3. Revert Renamed Branches**
```bash
# Iteration 31
git push origin --delete feature/iteration-31-techspec-lock-and-txt-pdf
git branch -m feature/iteration-31-techspec-lock-and-txt-pdf codex/iteration-31-techspec-lock-and-txt-pdf
git push origin codex/iteration-31-techspec-lock-and-txt-pdf
git branch -u origin/codex/iteration-31-techspec-lock-and-txt-pdf codex/iteration-31-techspec-lock-and-txt-pdf

# Iteration 28
git push origin --delete feature/iteration-28-go-live-hardening
git branch -m feature/iteration-28-go-live-hardening codex/iteration-28-go-live-hardening
git push origin codex/iteration-28-go-live-hardening
git branch -u origin/codex/iteration-28-go-live-hardening codex/iteration-28-go-live-hardening

# Experimental / Validations
git branch -m exp/antigravity-quote-browser-tests codex/antigravity-quote-browser-tests
git branch -m exp/operability-browser-audit codex/operability-browser-audit
```
