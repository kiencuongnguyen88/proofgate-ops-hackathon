# Live run protocol — ChatGPT connector runtime

The hackathon demo runtime is a tool-enabled agent session with Gmail, Google Drive and GitHub connectors.
The repository contains the deterministic state/proof contract and an offline evaluator; the live run uses the same contract with real connector actions.

## Happy path
1. Select one controlled Gmail message.
2. Record Gmail message ID + fingerprint.
3. Read the Drive runbook.
4. Return ACTION/REVIEW/NO_ACTION.
5. On ACTION only, upsert one GitHub issue using fingerprint as idempotency key.
6. Read back the issue.
7. Write proof receipt to Drive.
8. Read back exact receipt.

## Replay test
Run the same Gmail message again. Expected: same fingerprint; no second issue; result `DUPLICATE_REPLAY_NO_NEW_ACTION`.

## Uncertain-input test
Use an intentionally ambiguous message. Expected: REVIEW; no GitHub mutation.

## Failure test
Inject/observe one downstream failure. Expected: partial-failure status, never SUCCESS.
