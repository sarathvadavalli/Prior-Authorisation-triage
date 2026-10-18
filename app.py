"""Synthetic triage interface. Decisions and explanations come from the engine."""

import streamlit as st

from triage.engine import LISTED_PROCEDURES, decide
from triage.models import RedFlags, TriageRequest


st.set_page_config(
    page_title="Prior authorisation | Triage",
    page_icon=":material/fact_check:",
    layout="wide",
)

ANSWERS = {"Unknown": None, "No": False, "Yes": True}
st.session_state.setdefault("last_result", None)
st.session_state.setdefault("request_updated", False)


def clear_result() -> None:
    """Invalidate the displayed decision as soon as any request field changes."""
    if st.session_state.last_result is not None:
        st.session_state.request_updated = True
    st.session_state.last_result = None


def reset_request() -> None:
    for key in (
        "procedure", "unlisted_procedure", "history_of_cancer",
        "new_neurological_deficit", "suspected_infection", "mri_days", "mri_type",
        "mri_documented", "knee_days", "knee_documented", "mri_report_attached",
        "ct_hours", "gcs_documented",
    ):
        st.session_state.pop(key, None)
    st.session_state.last_result = None
    st.session_state.request_updated = False


def answer(label: str, key: str) -> bool | None:
    selected = st.segmented_control(
        label, list(ANSWERS), default="Unknown", key=key,
        on_change=clear_result, required=True,
    )
    return ANSWERS[selected] if selected is not None else None


def numeric_evidence(raw: str):
    """Translate text controls into numbers, retaining invalid and missing input.

Text controls let the engine see invalid evidence after checking red flags,
instead of having a numeric widget block submission first.
"""
    raw = raw.strip()
    if not raw:
        return None
    try:
        return int(raw)
    except ValueError:
        try:
            return float(raw)
        except ValueError:
            return raw


with st.container(horizontal=True, vertical_alignment="center"):
    st.badge("SYNTHETIC DEMO", icon=":material/science:", color="primary")
    st.caption("PRIOR AUTHORISATION  /  REVIEW WORKSPACE")
    
st.title("Every decision, explained.")
st.markdown("Explore a synthetic request and see exactly which payer rule applies.")
st.caption("Synthetic inputs only. Do not enter real patient information or upload patient records.")

request_column, result_column = st.columns([1.45, 1], gap="medium")

with request_column:
    with st.container(border=True):
        st.subheader("Build a request", icon=":material/edit_document:")
        st.caption("01 / PROCEDURE")
        procedure = st.selectbox(
            "Procedure", [*LISTED_PROCEDURES, "Other procedure"],
            key="procedure", on_change=clear_result,
        )
        if procedure == "Other procedure":
            procedure = st.text_input(
                "Unlisted procedure", key="unlisted_procedure",
                placeholder="e.g. Ultrasound abdomen", on_change=clear_result,
                help="Use a synthetic procedure name only.",
            )

        st.caption("02 / RED FLAGS")
        st.markdown("**Confirm each red flag**")
        st.caption("Any reported red flag routes the request to a clinician first.")
        flags = RedFlags(
            history_of_cancer=answer("History of cancer", "history_of_cancer"),
            new_neurological_deficit=answer("New neurological deficit", "new_neurological_deficit"),
            suspected_infection=answer("Suspected infection", "suspected_infection"),
        )

        st.caption("03 / SUPPORTING EVIDENCE")
        evidence = {}
        if procedure in ("MRI lumbar spine", "Knee arthroscopy"):
            prefix = "mri" if procedure == "MRI lumbar spine" else "knee"
            days = st.text_input(
                "Conservative therapy duration (days)", key=f"{prefix}_days",
                placeholder="Enter days, or leave blank if unknown", on_change=clear_result,
                help=(
                    "Enter whole days. Missing MRI duration keeps evaluation pending until you provide it."
                    if prefix == "mri" else
                    "Enter whole days. Missing or invalid evidence is assessed by the triage rules."
                ),
            )
            evidence["conservative_therapy_days"] = numeric_evidence(days)
            if prefix == "mri":
                therapy_type = st.selectbox(
                    "Conservative therapy type", ["Unknown", "physiotherapy", "medication"],
                    key="mri_type", on_change=clear_result,
                )
                evidence["conservative_therapy_type"] = None if therapy_type == "Unknown" else therapy_type
            evidence["conservative_therapy_documented"] = answer(
                "Conservative therapy documented", f"{prefix}_documented",
            )
            if prefix == "knee":
                evidence["mri_report_attached"] = st.checkbox(
                    "MRI report attached to the synthetic request", key="mri_report_attached",
                    on_change=clear_result,
                )
                st.caption("Confirm attachment status only. No report is uploaded or interpreted.")
        elif procedure == "CT head":
            hours = st.text_input(
                "Hours since trauma", key="ct_hours", placeholder="e.g. 24, or leave blank if unknown",
                on_change=clear_result, help="The rule accepts 0 to 48 hours inclusive.",
            )
            evidence["trauma_hours"] = numeric_evidence(hours)
            evidence["gcs_documented"] = answer("GCS documented", "gcs_documented")
            st.caption("Documentation status only. No GCS score threshold is applied.")
        else:
            st.caption("Unlisted procedures are referred for clinician review after red flags are checked.")

        request = TriageRequest(procedure=procedure, red_flags=flags, **evidence)
        with st.container(horizontal=True):
            submit = st.button(
                "Run triage", key="submit", type="primary", icon=":material/arrow_forward:",
                width="stretch",
            )
            st.button("Reset", key="reset", icon=":material/restart_alt:", on_click=reset_request)
        if submit:
            st.session_state.last_result = decide(request).to_dict()
            st.session_state.request_updated = False

