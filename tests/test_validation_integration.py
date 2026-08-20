from extractor.schema import (
    ExtractedDocument,
    LineItem,
    Party,
)

from extractor.validators import run_validation


def test_wrong_total_requires_review():

    document = ExtractedDocument(

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
            )
        ],

        subtotal=100000,

        tax_amount=18000,

        discount=None,

        # Deliberately WRONG
        total=999999,

        payment_status=None,

        payment_method=None,
    )

    data = document.model_dump()

    validation = run_validation(
        document,
        data,
    )

    assert validation["is_valid"] is False

    assert (
        "total_matches"
        in validation["failed_checks"]
    )