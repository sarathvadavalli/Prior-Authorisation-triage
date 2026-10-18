"""Compare contracts and engine responses with authored synthetic golden cases."""

import json
from pathlib import Path

import pytest

from triage.models import RedFlags, TriageRequest, TriageResult
from triage.engine import decide

CASES = json.loads((Path(__file__).parent / "golden" / "contracts.json").read_text(encoding="utf-8"))


@pytest.mark.parametrize("case", CASES, ids=[case["id"] for case in CASES])
def test_contract_golden(case):
    payload = dict(case["input"])
    try:
        if case["contract"] == "request":
            if "red_flags" in payload:
                payload["red_flags"] = RedFlags(**payload["red_flags"])
            actual = TriageRequest(**payload).to_dict()
        elif case["contract"] == "result":
            payload["rule_ids"] = tuple(payload["rule_ids"])
            payload["evidence_gaps"] = tuple(payload["evidence_gaps"])
            actual = TriageResult(**payload).to_dict()
        else:
            pytest.fail(f"Unknown golden contract: {case['contract']}")
    except ValueError as error:
        actual = {"error": str(error)}

    # Compare JSON values so serializability is part of the contract check.
    assert json.loads(json.dumps(actual, allow_nan=False)) == case["expected"]


REFERRALS = json.loads((Path(__file__).parent / "golden" / "referrals.json").read_text(encoding="utf-8"))
PROCEDURES = json.loads((Path(__file__).parent / "golden" / "procedures.json").read_text(encoding="utf-8"))


@pytest.mark.parametrize("case", REFERRALS + PROCEDURES, ids=[case["id"] for case in REFERRALS + PROCEDURES])
def test_referral_golden(case):
    payload = dict(case["input"])
    # JSON has no NaN/infinity values. These explicit fixture tags let authored
    # cases exercise actual non-finite Python floats without nonstandard JSON.
    if "non_finite_trauma_hours" in case:
        payload["trauma_hours"] = {
            "nan": float("nan"), "infinity": float("inf"), "negative_infinity": -float("inf")
        }[case["non_finite_trauma_hours"]]
    if "red_flags" in payload:
        payload["red_flags"] = RedFlags(**payload["red_flags"])
    request = TriageRequest(**payload)
    # Each call must independently match the fixed expected result.
    for _ in range(2):
        actual = decide(request).to_dict()
        assert json.loads(json.dumps(actual, allow_nan=False)) == case["expected"]
