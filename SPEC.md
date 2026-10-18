# SPEC.md — Synthetic Prior Authorisation Triage Demo

## Goal
Build a small, deterministic Python and Streamlit demonstration that classifies synthetic prior-authorisation requests using **only** payer rules R1–R6. Display the outcome, applicable rule ID(s), a concise explanation, and any missing or insufficient evidence. The system must never deny automatically.

## Users
- **Demo request submitter:** enters synthetic procedure and supporting evidence.
- **Payer triage reviewer:** examines the decision and its rule-based explanation.
- **Clinician reviewer:** receives cases classified as Clinician review; the demo does not implement clinical decisions.

## Inputs
- `procedure`: one of `MRI lumbar spine`, `CT head`, `Knee arthroscopy`, or an unlisted procedure string.
- `red_flags`: presence/absence of history of cancer, new neurological deficit, or suspected infection.
- `conservative_therapy_days`: nonnegative integer or missing, where applicable.
- `conservative_therapy_type`: physiotherapy or medication for MRI lumbar spine, where applicable; knee arthroscopy requires documented conservative therapy but R4 does not specify a modality.
- `conservative_therapy_documented`: yes/no, where applicable.
- `trauma_hours`: number of hours since trauma, or missing, for CT head.
- `gcs_documented`: yes/no for CT head; no minimum GCS score is defined by these rules.
- `mri_report_attached`: yes/no for knee arthroscopy.

Only synthetic inputs are permitted. No real patient identifiers or records are collected.

## Outcomes
1. **Approve:** the applicable procedure-specific approval conditions are all satisfied and no red flag is present.
2. **Needs info:** all required inputs have been supplied, but applicable evidence is invalid or insufficient, or a rule condition is not satisfied, and no red flag is present. Return `status=pending_info`, `outcome="Needs info"`, applicable rule IDs, an explanation, and evidence gaps. Display this outcome as **Needs more info**. This does not mean denial.
3. **Clinician review:** any red flag is present, or the procedure is not listed in R1/R3/R4. This is a referral, not a denial.

The application must not produce a `Deny` outcome.

Workflow status and outcome are separate:

| Situation | Status | Outcome | Clinical rule IDs |
| --- | --- | --- | --- |
| A required input is missing | `pending_info` | `None` | None |
| Inputs are supplied but a condition fails | `pending_info` | `Needs info` | Applicable procedure rule |
| All approval conditions are met | `completed` | `Approve` | Applicable procedure rule |
| A red flag is reported or procedure is unlisted | `completed` | `Clinician review` | R2 or R5 |

For every `pending_info` response, keep `explanation` to a short summary containing the procedure and relevant rule context: `Insufficient information to evaluate the MRI lumbar spine request under R1.` Put all actual missing-input details, invalid values, failed conditions, and required thresholds only in `evidence_gaps`; do not repeat them in the explanation. Unknown red-flag clarification uses R2 as the explanation context. Referencing a rule in a clarification explanation does not assign an outcome or populate its `rule_ids` field.

**Pending clarification** refers to the first row: no outcome is assigned until the missing information is supplied. Missing means `None`, not a supplied `False` answer or numeric zero. For MRI lumbar spine require duration, therapy type, and documentation status; for CT head require trauma hours and GCS documentation status; for knee arthroscopy require duration, documentation status, and MRI attachment status. A supplied `False` documentation/attachment answer is a failed condition, not a missing input. A supplied malformed value is invalid evidence, not a missing input. If both missing and invalid/insufficient evidence exist, request the missing inputs first without assigning an outcome. Each pending response explains what must be addressed. A known positive red flag still takes precedence over missing evidence and incomplete answers for other flags.

## Evaluation order
1. Check red flags first (R2). If any are present, return Clinician review, regardless of other rule conditions.
2. Identify the procedure. If not listed in R1/R3/R4, return Clinician review (R5).
3. Check the listed procedure's required inputs. If any are missing, return `pending_info` with outcome `None`. Otherwise apply the procedure rule: return `completed` / Approve when satisfied, or `pending_info` / Needs info for invalid, insufficient, or unsatisfied evidence.
4. Enforce R6 globally: never auto-deny.

