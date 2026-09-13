from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any


class Decision(str, Enum):
    ACTION = "ACTION"
    REVIEW = "REVIEW"
    NO_ACTION = "NO_ACTION"


@dataclass(frozen=True)
class Signal:
    source_app: str
    source_id: str
    subject: str
    body: str
    sender: str = ""
    received_at: str = ""


@dataclass(frozen=True)
class DecisionResult:
    decision: Decision
    confidence: float
    reason: str


@dataclass
class StepResult:
    step: str
    app: str
    status: str
    object_id: str | None = None
    detail: str = ""
    attempts: int = 1
    readback_verified: bool | None = None


@dataclass
class RunReceipt:
    run_id: str
    source_id: str
    fingerprint: str
    decision: str
    confidence: float
    status: str
    started_at: str
    finished_at: str
    steps: list[StepResult] = field(default_factory=list)
    output_object_ids: dict[str, str] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)
    replay_of_run_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
