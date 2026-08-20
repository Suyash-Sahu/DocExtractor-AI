import pytest
from extractor.file_utils import has_extractable_text

from extractor.file_utils import (
    detect_file_type,
    extract_text,
)


def test_detect_pdf():
    assert detect_file_type(
        "samples/invoice_layout_a.pdf"
    ) == "pdf"


def test_detect_text():
    assert detect_file_type(
        "samples/test_document.txt"
    ) == "text"


def test_extract_invoice_pdf():
    text = extract_text(
        "samples/invoice_layout_a.pdf"
    )

    assert "ABC Technologies" in text
    assert "INV-2026-001" in text
    assert "132160" in text


def test_extract_receipt_pdf():
    text = extract_text(
        "samples/receipt_layout_a.pdf"
    )

    assert "TECH MART" in text
    assert "RC-2026-091" in text
    assert "2596" in text


def test_unsupported_file(tmp_path):
    unsupported_file = tmp_path / "sample.exe"
    unsupported_file.write_text("test content")

    with pytest.raises(ValueError):
        detect_file_type(str(unsupported_file))


def test_missing_file():
    with pytest.raises(FileNotFoundError):
        detect_file_type(
            "this_file_does_not_exist.pdf"
        )

def test_text_quality():
    assert has_extractable_text(
        "This is a valid document containing enough text."
    )


def test_empty_text():
    assert not has_extractable_text("")


def test_short_text():
    assert not has_extractable_text("hello")

def test_extract_image():
    text = extract_text(
        "samples/receipt_ocr.png"
    )

    assert "TECH MART" in text
    assert "OCR-2026-001" in text
    assert "2596" in text

def test_extract_scanned_pdf():
    text = extract_text(
        "samples/receipt_scanned.pdf"
    )

    assert "TECH MART" in text
    assert "OCR-2026-001" in text
    assert "2596" in text