"""Request and response contracts; clinical rule evaluation belongs in the engine.

None represents an unanswered question, not a negative answer. Procedure evidence
is retained without coercion so later validation cannot conceal a known red flag.
"""

from dataclasses import asdict, dataclass, field
from typing import Literal


EvidenceValue = int | float | str | bool | None
Outcome = Literal["Approve", "Needs info", "Clinician review"]
Status = Literal["completed", "pending_info"]
RuleId = Literal["R1", "R2", "R3", "R4", "R5", "R6"]


@dataclass(frozen=True)
class RedFlags:
    history_of_cancer: bool | None = None
    new_neurological_deficit: bool | None = None
    suspected_infection: bool | None = None

    def __post_init__(self) -> None:
        for value in asdict(self).values():
            if value is not None and type(value) is not bool:
                raise ValueError("Red-flag answers must be true, false or null.")


@dataclass(frozen=True)
class TriageRequest:
    procedure: str
    red_flags: RedFlags = field(default_factory=RedFlags)
    conservative_therapy_days: EvidenceValue = None
    conservative_therapy_type: str | None = None
    conservative_therapy_documented: EvidenceValue = None
    trauma_hours: EvidenceValue = None
    gcs_documented: EvidenceValue = None
    mri_report_attached: EvidenceValue = None

    def to_dict(self) -> dict:
        """Return the complete request, preserving missing and invalid evidence."""
        return asdict(self)


@dataclass(frozen=True)
class TriageResult:
    status: Status
    outcome: Outcome | None
    rule_ids: tuple[RuleId, ...]
    explanation: str
    evidence_gaps: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.status not in ("completed", "pending_info"):
            raise ValueError("Invalid status.")
        if not isinstance(self.explanation, str) or not self.explanation.strip():
            raise ValueError("An explanation is not provided.")
        if any(rule not in ("R1", "R2", "R3", "R4", "R5", "R6") for rule in self.rule_ids):
            raise ValueError("Rule IDs must be R1 through R6.")

        if self.status == "completed":
            if self.outcome not in ("Approve", "Clinician review"):
                raise ValueError("Invalid completed outcome")
            if not self.rule_ids:
                raise ValueError("Rule IDs required.")
        else:
            if self.outcome is None:
                if self.rule_ids:
                    raise ValueError("Pending clarification cannot have clinical rule IDs.")
            elif self.outcome == "Needs info":
                if not self.rule_ids:
                    raise ValueError("Rule IDs required.")
            else:
                raise ValueError("Pending result outcome must be Needs info or None.")
            if not self.evidence_gaps:
                raise ValueError("Missing information must be identified.")

    def to_dict(self) -> dict:
        """Return a JSON-ready response with stable field names."""
        return {
            "status": self.status,
            "outcome": self.outcome,
            "rule_ids": list(self.rule_ids),
            "explanation": self.explanation,
            "evidence_gaps": list(self.evidence_gaps),
        }
