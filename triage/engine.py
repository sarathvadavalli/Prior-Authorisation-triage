"""Deterministic synthetic prior-authorisation decisions using only R1-R6."""

from math import isfinite

from triage.models import EvidenceValue, RuleId, TriageRequest, TriageResult


LISTED_PROCEDURES = ("MRI lumbar spine", "CT head", "Knee arthroscopy")
RED_FLAG_LABELS = (
    ("history_of_cancer", "History of cancer"),
    ("new_neurological_deficit", "New neurological deficit"),
    ("suspected_infection", "Suspected infection"),
)


def _pending_explanation(procedure: str, rule: RuleId) -> str:
    """Summarize pending evaluation; actionable details belong in evidence_gaps."""
    return f"Insufficient information to evaluate the {procedure} request under {rule}."


def decide(request: TriageRequest) -> TriageResult:
    """Check R2, clarification, R5, then applicable procedure evidence in order.

R6 is enforced by the result contract. Missing evidence has no outcome;
failed conditions return Needs info with pending_info workflow status.
"""
    present = [
        label for name, label in RED_FLAG_LABELS
        if getattr(request.red_flags, name) is True
    ]
    if present:
        return TriageResult(
            status="completed",
            outcome="Clinician review",
            rule_ids=("R2",),
            explanation=(
                "Reported red flags: " + ", ".join(present)
                + ". R2 requires clinician review regardless of procedure or other evidence."
            ),
        )

    unknown = [
        label for name, label in RED_FLAG_LABELS
        if getattr(request.red_flags, name) is None
    ]
    if unknown:
        return TriageResult(
            status="pending_info",
            outcome=None,
            rule_ids=(),
            explanation=_pending_explanation(request.procedure, "R2"),
            evidence_gaps=tuple(label + " status is unknown." for label in unknown),
        )

    if request.procedure not in LISTED_PROCEDURES:
        return TriageResult(
            status="completed",
            outcome="Clinician review",
            rule_ids=("R5",),
            explanation=(
                f"Procedure '{request.procedure}' is not listed in R1, R3, or R4. "
                "R5 requires clinician review; no listed approval rule applies."
            ),
        )

    if request.procedure == "CT head":
        required = (
            (request.trauma_hours, "Trauma time"),
            (request.gcs_documented, "GCS documentation status"),
        )
    else:
        required = (
            (request.conservative_therapy_days, "Conservative therapy duration"),
            (request.conservative_therapy_documented, "Conservative therapy documentation status"),
        )
        if request.procedure == "MRI lumbar spine":
            required += ((request.conservative_therapy_type, "Conservative therapy type"),)
        else:
            required += ((request.mri_report_attached, "MRI report attachment status"),)

    missing = tuple(f"{label} is missing." for value, label in required if value is None)

    if missing:
        rule: RuleId = "R3" if request.procedure == "CT head" else "R1" if request.procedure == "MRI lumbar spine" else "R4"
        return TriageResult(
            status="pending_info",
            outcome=None,
            rule_ids=(),
            explanation=_pending_explanation(request.procedure, rule),
            evidence_gaps=missing,
        )

    if request.procedure == "CT head":
        return _ct_head(request)
    return _therapy_procedure(request)


def _yes_gap(value: EvidenceValue, label: str) -> list[str]:
    """Require explicit documentation/attachment without coercing truthy values."""
    if value is True:
        return []
    if value is None:
        return [f"{label} status is missing."]
    if value is False:
        return [f"{label} is required."]
    return [f"{label} status is invalid; provide yes or no."]


def _therapy_procedure(request: TriageRequest) -> TriageResult:
    is_mri = request.procedure == "MRI lumbar spine"
    minimum = 42 if is_mri else 84
    rule: RuleId = "R1" if is_mri else "R4"
    gaps: list[str] = []
    days = request.conservative_therapy_days

    if type(days) is not int or days < 0:
        gaps.append("Conservative therapy duration is invalid; provide a nonnegative integer number of days.")
    elif days < minimum:
        gaps.append(f"Conservative therapy duration is {days} days; at least {minimum} days are required.")

    gaps.extend(_yes_gap(request.conservative_therapy_documented, "Conservative therapy documentation"))

    if is_mri:
        if request.conservative_therapy_type is None:
            gaps.append("Conservative therapy type is missing; provide physiotherapy or medication.")
        elif request.conservative_therapy_type not in ("physiotherapy", "medication"):
            gaps.append("Conservative therapy type is invalid; R1 requires physiotherapy or medication.")
    else:
        gaps.extend(_yes_gap(request.mri_report_attached, "MRI report attachment"))

    if gaps:
        return TriageResult(
            "pending_info", "Needs info", (rule,),
            _pending_explanation(request.procedure, rule), tuple(gaps),
        )

    explanation = (
        f"MRI lumbar spine has {days} days of documented {request.conservative_therapy_type}, "
        "meeting the 42-day minimum under R1; no red flags were reported."
        if is_mri else
        f"Knee arthroscopy has {days} days of documented conservative therapy, meeting the 84-day minimum, "
        "and an MRI report is attached under R4; no red flags were reported."
    )
    return TriageResult("completed", "Approve", (rule,), explanation)


def _ct_head(request: TriageRequest) -> TriageResult:
    gaps: list[str] = []
    hours = request.trauma_hours

    if type(hours) not in (int, float) or (type(hours) is float and not isfinite(hours)):
        gaps.append("Trauma time is invalid; provide a finite number of hours.")
    elif hours < 0:
        gaps.append(f"Trauma time is {hours} hours; negative hours are invalid.")
    elif hours > 48:
        gaps.append(f"Trauma time is {hours} hours; R3 requires 0 to 48 hours inclusive.")
    gaps.extend(_yes_gap(request.gcs_documented, "GCS documentation"))
    if gaps:
        return TriageResult(
            "pending_info", "Needs info", ("R3",),
            _pending_explanation(request.procedure, "R3"), tuple(gaps),
        )
        
    return TriageResult(
        "completed", "Approve", ("R3",),
        f"Trauma occurred {hours} hours ago, within 0 to 48 hours inclusive, and GCS is documented under R3; "
        "no red flags were reported.",
    )
