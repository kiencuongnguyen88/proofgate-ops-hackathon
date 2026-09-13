# Evidence notes

`live_r008_verified.json` is a **sanitized verification envelope**, not the raw Drive receipt and not an instance of `schemas/proof_receipt.schema.json`.

The live Drive receipt was intentionally written first with the provisional field:

`ACTION_WRITTEN_PENDING_RECEIPT_READBACK`

After an exact Drive readback succeeded, the external run terminal became `SUCCESS_VERIFIED`. The sanitized envelope preserves both facts:

- `proof_receipt.written_status` = the exact status written before readback;
- `proof_receipt.readback_verified` = whether exact readback passed;
- `terminal_status` = the verified run terminal after readback.

This separation avoids retroactively rewriting the original receipt and preserves chronology.

The local deterministic receipt schema under `schemas/` belongs to the repository evaluator. Live connector evidence is kept as a separate provenance object so a captured external proof is not misrepresented as locally generated output.
