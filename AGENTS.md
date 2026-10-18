# Project instructions

Build a synthetic prior-authorisation triage demo using Python and Streamlit.

Read SPEC.md before changing decision logic, validation, UI outcomes, or tests.
Treat SPEC.md as the source of truth for requirements.

- Implement only rules R1–R6.
- Keep decisions deterministic in a pure Python function; do not use an LLM.
- Preserve red-flag precedence.
- Never produce a Deny outcome.
- Use synthetic data only.
- Include rule IDs, explanations, and missing evidence in results.
- Test all rules, boundaries, missing evidence, and precedence.