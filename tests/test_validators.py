import pytest

from extractor.schema import (
    ExtractedDocument,
    LineItem,
    Party,
)

from extractor.validators import (
    validate_line_items,
    validate_subtotal,
    validate_total,
    validate_dates,
    validate_required_fields,
)


def create_invoice():

    return ExtractedDocument(
        document_type="invoice",
        document_id="TEST-001",

        vendor=Party(
            name="Test Vendor",
            address=None,
            tax_id=None,
        ),

        customer=None,

        invoice_date="2026-08-19",
        due_date="2026-09-18",

        currency="INR",

        line_items=[
            LineItem(
                description="Laptop",
                quantity=2,
                unit_price=50000,
                tax_rate=18,
                amount=100000,
            ),
            LineItem(
                description="Mouse",
                quantity=2,
                unit_price=1000,
                tax_rate=18,
                amount=2000,
            ),
        ],

        subtotal=102000,
        tax_amount=18360,
        discount=None,
        total=120360,

        payment_status=None,
        payment_method=None,
    )


# ============================================================
# Test 1
# ============================================================

def test_line_items_valid():

    document = create_invoice()

    result = validate_line_items(
        document.line_items
    )

    assert result["passed"] is True


# ============================================================
# Test 2
# ============================================================

def test_line_items_invalid():

    document = create_invoice()

    document.line_items[0].amount = 90000

    result = validate_line_items(
        document.line_items
    )

    assert result["passed"] is False


# ============================================================
# Test 3
# ============================================================

def test_subtotal_valid():

    document = create_invoice()

    result = validate_subtotal(
        document.line_items,
        document.subtotal,
    )

    assert result["passed"] is True


# ============================================================
# Test 4
# ============================================================

def test_total_valid():

    document = create_invoice()

    result = validate_total(
        document.subtotal,
        document.tax_amount,
        document.discount,
        document.total,
    )

    assert result["passed"] is True


# ============================================================
# Test 5
# ============================================================

def test_total_invalid():

    document = create_invoice()

    result = validate_total(
        document.subtotal,
        document.tax_amount,
        document.discount,
        999999,
    )

    assert result["passed"] is False


# ============================================================
# Test 6
# ============================================================

def test_invalid_date_order():

    result = validate_dates(
        "2026-08-19",
        "2026-08-18",
    )

    assert result["passed"] is False

    assert (
        "Due date occurs before invoice date."
        in result["warnings"]
    )


# ============================================================
# Test 7
# ============================================================

def test_valid_dates():

    result = validate_dates(
        "2026-08-19",
        "2026-09-18",
    )

    assert result["passed"] is True


# ============================================================
# Test 8
# ============================================================

def test_required_fields():

    document = create_invoice()

    data = document.model_dump()

    missing = validate_required_fields(
        data,
        "invoice",
    )

    assert missing == []