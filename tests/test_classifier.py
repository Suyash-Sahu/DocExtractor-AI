from extractor.classifier import classify_document
from extractor.file_utils import extract_text


def test_invoice_layout_a_classification():
    text = extract_text(
        "samples/invoice_layout_a.pdf"
    )

    result = classify_document(text)

    assert result.document_type == "invoice"
    assert result.confidence > 0


def test_invoice_layout_b_classification():
    text = extract_text(
        "samples/invoice_layout_b.pdf"
    )

    result = classify_document(text)

    assert result.document_type == "invoice"
    assert result.confidence > 0


def test_receipt_classification():
    text = extract_text(
        "samples/receipt_layout_a.pdf"
    )

    result = classify_document(text)

    assert result.document_type == "receipt"
    assert result.confidence > 0


def test_unknown_document():
    text = """
    Employee attendance report.
    Department: Computer Science.
    Total employees: 42.
    """

    result = classify_document(text)

    assert result.document_type == "unsupported"
    assert result.confidence == 0.0


def test_empty_document():
    import pytest

    with pytest.raises(ValueError):
        classify_document("")