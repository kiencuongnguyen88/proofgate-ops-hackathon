# Live runtime boundary

ProofGate Ops has two deliberately separate execution surfaces.

## 1. Repository evaluator

The Python CLI in this repository is a deterministic/reproducible reliability evaluator. It exercises the same decision, runbook-gate, GitHub-action, readback, receipt, retry, failure and replay contract using fake adapters. Optional Ollama can replace the deterministic classifier.

It **does not contain Gmail, Google Drive, or GitHub OAuth credentials or standalone cloud API adapters**. Do not interpret `python -m proofgate.cli ...` as a live three-app execution claim.

The local evaluator's `replay_ledger` is process-local by design. Its purpose is deterministic replay testing, not durable cross-process production state.

## 2. Live connector-native agent

The hackathon live execution surface is a tool-enabled LLM session with authenticated Gmail, Google Drive and GitHub connectors, governed by `AGENT_SYSTEM_PROMPT.md` and `LIVE_RUN_PROTOCOL.md`.

Durable live idempotency is checked against external state using the stable Gmail-derived fingerprint before GitHub mutation. R008 proved this path by replaying the same Gmail source and finding exactly one matching GitHub issue.

The live execution claim is therefore:

> host LLM decision + authenticated external connectors + explicit readback/proof contract

It is **not** a claim that this repository ships a standalone OAuth client.

## R008 evidence boundary

- Gmail source fresh-read: verified.
- Drive runbook write/readback: verified.
- GitHub bounded issue write/readback: verified.
- Drive receipt write/readback: verified.
- Same-source replay: one matching issue; no second issue created.
- Standalone OAuth/API adapter implementation: not claimed.

See `evidence/live_r008_verified.json` and `evidence/README.md`.
