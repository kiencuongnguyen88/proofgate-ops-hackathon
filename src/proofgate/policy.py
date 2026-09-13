from __future__ import annotations

import re
from .models import Decision, DecisionResult, Signal

ACTION_TERMS = (
    "action required",
    "deadline",
    "due by",
    "submit",
    "submission",
    "accepted",
    "approval required",
    "confirm by",
    "eligibility",
    "judging",
    "result",
)

NO_ACTION_TERMS = (
    "newsletter",
    "weekly digest",
    "fyi only",
    "no action required",
)

UNCERTAINTY_TERMS = (
    "maybe",
    "might need",
    "not sure",
    "possibly",
    "if needed",
)


def classify(signal: Signal) -> DecisionResult:
    text = re.sub(r"\s+", " ", f"{signal.subject}\n{signal.body}").strip().lower()
    if len(text) < 25:
        return DecisionResult(Decision.REVIEW, 0.35, "Input is too sparse for safe action.")

    if any(term in text for term in NO_ACTION_TERMS):
        return DecisionResult(Decision.NO_ACTION, 0.95, "Explicit informational/no-action signal.")

    uncertainty_hits = [t for t in UNCERTAINTY_TERMS if t in text]
    action_hits = [t for t in ACTION_TERMS if t in text]

    if uncertainty_hits and not action_hits:
        return DecisionResult(
            Decision.REVIEW,
            0.55,
            f"Ambiguous intent: {', '.join(uncertainty_hits[:2])}.",
        )

    if action_hits:
        confidence = min(0.98, 0.72 + 0.06 * len(action_hits))
        return DecisionResult(
            Decision.ACTION,
            confidence,
            f"Material action signal(s): {', '.join(action_hits[:4])}.",
        )

    return DecisionResult(
        Decision.REVIEW,
        0.50,
        "No explicit action or no-action signal; human review is safer.",
    )
