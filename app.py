"""
Document Data Extractor
=======================
Streamlit frontend for the Document Data Extractor backend.

Pipeline: Upload -> Text Extraction -> Classification -> LLM Extraction
          -> Pydantic Validation -> Deterministic Verification
          -> Confidence -> Final Decision
"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path
from typing import Any

import streamlit as st

from extractor.pipeline import process_document

# ============================================================
# Config
# ============================================================

SUPPORTED_FILE_TYPES = ["pdf", "txt", "png", "jpg", "jpeg"]

STATUS_ACCEPTED = "ACCEPTED"
STATUS_REVIEW = "REVIEW_REQUIRED"

CHECK_LABELS = {
    "line_items": "Line Item Arithmetic",
    "subtotal": "Subtotal",
    "total_matches": "Total Calculation",
    "dates": "Date Validation",
}

PIPELINE_STEPS = [
    ("01", "Upload", "Provide an invoice or receipt."),
    ("02", "Extract", "LLM identifies structured fields."),
    ("03", "Validate", "Pydantic checks the schema."),
    ("04", "Verify", "Python checks the calculations."),
    ("05", "Decide", "Accept or flag for review."),
]

SIDEBAR_PIPELINE_STEPS = [
    "Text Extraction",
    "Classification",
    "LLM Extraction",
    "Schema Validation",
    "Arithmetic Verification",
    "Confidence",
    "Final Decision",
]

RUN_STEPS = [
    "Extracting text",
    "Classifying document",
    "Extracting structured fields",
    "Validating schema",
    "Running deterministic verification",
    "Calculating confidence",
]


# ============================================================
# Page setup + CSS
# ============================================================

def configure_page() -> None:
    st.set_page_config(
        page_title="Document Data Extractor",
        page_icon="📄",
        layout="wide",
        initial_sidebar_state="expanded",
    )


def inject_css() -> None:
    # NOTE: every HTML string below is flush-left. Indenting these lines
    # (even inside the triple-quote) makes Markdown treat them as a
    # code block instead of HTML - that was the original rendering bug.
    st.markdown("""
