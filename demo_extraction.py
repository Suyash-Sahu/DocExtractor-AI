"""
Demo runner for the Document Data Extractor.

Pipeline:

    Document
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
    Confidence & Status Decision
        ↓
    Final JSON
"""

import json
from pathlib import Path

from extractor.file_utils import extract_text
from extractor.classifier import classify_document
from extractor.llm_extract import extract_fields
from extractor.schema import ExtractedDocument
from extractor.validators import run_validation
from extractor.status import build_validation_decision


# ============================================================
# Configuration
# ============================================================

SAMPLE_FILES = [
    "samples/invoice_layout_a.pdf",
    "samples/invoice_layout_b.pdf",
    "samples/receipt_layout_a.pdf",
]


# ============================================================
# Process One Document
# ============================================================

def process_demo_file(file_path: str):
    """
    Process a single document through the complete
    Document Data Extractor pipeline.
    """

    print("\n" + "=" * 80)
    print(f"FILE: {file_path}")
    print("=" * 80)

    # ========================================================
    # Step 1 — Text Extraction
    # ========================================================

    print("\n[1] Extracting text...")

    text = extract_text(file_path)

    if not text or not text.strip():
        print("ERROR: No text could be extracted.")
        return None

    print(
        f"Extracted characters: {len(text)}"
    )

    # ========================================================
    # Step 2 — Document Classification
    # ========================================================

    print("\n[2] Classifying document...")

    classification = classify_document(text)

    print(
        f"Document type : "
        f"{classification.document_type}"
    )

    print(
        f"Confidence    : "
        f"{classification.confidence}"
    )

    # ========================================================
    # Step 3 — LLM Field Extraction
    # ========================================================

    print(
        "\n[3] Extracting structured fields "
        "with OpenRouter / Ollama..."
    )

    try:

        fields = extract_fields(
            text=text,
            doc_type=classification.document_type,
        )

    except Exception as exc:

        print(
            "\nLLM extraction FAILED:"
        )

        print(exc)

        return None

    # ========================================================
    # Step 4 — Pydantic Schema Validation
    # ========================================================

    print(
        "\n[4] Validating against "
        "Pydantic schema..."
    )

    try:

        document = ExtractedDocument(
            **fields
        )

    except Exception as exc:

        print(
            "\nPydantic validation FAILED:"
        )

        print(exc)

        return None

    print(
        "Pydantic validation: PASSED"
    )

    # ========================================================
    # Step 5 — Deterministic Validation
    # ========================================================

    print(
        "\n[5] Running deterministic "
        "sanity checks..."
    )

    try:

        validation = run_validation(
            document=document,
            document_dict=fields,
        )

    except Exception as exc:

        print(
            "\nDeterministic validation FAILED:"
        )

        print(exc)

        return None

    # ========================================================
    # Step 6 — Confidence & Status Decision
    # ========================================================

    validation_decision = (
        build_validation_decision(
            validation
        )
    )

    # ========================================================
    # Display Validation Results
    # ========================================================

    print(
        "\nValidation results:"
    )

    print(
        f"  Line items : "
        f"{validation['checks']['line_items']}"
    )

    print(
        f"  Subtotal   : "
        f"{validation['checks']['subtotal']}"
    )

    print(
        f"  Total      : "
        f"{validation['checks']['total_matches']}"
    )

    print(
        f"  Dates      : "
        f"{validation['checks']['dates']}"
    )

    # ========================================================
    # Display Decision
    # ========================================================

    print(
        "\nDecision:"
    )

    print(
        f"  Status           : "
        f"{validation_decision['status']}"
    )

    print(
        f"  Confidence       : "
        f"{validation_decision['confidence']}"
    )

    print(
        f"  Confidence Level : "
        f"{validation_decision['confidence_level']}"
    )

    # --------------------------------------------------------
    # Review Reasons
    # --------------------------------------------------------

    if validation_decision["reasons"]:

        print(
            "\nReview Reasons:"
        )

        for reason in validation_decision[
            "reasons"
        ]:

            print(
                f"  - {reason}"
            )

    # --------------------------------------------------------
    # Warnings
    # --------------------------------------------------------

    if validation_decision["warnings"]:

        print(
            "\nWarnings:"
        )

        for warning in validation_decision[
            "warnings"
        ]:

            print(
                f"  - {warning}"
            )

    # ========================================================
    # Build Final Result
    # ========================================================

    # mode="json" converts Python date objects
    # into JSON-compatible strings.

    result = document.model_dump(
        mode="json"
    )

    # Combine Phase 5 validation details
    # with Phase 6 decision information.

    result["validation"] = {
        # ----------------------------------------------------
        # Phase 6 Decision
        # ----------------------------------------------------

        "status": validation_decision[
            "status"
        ],

        "is_valid": validation_decision[
            "is_valid"
        ],

        "confidence": validation_decision[
            "confidence"
        ],

        "confidence_level": (
            validation_decision[
                "confidence_level"
            ]
        ),

        "reasons": validation_decision[
            "reasons"
        ],

        # ----------------------------------------------------
        # Phase 5 Validation
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
        # Detailed Validation Evidence
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
    # Final Output
    # ========================================================

    print(
        "\n[7] FINAL STRUCTURED DATA"
    )

    print("-" * 80)

    print(
        json.dumps(
            result,
            indent=2,
            ensure_ascii=False,
        )
    )

    print("-" * 80)

    print(
        f"STATUS: "
        f"{validation_decision['status']}"
    )

    print(
        f"CONFIDENCE: "
        f"{validation_decision['confidence']}"
    )

    print(
        f"LEVEL: "
        f"{validation_decision['confidence_level']}"
    )

    return result


# ============================================================
# Main
# ============================================================

if __name__ == "__main__":

    print(
        "\n"
        "=" * 80
    )

    print(
        "DOCUMENT DATA EXTRACTOR"
    )

    print(
        "Phase 6 — Confidence & Status Demo"
    )

    print(
        "=" * 80
    )

    successful = 0
    failed = 0

    # --------------------------------------------------------
    # Process all sample documents
    # --------------------------------------------------------

    for file_path in SAMPLE_FILES:

        path = Path(file_path)

        if not path.exists():

            print(
                f"\nWARNING: File not found: "
                f"{file_path}"
            )

            failed += 1

            continue

        try:

            result = process_demo_file(
                file_path
            )

            if result is not None:

                successful += 1

            else:

                failed += 1

        except Exception as exc:

            failed += 1

            print(
                "\nERROR PROCESSING FILE:"
            )

            print(
                f"{type(exc).__name__}: "
                f"{exc}"
            )

    # ========================================================
    # Summary
    # ========================================================

    print(
        "\n" + "=" * 80
        
    )

    print(
        "PROCESSING SUMMARY"
    )

    print(
        "=" * 80
    )

    print(
        f"Successful: {successful}"
    )

    print(
        f"Failed    : {failed}"
    )

    print(
        f"Total     : {len(SAMPLE_FILES)}"
    )

    print(
        "=" * 80
    )