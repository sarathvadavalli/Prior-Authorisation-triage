# Build plan

Build tasks and acceptance checks for the implemented demo. See README.md for usage and tests/golden/coverage.md for the acceptance matrix.

## Sources and constraints

Final requirement clarification: for every listed procedure, missing required inputs produce `pending_info`, `outcome=None`, and no clinical rule IDs. When required inputs are supplied but a condition fails, return `pending_info`, outcome `Needs info`, applicable rule IDs, reason, and evidence gaps; display this as Needs more info. Approval and clinician review retain `completed` status. Known red flags still take precedence under R2. This supersedes earlier status wording in the original tasks below; approval thresholds are unchanged.

- Read `AGENTS.md`, `SPEC.md`, and `rules.md`. `SPEC.md` is the source of truth; its documented-therapy requirements and evaluation precedence clarify the shorter payer rules.
- Use Python and Streamlit, synthetic inputs only, and a deterministic pure Python decision function without an LLM.
- Implement only R1–R6. Assigned outcomes are Approve, Needs info, or Clinician review; never Deny. Only Approve and Clinician review have completed workflow status.
- Known red flags take precedence over missing or invalid procedure evidence and unlisted procedures. Incomplete red-flag information without a known positive must prompt for clarification before classification.
- Results contain applicable rule IDs, a concise explanation, and missing, invalid, or insufficient evidence where relevant.
- Use golden tests only, as explicitly requested: fixed synthetic inputs and independently authored expected outputs. Do not generate expectations from the implementation, automatically accept updated snapshots, or add other test categories.
- Keep `AGENTS.md` and unrelated user files unchanged. Update `SPEC.md` and `rules.md` to capture the user's final workflow clarification during task 5. Dependency installations and generated caches are not source artifacts.

## Task 1 — Establish the request/result contract and golden-test harness

Create a small Python package with request and result structures, explicit unknown red-flag states, and a pending-information response distinct from a completed classification. Define stable serialized output fields for outcome, rule IDs, explanation, and evidence gaps. Establish a test runner that compares these structures against hand-authored JSON expectations. Record Python and Streamlit dependencies; resolve a supported Streamlit version and its matching documentation during implementation.

Files:
- Create `requirements.txt`.
- Create `triage/__init__.py`.
- Create `triage/models.py`.
- Create `tests/test_golden.py`.
- Create `tests/golden/contracts.json`.

Acceptance check: `python -m pytest tests/test_golden.py -q` passes fixed contract cases covering complete evidence, explicitly missing evidence, unknown red-flag states, and the pending-information response. These cases check representation only; they do not claim the decision engine exists yet.

## Task 2 — Implement precedence and referral rules

Add the pure decision function. Evaluate known positive red flags first (R2), require clarification when red flags remain indeterminate without any known positive, and route unlisted procedures to Clinician review (R5) after red-flag status is established. Apply R6 to completed results. Keep procedure-specific evidence validation after these checks. At this intermediate stage, golden cases exercise referral and pending-information paths only.

The function itself must return a clear, request-specific reason and the applicable rule ID(s) for every decision; the UI must not construct the reasoning. For R2, name the reported red flag(s) and explain why clinician review takes precedence. For R5, name the unlisted procedure and explain that no listed approval rule applies. Pending clarification uses a concise procedure/rule summary; only evidence gaps name unanswered red-flag questions. Rule context in the explanation does not populate clinical rule IDs or assign an outcome.

Files:
- Create `triage/engine.py`.
- Create `tests/golden/referrals.json`.
- Change `tests/test_golden.py`.

Acceptance check: the cumulative golden suite passes cases for each individual red flag, multiple red flags, positive flags with other flags unknown, positive flags with otherwise approvable/missing/invalid procedure evidence, and positive flags on unlisted procedures. Also cover unlisted and similar-but-unlisted procedure strings with all flags absent, plus incomplete red-flag information that requires clarification. Expected outputs explicitly verify R2 precedence, R5 routing, explanations, and absence of Deny.

Golden expectations must compare the exact reason text and rule IDs returned by the function, including the specific red flags or unlisted procedure responsible for referral and the unanswered fields responsible for pending clarification.

## Task 3 — Implement procedure-specific approval and evidence checks

Complete R1, R3, and R4 in the same pure function. MRI lumbar spine requires documented physiotherapy or medication for at least 42 days. CT head requires trauma hours in the inclusive range 0–48 and documented GCS, with no score threshold. Knee arthroscopy requires at least 84 days of documented conservative therapy and an attached MRI report, without a modality restriction or report interpretation. Return Needs info for missing, invalid, or insufficient applicable evidence when red flags are absent. Report all relevant evidence gaps in a stable order.