Input validation should preserve this precedence. In particular, malformed or missing procedure-specific evidence must not hide a known red flag. If the system cannot determine whether a red flag exists because the red-flag input is incomplete, it must not silently assume there is no red flag; prompt for that information before a final classification. This is an implementation safety constraint, not an additional clinical approval rule.

## Acceptance criteria

### R1 — MRI lumbar spine
- Given at least 42 days of **documented** physiotherapy or medication and no red flags, outcome is Approve.
- Exactly 42 days qualifies; 41 days does not.
- Missing therapy duration, type, or documentation status yields pending clarification (`status=pending_info`, `outcome=None`) unless R2 applies. Identify every missing applicable input.
- With all required inputs supplied, undocumented therapy, an unsupported therapy type, invalid evidence, or duration under 42 days yields `pending_info` / Needs info (unless R2 applies).
- Do not substitute undocumented therapy for documented therapy.

### R2 — Red flags
- History of cancer, new neurological deficit, or suspected infection individually causes Clinician review.
- Multiple red flags also cause Clinician review.
- This result overrides otherwise approvable, incomplete, or invalid procedure-specific evidence, and applies to unlisted procedures too.

### R3 — CT head
- Trauma time in the inclusive range `0 <= trauma_hours <= 48` **and** GCS documented yields Approve, absent red flags.
- Both boundary values 0 and 48 qualify when GCS is documented.
- Negative trauma hours are invalid and yield Needs info, absent red flags.
- Missing trauma time or GCS documentation status yields `pending_info` / `None`, absent red flags.
- With required inputs supplied, trauma time greater than 48 or GCS explicitly not documented yields `pending_info` / Needs info, absent red flags.
- No GCS score threshold is imposed.

### R4 — Knee arthroscopy
- At least 84 days of documented conservative therapy **and** an attached MRI report yields Approve, absent red flags.
- Exactly 84 days qualifies; 83 days does not.
- Missing therapy duration, documentation status, or MRI attachment status yields `pending_info` / `None`, absent red flags.
- With required inputs supplied, insufficient/invalid therapy, therapy explicitly undocumented, or MRI report explicitly not attached yields `pending_info` / Needs info, absent red flags.
- The system checks whether the MRI report is attached; it does not interpret the report.

### R5 — Unlisted procedure
- A procedure other than MRI lumbar spine, CT head, or knee arthroscopy yields Clinician review.
- Do not infer coverage or approval from similarity to a listed procedure.

### R6 — Never deny
- No input or rule path returns Deny.
- Every assigned outcome is exactly one of Approve, Needs info, or Clinician review. Only Approve and Clinician review have `completed` workflow status; Needs info has `pending_info` status. Missing inputs have no assigned outcome.
- Clinician review is not a denial; any actual denial is outside the demo.

## General acceptance criteria
- Streamlit displays a synthetic request form and a human-readable outcome.
- Results include rule ID(s), explanation, and missing/insufficient evidence when relevant.
- Pending explanations are concise; actionable details appear only in evidence gaps. For 40 days of otherwise qualifying MRI therapy, the explanation is `Insufficient information to evaluate the MRI lumbar spine request under R1.` and the gap is `Conservative therapy duration is 40 days; at least 42 days are required.`
- A pure Python function makes the decision deterministically without an LLM.
- Automated tests cover every rule, threshold boundaries, negative trauma hours, missing evidence, red-flag precedence, and unlisted procedures.
- No real patient data is stored or sent to an external service.

## Non-goals
- **No automatic denial** or clinician decision replacement.
- **No real patient data**, protected health information, or live payer cases.
- **No EHR integration** or external clinical systems.
- No clinical guideline inference, medical-necessity judgment beyond R1–R6, or interpretation of attached MRI reports.
- No claims processing, payment, appeals, or production-grade authorization workflow.