<style>
.stApp { background-color: #F4F7F9; color: #17324D; }
.main .block-container { max-width: 1250px; padding-top: 2rem; padding-bottom: 3rem; }
h1, h2, h3, h4 { color: #17324D !important; }
p { color: #52677D; }

section[data-testid="stSidebar"] { background-color: #EAF0F4; border-right: 1px solid #D3DEE6; }
section[data-testid="stSidebar"] .block-container { padding-top: 2rem; }
section[data-testid="stSidebar"] h2, section[data-testid="stSidebar"] h3 { color: #17324D !important; }
section[data-testid="stSidebar"] p, section[data-testid="stSidebar"] span { color: #52677D !important; }

.hero {
background: #FFFFFF; border: 1px solid #D7E1E8; border-radius: 14px;
padding: 2rem 2.2rem; margin-bottom: 2rem; box-shadow: 0 2px 8px rgba(23,50,77,0.06);
}
.hero h1 { margin: 0; font-size: 2rem; }
.hero p { margin-top: 0.45rem; color: #687D8F; }
.pipeline {
margin-top: 1rem; display: inline-block; padding: 0.5rem 0.8rem;
border-radius: 7px; background: #EDF4F5; color: #286B62; font-weight: 700; font-size: 0.8rem;
}

.info-card {
background: #FFFFFF; border: 1px solid #D7E1E8; border-radius: 10px;
padding: 1rem; height: 100%;
}
.step-num { color: #7A8A99; font-size: 0.7rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em; }
.step-title { color: #17324D; font-weight: 700; margin-top: 8px; }
.step-desc { color: #718395; font-size: 0.75rem; margin-top: 5px; }

[data-testid="stFileUploader"] { background: #FFFFFF; border: 1px solid #D7E1E8; border-radius: 10px; padding: 0.5rem; }
[data-testid="stFileUploaderDropzone"] { background: #F8FAFB !important; border: 1px dashed #B7C9D5 !important; border-radius: 8px !important; }

.stButton > button { border-radius: 7px; font-weight: 600; border: 1px solid #C7D5DE; }
.stButton > button[kind="primary"] { background-color: #17324D !important; color: white !important; border-color: #17324D !important; }
.stButton > button[kind="primary"]:hover { background-color: #294C68 !important; }

[data-testid="stMetric"] { background: #FFFFFF; border: 1px solid #D7E1E8; border-radius: 9px; padding: 0.8rem; }
[data-testid="stMetricLabel"] { color: #718395 !important; }
[data-testid="stMetricValue"] { color: #17324D !important; }

[data-testid="stDataFrame"] { border: 1px solid #D7E1E8; border-radius: 8px; }

.status-box { border-radius: 9px; padding: 0.9rem 1rem; font-weight: 700; }
.status-accepted { background: #EDF6F2; border: 1px solid #C8E0D6; color: #286B62; }
.status-review { background: #FBF5E9; border: 1px solid #E7D8B5; color: #80652E; }

.footer { text-align: center; margin-top: 3rem; color: #8A9AA8; font-size: 0.72rem; }
</style>
""", unsafe_allow_html=True)


# ============================================================
# Helpers
# ============================================================

def fmt_currency(value: Any) -> str:
    if value is None:
        return "N/A"
    try:
        return f"{float(value):,.2f}"
    except (TypeError, ValueError):
        return "N/A"


def fmt_pct(value: Any) -> str:
    if value is None:
        return "N/A"
    try:
        return f"{float(value) * 100:.0f}%"
    except (TypeError, ValueError):
        return "N/A"


def as_dict(value: Any) -> dict:
    return value if isinstance(value, dict) else {}


# ============================================================
# Sidebar
# ============================================================

def render_sidebar() -> None:
    with st.sidebar:
        st.markdown("## ⚙ System")
        st.success("● Backend Ready")
        st.caption("Document processing pipeline is available.")
        st.divider()

        st.markdown("### LLM Strategy")
        st.caption("PRIMARY"); st.write("OpenRouter")
        st.caption("FALLBACK"); st.write("Local Ollama")
        st.caption("VERIFICATION"); st.write("Deterministic Python")
        st.divider()

        st.markdown("### Supported Documents")
        cols = st.columns(3)
        for i, ext in enumerate(SUPPORTED_FILE_TYPES):
            cols[i % 3].caption(ext.upper())
        st.divider()

        st.markdown("### Processing Pipeline")
        for i, step in enumerate(SIDEBAR_PIPELINE_STEPS, start=1):
            st.write(f"**{i:02d}**  {step}")


# ============================================================
# Hero
# ============================================================

def render_hero() -> None:
    st.markdown("""
<div class="hero">
<h1>📄 Document Data Extractor</h1>
<p>Intelligent invoice & receipt processing</p>
<div class="pipeline">Extract → Structure → Validate → Verify → Decide</div>
</div>
""", unsafe_allow_html=True)


# ============================================================
# Upload + pipeline run
# ============================================================

def save_upload_to_tempfile(uploaded_file) -> Path:
    suffix = Path(uploaded_file.name).suffix
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(uploaded_file.getbuffer())
        return Path(tmp.name)


def run_pipeline(uploaded_file) -> dict | None:
    temp_path = None
    try:
        temp_path = save_upload_to_tempfile(uploaded_file)

        with st.status("Processing document...", expanded=True) as status:
            for step in RUN_STEPS:
                st.write(f"• {step}...")
            result = process_document(str(temp_path))
            status.update(label="Processing complete", state="complete", expanded=False)

        return result

    except Exception as exc:
        st.error("Document processing failed.")
        st.exception(exc)
        return None

    finally:
        if temp_path:
            temp_path.unlink(missing_ok=True)


def render_upload() -> None:
    st.markdown("## 📤 Upload Document")
    st.caption("Upload an invoice or receipt to extract, validate and verify its structured data.")

    uploaded_file = st.file_uploader(
        "Choose a document",
        type=SUPPORTED_FILE_TYPES,
        help="PDF, TXT, PNG, JPG or JPEG.",
    )

    if uploaded_file is None:
        return

    st.info(f"Selected file: **{uploaded_file.name}** • {uploaded_file.size / 1024:.2f} KB")

    if st.button("Process Document", type="primary", use_container_width=True):
        result = run_pipeline(uploaded_file)
        if result is not None:
            st.session_state["processing_result"] = result
            st.session_state["processed_filename"] = uploaded_file.name
            st.rerun()


# ============================================================
# How it works
# ============================================================

def render_workflow() -> None:
    st.markdown("## How the system works")
    st.caption("The system combines AI extraction with independent deterministic verification.")

    columns = st.columns(5)
    for column, (number, title, description) in zip(columns, PIPELINE_STEPS):
        with column:
            st.markdown(f"""
<div class="info-card">
<div class="step-num">{number}</div>
<div class="step-title">{title}</div>
<div class="step-desc">{description}</div>
</div>
""", unsafe_allow_html=True)

    st.info("The AI extracts the information. Python independently verifies the numbers.")


# ============================================================
# Result sections
# ============================================================

def render_status(status: str, confidence: float | None) -> None:
    confidence_text = f" — Confidence: {fmt_pct(confidence)}" if confidence is not None else ""

    if status == STATUS_ACCEPTED:
        st.markdown(f"""
<div class="status-box status-accepted">✓ DOCUMENT ACCEPTED{confidence_text}</div>
""", unsafe_allow_html=True)
    elif status == STATUS_REVIEW:
        st.markdown(f"""
<div class="status-box status-review">! HUMAN REVIEW REQUIRED{confidence_text}</div>
""", unsafe_allow_html=True)
    else:
        st.error(f"Status: {status}")


def render_summary(result: dict, validation: dict) -> None:
    confidence = validation.get("confidence")
    level = validation.get("confidence_level", "UNKNOWN")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Document Type", str(result.get("document_type", "unknown")).upper())
    c2.metric("Document ID", result.get("document_id") or "Not available")
    c3.metric("Confidence", fmt_pct(confidence))
    c4.metric("Confidence Level", level)


def render_party(title: str, party: Any) -> None:
    st.markdown(f"### {title}")
    party = as_dict(party)
    if not party:
        st.caption("Not available")
        return
    st.write(party.get("name") or "Not available")
    if party.get("address"):
        st.caption(party["address"])
    if party.get("tax_id"):
        st.caption(f"Tax ID: {party['tax_id']}")


def render_extracted_info(result: dict) -> None:
    st.markdown("## 📋 Extracted Information")
    left, right = st.columns(2)

    with left:
        render_party("Vendor", result.get("vendor"))
        render_party("Customer", result.get("customer"))

    with right:
        st.markdown("### Dates")
        st.write(f"**Invoice Date:** {result.get('invoice_date') or 'Not available'}")
        st.write(f"**Due Date:** {result.get('due_date') or 'Not available'}")

        st.markdown("### Payment")
        st.write(f"**Status:** {result.get('payment_status') or 'Not available'}")
        st.write(f"**Method:** {result.get('payment_method') or 'Not available'}")


def render_financial_summary(result: dict) -> None:
    st.markdown("## 💰 Financial Summary")

    values = [
        ("Currency", result.get("currency") or "N/A"),
        ("Subtotal", fmt_currency(result.get("subtotal"))),
        ("Tax", fmt_currency(result.get("tax_amount"))),
        ("Discount", fmt_currency(result.get("discount"))),
        ("Total", fmt_currency(result.get("total"))),
    ]

    columns = st.columns(len(values))
    for column, (label, value) in zip(columns, values):
        column.metric(label, value)


def render_line_items(result: dict) -> None:
    st.markdown("## 🧾 Line Items")
    items = result.get("line_items") or []

    if not items:
        st.info("No line items extracted.")
        return

    table = [
        {
            "#": i,
            "Description": item.get("description"),
            "Quantity": item.get("quantity"),
            "Unit Price": item.get("unit_price"),
            "Tax Rate": item.get("tax_rate"),
            "Amount": item.get("amount"),
        }
        for i, item in enumerate(items, start=1)
    ]

    st.dataframe(table, use_container_width=True, hide_index=True)


def render_check(label: str, value: bool | None) -> None:
    if value is True:
        st.success(f"✓ {label}: PASSED")
    elif value is False:
        st.error(f"✗ {label}: FAILED")
    else:
        st.info(f"○ {label}: NOT APPLICABLE")


def render_verification(validation: dict) -> None:
    st.markdown("## 🧮 Independent Verification")
    st.caption("These checks are performed by deterministic Python logic — not by the LLM.")

    checks = validation.get("checks", {})
    columns = st.columns(2)
    for i, (key, label) in enumerate(CHECK_LABELS.items()):
        with columns[i % 2]:
            render_check(label, checks.get(key))


def render_validation_details(validation: dict) -> None:
    details = validation.get("details", {})

    with st.expander("🔍 View Validation Details"):
        line_details = details.get("line_items", {})
        st.markdown("### Line Item Arithmetic")
        st.write("Calculated line-item sum:", line_details.get("calculated_sum", "N/A"))
        if line_details.get("items"):
            st.dataframe(line_details["items"], use_container_width=True, hide_index=True)

        subtotal_details = details.get("subtotal", {})
        st.markdown("### Subtotal Check")
        st.write(subtotal_details.get("message", "No information."))

        total_details = details.get("total", {})
        st.markdown("### Total Check")
        st.write(total_details.get("message", "No information."))

        if total_details.get("calculated_total") is not None:
            st.write("Calculated total:", fmt_currency(total_details.get("calculated_total")))
            st.write("Extracted total:", fmt_currency(total_details.get("extracted_total")))
            st.write("Difference:", fmt_currency(total_details.get("difference")))

        date_details = details.get("dates", {})
        st.markdown("### Date Validation")
        warnings = date_details.get("warnings", [])
        if warnings:
            for warning in warnings:
                st.warning(warning)
        else:
            st.caption("No date validation warnings.")


def render_warnings(validation: dict) -> None:
    reasons = validation.get("reasons", [])
    warnings = validation.get("warnings", [])

    if not reasons and not warnings:
        return

    st.markdown("## ⚠️ Warnings & Review Information")
    for reason in reasons:
        st.warning(reason)
    for warning in warnings:
        st.info(warning)


def render_json(result: dict, filename: str) -> None:
    st.markdown("## 📦 Structured JSON")

    with st.expander("View extracted JSON"):
        st.json(result)

    json_data = json.dumps(result, indent=2, ensure_ascii=False, default=str)
    st.download_button(
        "Download JSON",
        data=json_data,
        file_name=f"{Path(filename).stem}.json",
        mime="application/json",
        use_container_width=True,
    )


def render_result(result: dict, filename: str) -> None:
    validation = result.get("validation", {})
    status = validation.get("status", "UNKNOWN")
    confidence = validation.get("confidence")

    st.divider()
    st.markdown("## 📊 Processing Result")
    render_status(status, confidence)
    st.write("")

    render_summary(result, validation)
    st.divider()

    render_extracted_info(result)
    st.divider()

    render_financial_summary(result)
    st.divider()

    render_line_items(result)
    st.divider()

    render_verification(validation)
    render_validation_details(validation)
    render_warnings(validation)
    st.divider()

    render_json(result, filename)


# ============================================================
# Footer
# ============================================================

def render_footer() -> None:
    st.markdown("""
<div class="footer">Document Data Extractor &nbsp;•&nbsp; AI Extraction &nbsp;•&nbsp; Deterministic Verification</div>
""", unsafe_allow_html=True)


# ============================================================
# Main
# ============================================================

def main() -> None:
    configure_page()
    inject_css()
    render_sidebar()
    render_hero()
    render_upload()

    if "processing_result" in st.session_state:
        render_result(
            st.session_state["processing_result"],
            st.session_state.get("processed_filename", "document"),
        )
    else:
        render_workflow()

    render_footer()


if __name__ == "__main__":
    main()