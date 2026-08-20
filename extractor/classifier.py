"""
Deterministic document classifier.

The classifier uses document-specific keywords instead of an LLM.
This keeps classification fast, cheap and explainable.
"""

from dataclasses import dataclass


@dataclass
class ClassificationResult:
    document_type: str
    confidence: float
    matched_keywords: list[str]


INVOICE_KEYWORDS = [
    "invoice",
    "tax invoice",
    "invoice no",
    "invoice number",
    "invoice #",
    "gstin",
    "bill to",
    "due date",
    "taxable value",
    "amount payable",
    "cgst",
    "sgst",
]


RECEIPT_KEYWORDS = [
    "receipt",
    "retail receipt",
    "receipt no",
    "receipt number",
]


def classify_document(text: str) -> ClassificationResult:
    """
    Classify raw document text as invoice, receipt,
    or unsupported.
    """

    if not text or not text.strip():
        raise ValueError(
            "Cannot classify empty document text."
        )

    normalized_text = " ".join(
        text.lower().split()
    )

    invoice_matches = [
        keyword
        for keyword in INVOICE_KEYWORDS
        if keyword in normalized_text
    ]

    receipt_matches = [
        keyword
        for keyword in RECEIPT_KEYWORDS
        if keyword in normalized_text
    ]

    invoice_score = len(invoice_matches)
    receipt_score = len(receipt_matches)

    if invoice_score == 0 and receipt_score == 0:
        return ClassificationResult(
            document_type="unsupported",
            confidence=0.0,
            matched_keywords=[],
        )

    # Strong explicit document labels get priority.
    has_invoice_label = (
        "invoice" in normalized_text
        or "tax invoice" in normalized_text
    )

    has_receipt_label = (
        "receipt" in normalized_text
        or "retail receipt" in normalized_text
    )

    if has_invoice_label and not has_receipt_label:
        return ClassificationResult(
            document_type="invoice",
            confidence=1.0,
            matched_keywords=invoice_matches,
        )

    if has_receipt_label and not has_invoice_label:
        return ClassificationResult(
            document_type="receipt",
            confidence=1.0,
            matched_keywords=receipt_matches,
        )

    if invoice_score > receipt_score:
        confidence = invoice_score / (
            invoice_score + receipt_score
        )

        return ClassificationResult(
            document_type="invoice",
            confidence=round(confidence, 2),
            matched_keywords=invoice_matches,
        )

    if receipt_score > invoice_score:
        confidence = receipt_score / (
            invoice_score + receipt_score
        )

        return ClassificationResult(
            document_type="receipt",
            confidence=round(confidence, 2),
            matched_keywords=receipt_matches,
        )

    return ClassificationResult(
        document_type="unsupported",
        confidence=0.0,
        matched_keywords=[],
    )