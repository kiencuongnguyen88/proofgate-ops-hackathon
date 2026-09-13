# ProofGate Ops — System + Reliability Brief

## Product
**ProofGate Ops** — an evidence-gated operations agent.

## Problem
Important operational signals arrive in email, but humans still have to interpret the request, consult a runbook, create the work item, and then verify that the external systems actually reflect the intended change. The failure mode is not only missed work; it is false confidence after a partial automation failure.

## Multi-app workflow
1. **Gmail** — reads one source signal and preserves the immutable message ID.
2. **Google Drive** — reads a bounded runbook and stores the final evidence receipt.
3. **GitHub** — creates or reuses one action issue and then reads it back.

## Why an agent is needed
The workflow contains a decision boundary. The system must distinguish ACTION from REVIEW/NO_ACTION, consult policy before acting, prevent duplicate effects, and change its behavior when evidence is ambiguous or a downstream step fails. A fixed one-way script cannot safely make those decisions and verify the resulting state.

## Architecture
```text
Gmail signal
→ normalize + stable fingerprint
→ ACTION | REVIEW | NO_ACTION
→ Drive runbook gate
→ GitHub issue upsert
→ GitHub readback
→ Drive proof receipt
→ Drive readback
→ verified terminal state
```

## Reliability design
- **Identity:** immutable source message ID + SHA-256 fingerprint.
- **Idempotency:** same completed fingerprint replays without creating a second action.
- **Readback:** GitHub and Drive writes are followed by fresh verification.
- **Partial failure:** downstream failure receives an explicit partial-failure state, never SUCCESS.
- **Uncertain input:** ambiguous input routes to REVIEW with zero downstream mutation.
- **Retry:** transient writes are retried at most twice and attempts are recorded.
- **Proof receipt:** machine-readable result includes run ID, source ID, fingerprint, decision, statuses, object IDs, timestamps, attempts and errors.

## Evaluation
1. Happy path — Gmail → Drive runbook → GitHub issue → Drive receipt, both writes verified.
2. Duplicate replay — same source generates no second issue or receipt.
3. Uncertain input — REVIEW, no downstream write.
4. Partial failure — GitHub may succeed while Drive receipt fails; terminal state remains partial failure.
5. Bounded retry — one transient GitHub failure recovers on attempt 2.

## Known limitations / trust boundary
- The repository test harness uses deterministic fake adapters for repeatable evaluation.
- Its in-memory replay ledger is a local evaluation mechanism, not durable cross-process state.
- The hackathon live path uses the host LLM plus authenticated Gmail/Drive/GitHub connectors; standalone OAuth/API adapters are not shipped in this repository.
- Live durable idempotency is checked against external state using the stable fingerprint before GitHub mutation.
- Judge credentials are not stored in the repository.
- Exact repo visibility/deployment requirements were not visible in the organizer evidence captured before build start; judge access to repository and demo is required.

## Demo claim
Only behavior captured in the live connector run and its readback proof will be claimed as externally executed.

## Live R008 proof result
The live connector path has now been exercised with authenticated Gmail, Google Drive, and GitHub tools. The exact source fingerprint was replayed after the successful round trip, and the repository search returned one matching issue only. This upgrades the three-app path from smoke-only evidence to a verified live happy path plus duplicate-replay proof. It does not prove standalone OAuth adapters or public access to the Drive evidence objects.
