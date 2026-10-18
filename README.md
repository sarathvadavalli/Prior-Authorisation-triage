# Synthetic prior-authorisation triage

A small Python and Streamlit demo that evaluates synthetic requests using only payer rules R1–R6. Each assigned outcome includes the applicable rule IDs, a plain-language reason, and any evidence gaps. Decisions come from the pure Python engine, without an LLM.

## Run locally

The confirmed baseline is Python 3.10, Streamlit 1.64.0, and pytest 9.1.1. Package versions are pinned in `requirements.txt`.

From the project root, in PowerShell:

```powershell
py -3.10 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m streamlit run app.py
```

Open the local address printed by Streamlit. With the intended Python environment already active, the launch command is `streamlit run app.py` or `python -m streamlit run app.py`.

## Use the demo

1. Choose a procedure, or choose Other procedure and enter a synthetic procedure name.
2. Answer each red-flag question explicitly: Unknown, No, or Yes.
3. Enter the applicable evidence. Leave unknown numeric values blank; do not substitute zero. Select the documentation answers explicitly.
4. Select Run triage to see the outcome, reason, rules, and evidence gaps.
5. Change a field to clear the previous result, then run triage again. Reset clears the form and result.

For knee arthroscopy, the MRI checkbox records attachment status only. Unchecked means the report is not attached (`False`); the UI does not upload or interpret a report. The Python contract can also represent an unknown attachment status with `None`.

## Workflow status and outcome

| Situation                                                                     | `status`       | `outcome`          | Display                |
| ----------------------------------------------------------------------------- | ---------------- | -------------------- | ---------------------- |
| A required input is missing                                                   | `pending_info` | `None`             | Clarification required |
| Inputs are supplied but evidence is invalid/insufficient or a condition fails | `pending_info` | `Needs info`       | Needs more info        |
| Approval conditions are satisfied                                             | `completed`    | `Approve`          | Approve                |
| A red flag is present or procedure is unlisted                                | `completed`    | `Clinician review` | Clinician review       |

Missing-input clarification has no clinical rule IDs. Needs info retains its applicable procedure rule ID and explains each failed condition. Explicit No/False and numeric zero are supplied answers, not missing inputs. If a request combines missing inputs with invalid or insufficient evidence, the engine asks for the missing information before assigning an outcome.

For example, MRI lumbar spine with 30 days of documented physiotherapy and all red flags absent returns `pending_info` / `Needs info`, rule R1, and the reason:

> Insufficient information to evaluate the MRI lumbar spine request under R1.

Its evidence gap is: `Conservative therapy duration is 30 days; at least 42 days are required.` Pending explanations contain only the procedure, rule context, and a short summary. All missing information, invalid evidence, and failed-condition details appear only in `evidence_gaps`. Clarification with no assigned outcome can reference the relevant rule in its explanation while keeping `rule_ids` empty; unknown red-flag answers use R2 as context.

If the therapy duration is unknown, the outcome is `None` until it is supplied. Needs more info and clinician review are never denials.

## Evaluation order and rules

1. **R2:** Any known cancer history, new neurological deficit, or suspected infection causes Clinician review immediately, regardless of missing/invalid evidence or other unanswered red-flag questions.
2. If no flag is known positive but any red-flag answer is unknown, request clarification without assigning an outcome.
3. **R5:** A procedure outside MRI lumbar spine, CT head, and Knee arthroscopy goes to Clinician review. Do not infer approval from a similar name.
4. For a listed procedure, request all missing required inputs before evaluating its approval conditions.
5. Apply the procedure rule below. Satisfied conditions return Approve; supplied but invalid/insufficient evidence returns Needs info.
6. **R6:** Never automatically deny.

| Rule                   | Required evidence and approval condition                                                                                                        |
| ---------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------- |
| R1 · MRI lumbar spine | At least 42 whole days of documented physiotherapy or medication.                                                                               |
| R3 · CT head          | Finite trauma hours in the inclusive interval 0–48, and GCS documented. No score threshold is defined.                                         |
| R4 · Knee arthroscopy | At least 84 whole days of documented conservative therapy and an attached MRI report. No therapy modality restriction or report interpretation. |

All approval paths require every red flag to be explicitly absent. Therapy days must be nonnegative integers; booleans, numeric strings supplied directly to the engine, and fractional days are invalid. CT trauma hours may be integer or fractional numbers, but not booleans, numeric strings, NaN, or infinity. The UI translates numeric text to numbers while preserving invalid values for the engine to assess after checking red flags.

## Golden acceptance tests

Run from the project root:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_golden.py tests/test_app_golden.py -q
```

With the intended environment active:

```powershell
python -m pytest tests/test_golden.py tests/test_app_golden.py -q
```

The tests compare hand-authored synthetic inputs and expected outputs; they never generate expectations from the engine or automatically accept new snapshots. Every engine case runs twice against the same fixed expected result to check determinism. The UI suite uses Streamlit AppTest in-process, without launching a server or browser.

- `contracts.json`: request/result representation and rejected status/outcome combinations.
- `referrals.json`: R2 precedence, R5 routing, and incomplete red-flag answers.
- `procedures.json`: procedure conditions, boundaries, missing inputs, invalid values, and evidence gaps.
- `ui.json`: fixed widget interactions, visible controls/text, reasons, rule IDs, stale-result clearing, reset, and resubmission.

See [the coverage matrix](tests/golden/coverage.md) for named cases mapped to each requirement. UI golden checks verify rendered Streamlit elements and returned data; they do not verify screenshots, typography, color contrast, responsive layout, or browser rendering.

JSON cannot represent non-finite numbers. Explicit `non_finite_trauma_hours` fixture tags represent NaN and positive/negative infinity; the test harness substitutes those Python values only in inputs. Expected output remains standard JSON.

## Project files

| File                       | Purpose                                                         |
| -------------------------- | --------------------------------------------------------------- |
| `SPEC.md`                | Requirements, including the final status/outcome clarification. |
| `rules.md`               | Concise synthetic payer rules.                                  |
| `AGENTS.md`              | Project instructions for coding agents.                         |
| `PLAN.md`                | Five build tasks and acceptance checks.                         |
| `triage/models.py`       | Dataclass contracts; `None` preserves unknown values.         |
| `triage/engine.py`       | Pure, deterministic rule evaluation and explanations.           |
| `app.py`                 | Synthetic request UI and result rendering.                      |
| `.streamlit/config.toml` | Native theme and disabled Streamlit usage telemetry.            |
| `tests/golden/`          | Authored cases and coverage matrix.                             |

When a payer rule changes, update its requirements, engine conditions/explanations, UI rule reference, and independently reviewed golden cases together. Do not generate expected results by calling the engine being tested.

## Scope and data

Use only synthetic requests. The form has no patient identifier fields and no record upload. Synthetic inputs/results exist in the current Streamlit session's memory; there is no request database, durable request history, or application call to an external clinical service. Do not enter real patient records or protected health information.

This demo does not interpret MRI reports, infer clinical guidelines, make clinical judgments beyond R1–R6, replace a clinician, or issue denials. EHR integration, live payer cases, claims, payments, appeals, production authentication, and a production authorisation workflow are outside its scope.
