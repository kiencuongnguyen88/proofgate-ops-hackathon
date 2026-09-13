# ProofGate Ops

**One evidence-gated AI operations agent across Gmail → Google Drive → GitHub.**

ProofGate turns one material email into one bounded, verified operations action. It reads the source signal, decides `ACTION | REVIEW | NO_ACTION`, consults a Drive runbook, performs one GitHub action only when allowed, reads the result back, and writes a machine-readable proof receipt to Drive.

## External apps
- **Gmail** — source signal / immutable message ID
- **Google Drive** — runbook + proof receipt
- **GitHub** — action issue + readback

## Why this is an agent, not a fixed script
The system must decide whether evidence is actionable, refuse ambiguous input, consult policy, deduplicate replays, and report partial failure honestly. The action path changes based on evidence and state.

## Reliability contract
- stable source IDs + SHA-256 fingerprint
- `ACTION | REVIEW | NO_ACTION`
- idempotency / duplicate replay guard
- post-write readback
- bounded retries
- explicit partial-failure states
- machine-readable proof receipt

## Run the deterministic evaluator
Requires Python 3.11+; no secrets required.

```bash
# No network install is required for the evaluator.
# PowerShell:
$env:PYTHONPATH = "src"
python -m unittest discover -s tests -v
python -m proofgate.cli demo/fixtures/happy_action.json --replay
python -m proofgate.cli demo/fixtures/uncertain_review.json

# macOS/Linux:
PYTHONPATH=src python -m unittest discover -s tests -v
PYTHONPATH=src python -m proofgate.cli demo/fixtures/happy_action.json --replay
```

## Live connector run
See [`LIVE_RUN_PROTOCOL.md`](LIVE_RUN_PROTOCOL.md). The live hackathon demo uses an authenticated tool-enabled agent runtime with Gmail, Drive, and GitHub connectors. Credentials and private tokens are never committed to this repository.


## AI decision runtime
The **live hackathon run uses the host LLM in the tool-enabled connector session** for the `ACTION | REVIEW | NO_ACTION` decision. The repository also includes:

- a deterministic decision oracle for repeatable reliability tests; and
- an optional local Ollama decision path (`qwen3:4b` by default) so the core can be exercised without a metered cloud-model API.

Optional local-model command:

```bash
# PowerShell
$env:PYTHONPATH = "src"
python -m proofgate.cli demo/fixtures/happy_action.json --ollama --model qwen3:4b
```

The deterministic oracle is an evaluation/fail-safe surface; it is not presented as the live AI model.

## Execution boundary
The repository and the live agent share one reliability contract, but they are different execution surfaces:

- **Repository CLI:** deterministic/fault-injection evaluator; fake app adapters; optional Ollama decision path.
- **Live hackathon agent:** host LLM + authenticated Gmail/Drive/GitHub connectors governed by `AGENT_SYSTEM_PROMPT.md`.

The repository does **not** claim to ship standalone Gmail/Drive/GitHub OAuth adapters. Local `--replay` uses a process-local ledger for deterministic tests; the live R008 replay used the stable fingerprint against external GitHub state. See [`LIVE_RUNTIME_BOUNDARY.md`](LIVE_RUNTIME_BOUNDARY.md).

## Reliability evaluation
See [`SYSTEM_RELIABILITY_BRIEF.md`](SYSTEM_RELIABILITY_BRIEF.md) and the tests under [`tests/`](tests/).

## Two-minute demo
See [`DEMO_SCRIPT.md`](DEMO_SCRIPT.md).

**Demo URL:** https://youtu.be/30siPYrRLRo

## Repository / demo access
Organizer live briefing requires judges to be able to access both the repository and the two-minute demo. This project does not assume that “judge-accessible” necessarily means “public” unless the final submission instructions state that explicitly.

## Known limitations
- The offline evaluator uses deterministic fake adapters for reproducible fault injection.
- The local replay ledger is process-local and is not claimed as durable production state.
- Standalone cloud OAuth/API adapters are not included; authenticated external actions are claimed only from the separate connector-native live proof captured during the hackathon.

## Live connector proof — R008
A controlled live run was completed during the hackathon build window using the same reliability contract:

- Gmail source fresh-read: PASS
- Drive runbook write + exact readback: PASS
- GitHub bounded issue action + fresh readback: PASS
- Drive proof receipt write + exact readback: PASS
- Replay of the same Gmail source: `DUPLICATE_REPLAY_NO_NEW_ACTION`
- Matching GitHub issues for the fingerprint after replay: **1**

Sanitized machine-readable evidence is in [`evidence/live_r008_verified.json`](evidence/live_r008_verified.json). The public GitHub action target used for the connector proof is issue #2 in `kiencuongnguyen88/diamond-evidence-gate`. Drive objects are recorded by ID; access is not claimed for judges unless explicitly shared later.
