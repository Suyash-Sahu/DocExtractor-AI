"""
Production document processing pipeline.

This module connects all components of the
Document Data Extractor into one reusable workflow.

Pipeline:

    File
      ↓
    Text Extraction
      ↓
    Classification
      ↓
    LLM Extraction
      ↓
    Pydantic Validation
      ↓
    Deterministic Validation
      ↓
    Confidence / Status Decision
      ↓
    Final Structured Result
"""

from extractor.file_utils import extract_text
from extractor.classifier import classify_document
from extractor.llm_extract import extract_fields
from extractor.schema import ExtractedDocument
from extractor.validators import run_validation
from extractor.status import build_validation_decision


def process_document(
    file_path: str,
) -> dict:
    """
    Process one document through the complete
    extraction and validation pipeline.

    Args:
        file_path:
            Path to PDF, image, or text document.

    Returns:
        Final structured dictionary containing:
        - extracted document fields
        - validation checks
        - confidence
        - status
        - review reasons
    """

    # ========================================================
    # Step 1 — Extract text
    # ========================================================

    text = extract_text(file_path)

    if not text or not text.strip():
        raise ValueError(
            "No text could be extracted from the document."
        )

    # ========================================================
    # Step 2 — Classify document
    # ========================================================

    classification = classify_document(text)

    document_type = (
        classification.document_type
    )

    # ========================================================
    # Step 3 — LLM extraction
    # ========================================================

    fields = extract_fields(
        text=text,
        doc_type=document_type,
    )

    # ========================================================
    # Step 4 — Pydantic validation
    # ========================================================

    document = ExtractedDocument(
        **fields
    )

    # ========================================================
    # Step 5 — Deterministic validation
    # ========================================================

    validation = run_validation(
        document=document,
        document_dict=fields,
    )

    # ========================================================
    # Step 6 — Confidence / status decision
    # ========================================================

    decision = build_validation_decision(
        validation
    )

    # ========================================================
    # Step 7 — Build final JSON
    # ========================================================

    result = document.model_dump(
        mode="json"
    )

    result["validation"] = {
        # ----------------------------------------------------
        # Decision
        # ----------------------------------------------------

        "status": decision[
            "status"
        ],

        "is_valid": decision[
            "is_valid"
        ],

        "confidence": decision[
            "confidence"
        ],

        "confidence_level": decision[
            "confidence_level"
        ],

        "reasons": decision[
            "reasons"
        ],

        # ----------------------------------------------------
        # Validation
        # ----------------------------------------------------

        "checks": validation[
            "checks"
        ],

        "missing_fields": validation[
            "missing_fields"
        ],

        "failed_checks": validation[
            "failed_checks"
        ],

        "warnings": validation[
            "warnings"
        ],

        # ----------------------------------------------------
        # Detailed evidence
        # ----------------------------------------------------

        "details": {
            "line_items": validation[
                "line_items"
            ],

            "subtotal": validation[
                "subtotal"
            ],

            "total": validation[
                "total"
            ],

            "dates": validation[
                "dates"
            ],
        },
    }

    # ========================================================
    # Metadata
    # ========================================================

    result["metadata"] = {
        "source_file": file_path,
        "document_type": document_type,
        "classification_confidence": (
            classification.confidence
        ),
    }

    return result