with result_column:
    with st.container(border=True, key="result_panel"):
        st.subheader("Triage outcome", icon=":material/fact_check:")
        result = st.session_state.last_result
        if result is None:
            st.badge("Awaiting request", icon=":material/pending:", color="gray")
            if st.session_state.request_updated:
                st.info("Request updated. Run triage again to see the current outcome.", icon=":material/edit:")
            else:
                st.info("Complete the request and select Run triage to see the outcome and its reason.", icon=":material/arrow_back:")
            st.caption("Your result will include the applicable rules and any evidence gaps.")
        else:
            if result["status"] == "pending_info" and result["outcome"] is None:
                st.warning("Clarification required", icon=":material/help:")
                st.caption("No final classification has been made.")
            elif result["outcome"] == "Approve":
                st.success("Approve", icon=":material/check_circle:")
                st.caption("The synthetic request meets the applicable payer rule.")
            elif result["outcome"] == "Needs info":
                st.warning("Needs more info", icon=":material/description:")
                st.caption("More or sufficient evidence is needed. This is not a denial.")
            else:
                st.info("Clinician review", icon=":material/stethoscope:")
                st.caption("Referral for clinician review. This is not a denial.")

            if result["rule_ids"]:
                st.caption("APPLICABLE RULES")
                with st.container(horizontal=True):
                    for rule in result["rule_ids"]:
                        st.badge(rule, color="primary")
            st.markdown("**Reason for this result**")
            # Plain text preserves the engine explanation, including unlisted
            # procedure text, without interpreting user input as Markdown/HTML.
            st.text(result["explanation"], width="stretch")
            if result["evidence_gaps"]:
                st.markdown("**Information to address**")
                for gap in result["evidence_gaps"]:
                    st.text(gap, width="stretch")

    with st.container(border=True):
        st.markdown("**The rules at a glance**")
        st.caption("A transparent path from evidence to outcome.")
        with st.expander("Procedure requirements", expanded=True, icon=":material/menu_book:"):
            st.markdown("**R1 · MRI lumbar spine**  \nAt least 42 days of documented physiotherapy or medication. Missing duration keeps evaluation pending.")
            st.markdown("**R3 · CT head**  \nTrauma within 0-48 hours, inclusive, and GCS documented.")
            st.markdown("**R4 · Knee arthroscopy**  \nAt least 84 days of documented conservative therapy and an attached MRI report.")
            st.caption("Approval also requires all red flags to be absent.")
        st.markdown("**R2** · Red flags take priority.  \n**R5** · Unlisted procedures go to a clinician.  \n**R6** · The demo never automatically denies.")

st.caption("SYNTHETIC DATA ONLY  ·  No patient records  ·  No automatic denial  ·  Clinical decisions remain with clinicians")