For every Approve or Needs info decision, the function must return the applicable procedure rule ID. Pending explanations contain only a short procedure/rule summary; supplied values, required thresholds, and missing or invalid evidence belong only in evidence gaps. Approval reasons explain which conditions were satisfied and that no red flags were reported. Return these fields as data alongside the outcome and status.

Required golden example: MRI lumbar spine, all red flags absent, 30 days of documented physiotherapy returns status `pending_info`, outcome `Needs info`, includes rule `R1`, and returns the explanation: "Insufficient information to evaluate the MRI lumbar spine request under R1." Only evidence gaps contain the duration shortfall: "Conservative therapy duration is 30 days; at least 42 days are required." This is not a denial.

Files:
- Change `triage/engine.py`.
- Create `tests/golden/procedures.json`.
- Change `tests/test_golden.py` to load the procedure golden cases and represent non-finite numeric inputs using explicit fixture tags.

Acceptance check: the cumulative golden suite passes fixed cases for MRI at 41/42/43 days and both permitted modalities; knee at 83/84/85 days; CT at negative/0/48/over-48 hours; and missing documentation, missing duration, missing GCS documentation, and missing MRI attachment. Include negative, non-integer, and malformed therapy durations; malformed/non-finite trauma values; unsupported/missing MRI therapy types; multiple simultaneous evidence gaps; and red flags overriding invalid evidence for every listed procedure. Every completed expected result uses one of the three permitted outcomes and contains its rule IDs, explanation, and evidence gaps.

Include the 30-day MRI example above. Golden expectations must compare exact returned reason text and rule IDs for every decision, covering satisfied conditions, insufficient thresholds, missing/invalid evidence, and multiple evidence gaps.

## Task 4 — Build the Streamlit synthetic request form and result display

Add the procedure selector with an unlisted-procedure text entry, explicit red-flag answers including unknown, and applicable evidence controls. Preserve missing values rather than converting them to zero or false. Display pending clarification when required; otherwise render the engine result with its rule IDs, explanation, and evidence gaps. Clearly label Needs info and Clinician review as non-denial outcomes. Use a documentation checkbox for MRI report attachment status, without uploading or interpreting patient records. Do not collect identifiers, persist requests, or call external services.

Files:
- Create `app.py`.
- Create `tests/test_app_golden.py`.
- Create `tests/golden/ui.json`.
- Create `.streamlit/config.toml` for the requested professional visual theme and to disable usage telemetry.

Acceptance check: `python -m pytest tests/test_golden.py tests/test_app_golden.py -q` passes fixed Streamlit AppTest interaction cases compared with hand-authored expected visible text and outcome fields. Cover each listed procedure, an unlisted procedure, each outcome, missing evidence, pending red-flag clarification, red-flag precedence over invalid procedure evidence, and editing/resubmitting a request without showing a stale result. These are golden comparisons, not image snapshots or a separate testing methodology.

## Task 5 — Finish the golden acceptance matrix and usage documentation

Review the fixed cases against every SPEC acceptance criterion and fill any gaps. Document installation, launch and golden-test commands, synthetic-data restrictions, output meanings, evaluation order, and the demo's limits. Map R1–R6 and the incomplete-red-flag constraint to named golden cases so reviewers can trace coverage.

Files:
- Create `README.md`.
- Create `tests/golden/coverage.md`.
- Change `tests/golden/contracts.json`.
- Change `tests/golden/referrals.json`.
- Change `tests/golden/procedures.json`.
- Change `tests/golden/ui.json`.
- Change `SPEC.md` and `rules.md` to align the documented workflow with the user's final clarification.
- Change `PLAN.md` to record completion and the final workflow semantics.

Acceptance check: run the complete golden suite with `python -m pytest tests/test_golden.py tests/test_app_golden.py -q`. All fixed expected outputs must pass, including repeated identical requests producing identical outputs. The coverage matrix must identify golden cases for every rule, threshold, missing-evidence condition, red-flag precedence scenario, and unlisted procedure behavior required by SPEC. README commands must match the implemented entry points (`streamlit run app.py` and the golden-suite command).

## Execution order

Implement tasks 1–5 sequentially. Each task must pass its cumulative golden acceptance check before the next begins. Do not expand the clinical rules or introduce a Deny outcome to resolve an implementation ambiguity.

## Completion

Tasks 1–5 are complete with the final workflow clarification incorporated into the requirements and golden expectations. The acceptance command is `python -m pytest tests/test_golden.py tests/test_app_golden.py -q`; the current suite has 134 golden cases (22 contracts, 20 referrals, 66 procedure decisions, 26 UI scenarios), including concise pending explanations with actionable details only in evidence gaps. README.md contains setup, launch, testing, workflow semantics, and scope; tests/golden/coverage.md maps acceptance criteria to existing named cases. UI verification covers Streamlit elements and interactions, not screenshots or browser rendering.
