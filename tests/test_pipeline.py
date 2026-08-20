from pathlib import Path

from extractor.pipeline import process_document


def test_invoice_pipeline():

    file_path = (
        "samples/invoice_layout_a.pdf"
    )

    result = process_document(
        file_path
    )

    assert result["document_type"] == "invoice"

    assert (
        result["document_id"]
        == "INV-2026-001"
    )

    assert (
        result["validation"]["status"]
        == "ACCEPTED"
    )

    assert (
        result["validation"]["is_valid"]
        is True
    )

    assert (
        result["validation"][
            "confidence_level"
        ]
        == "HIGH"
    )


def test_receipt_pipeline():

    file_path = (
        "samples/receipt_layout_a.pdf"
    )

    result = process_document(
        file_path
    )

    assert result["document_type"] == "receipt"

    assert (
        result["document_id"]
        == "RC-2026-091"
    )

    assert (
        result["validation"]["status"]
        == "ACCEPTED"
    )


def test_pipeline_contains_metadata():

    file_path = (
        "samples/invoice_layout_b.pdf"
    )

    result = process_document(
        file_path
    )

    assert "metadata" in result

    assert (
        result["metadata"][
            "document_type"
        ]
        == "invoice"
    )

    assert (
        result["metadata"][
            "classification_confidence"
        ]
        == 1.0
    )