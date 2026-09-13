# Two-minute demo script

## 0:00–0:15 — Problem
“An important email should become verified work, but humans still jump between email, a runbook, and the work tracker — and automation can silently fail halfway.”

## 0:15–0:30 — Input
Show one controlled Gmail message and its immutable message ID.

## 0:30–1:10 — Verified live execution
Show the captured R008 path: agent ACTION decision, Drive runbook, GitHub issue #2, GitHub readback, Drive proof receipt, and receipt readback. State explicitly that the live runtime is the host LLM with authenticated connectors; the repository CLI is the reproducible evaluator.

## 1:10–1:35 — Reliability
Show the replay proof for the same Gmail fingerprint: GitHub search resolves exactly one matching issue and no second issue was created. Then briefly show the local ambiguous fixture routing to REVIEW with zero downstream mutation.

## 1:35–1:55 — Value
“ProofGate handles the decision, action, and verification loop across three apps, so the operator gets evidence of what actually happened instead of a hopeful success message.”

## 1:55–2:00 — Close
“ProofGate does not just call three apps; it completes and verifies one cross-app job.”

## Captured live proof references
- Source fingerprint: `2d17fefe09134133dc65826df2fe6941b780c9509fc13f79fde27274ee7f5377`
- GitHub action: `kiencuongnguyen88/diamond-evidence-gate#2`
- Replay result: `DUPLICATE_REPLAY_NO_NEW_ACTION`
- Sanitized receipt: `evidence/live_r008_verified.json`
