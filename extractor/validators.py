"""
Deterministic validation engine.

The LLM extracts values.
This module independently verifies those values
using deterministic Python logic.

No LLM is used here.
"""

from datetime import date
from typing import Any


# ============================================================
# Configuration
# ============================================================

DEFAULT_TOLERANCE = 1.0


# ============================================================
# Required Fields
# ============================================================

REQUIRED_FIELDS = {
    "invoice": [
        "document_id",
        "vendor",
        "invoice_date",
        "line_items",
        "total",
    ],

    "receipt": [
        "vendor",
        "invoice_date",
        "line_items",
        "total",
    ],
}


# ============================================================
# Line Item Validation
# ============================================================

def validate_line_items(
    line_items: list,
    tolerance: float = DEFAULT_TOLERANCE,
) -> dict[str, Any]:
    """
    Verify that each line item's quantity × unit price
    matches its extracted amount.

    Example:

        quantity = 2
        unit_price = 1000
        amount = 2000

        2 × 1000 = 2000 → PASS
    """

    results = []

    if not line_items:
        return {
            "passed": False,
            "calculated_sum": 0.0,
            "items": [],
            "message": "No line items found.",
        }

    calculated_sum = 0.0

    for index, item in enumerate(line_items):

        quantity = item.quantity
        unit_price = item.unit_price
        amount = item.amount

        calculated_amount = (
            quantity * unit_price
        )

        difference = abs(
            calculated_amount - amount
        )

        passed = difference <= tolerance

        calculated_sum += amount

        results.append(
            {
                "line": index + 1,
                "description": item.description,
                "calculated_amount": round(
                    calculated_amount,
                    2,
                ),
                "extracted_amount": round(
                    amount,
                    2,
                ),
                "difference": round(
                    difference,
                    2,
                ),
                "passed": passed,
            }
        )

    return {
        "passed": all(
            item["passed"]
            for item in results
        ),
        "calculated_sum": round(
            calculated_sum,
            2,
        ),
        "items": results,
        "message": (
            "All line items passed arithmetic validation."
            if all(item["passed"] for item in results)
            else "One or more line items failed arithmetic validation."
        ),
    }


# ============================================================
# Subtotal Validation
# ============================================================

def validate_subtotal(
    line_items: list,
    subtotal: float | None,
    tolerance: float = DEFAULT_TOLERANCE,
) -> dict[str, Any]:
    """
    Verify that the sum of line-item amounts matches
    the extracted subtotal.
    """

    if subtotal is None:
        return {
            "passed": None,
            "calculated_subtotal": None,
            "extracted_subtotal": None,
            "difference": None,
            "message": "Subtotal not provided.",
        }

    calculated_subtotal = sum(
        item.amount
        for item in line_items
    )

    difference = abs(
        calculated_subtotal - subtotal
    )

    passed = difference <= tolerance

    return {
        "passed": passed,
        "calculated_subtotal": round(
            calculated_subtotal,
            2,
        ),
        "extracted_subtotal": round(
            subtotal,
            2,
        ),
        "difference": round(
            difference,
            2,
        ),
        "message": (
            "Subtotal matches line-item sum."
            if passed
            else "Subtotal does not match line-item sum."
        ),
    }


# ============================================================
# Total Validation
# ============================================================

def validate_total(
    subtotal: float | None,
    tax_amount: float | None,
    discount: float | None,
    total: float,
    tolerance: float = DEFAULT_TOLERANCE,
) -> dict[str, Any]:
    """
    Verify:

        subtotal + tax - discount = total
    """

    if subtotal is None:
        return {
            "passed": None,
            "calculated_total": None,
            "extracted_total": total,
            "difference": None,
            "message": "Subtotal unavailable; total check skipped.",
        }

    tax = (
        tax_amount
        if tax_amount is not None
        else 0.0
    )

    discount_value = (
        discount
        if discount is not None
        else 0.0
    )

    calculated_total = (
        subtotal
        + tax
        - discount_value
    )

    difference = abs(
        calculated_total - total
    )

    passed = difference <= tolerance

    return {
        "passed": passed,
        "calculated_total": round(
            calculated_total,
            2,
        ),
        "extracted_total": round(
            total,
            2,
        ),
        "difference": round(
            difference,
            2,
        ),
        "message": (
            "Total matches subtotal + tax - discount."
            if passed
            else "Total does not match subtotal + tax - discount."
        ),
    }


# ============================================================
# Date Validation
# ============================================================

def validate_dates(
    invoice_date,
    due_date,
) -> dict[str, Any]:
    """
    Validate invoice and due dates.

    Supports both:
    - Python datetime.date objects from Pydantic
    - ISO date strings such as "2026-08-19"

    Rules:
    - invoice_date must be valid
    - due_date is optional
    - due_date cannot be before invoice_date
    """

    warnings = []

    # --------------------------------------------------------
    # Validate invoice date
    # --------------------------------------------------------

    if invoice_date is None:

        return {
            "passed": False,
            "invoice_date_valid": False,
            "due_date_valid": None,
            "warnings": [
                "Invoice date is missing."
            ],
        }

    try:

        # Pydantic normally gives us datetime.date.
        if isinstance(invoice_date, date):

            invoice_date_obj = invoice_date

        # Also support raw string input.
        elif isinstance(invoice_date, str):

            invoice_date_obj = date.fromisoformat(
                invoice_date
            )

        else:

            raise TypeError(
                "Unsupported invoice_date type"
            )

    except (
        ValueError,
        TypeError,
    ):

        return {
            "passed": False,
            "invoice_date_valid": False,
            "due_date_valid": None,
            "warnings": [
                "Invoice date is not a valid date."
            ],
        }

    # --------------------------------------------------------
    # Validate due date
    # --------------------------------------------------------

    due_date_valid = None

    if due_date is not None:

        try:

            if isinstance(due_date, date):

                due_date_obj = due_date

            elif isinstance(due_date, str):

                due_date_obj = date.fromisoformat(
                    due_date
                )

            else:

                raise TypeError(
                    "Unsupported due_date type"
                )

            due_date_valid = True

            # ------------------------------------------------
            # Logical ordering
            # ------------------------------------------------

            if due_date_obj < invoice_date_obj:

                due_date_valid = False

                warnings.append(
                    "Due date occurs before invoice date."
                )

        except (
            ValueError,
            TypeError,
        ):

            due_date_valid = False

            warnings.append(
                "Due date is not a valid date."
            )

    # --------------------------------------------------------
    # Overall result
    # --------------------------------------------------------

    passed = (
        due_date_valid is not False
    )

    return {
        "passed": passed,

        "invoice_date_valid": True,

        "due_date_valid": due_date_valid,

        "warnings": warnings,
    }

# ============================================================
# Required Field Validation
# ============================================================

def validate_required_fields(
    document: dict,
    document_type: str,
) -> list[str]:
    """
    Check required fields based on document type.
    """

    required = REQUIRED_FIELDS.get(
        document_type,
        [],
    )

    missing = []

    for field in required:

        value = document.get(field)

        if value is None:
            missing.append(field)

        elif value == "":
            missing.append(field)

        elif value == []:
            missing.append(field)

    return missing


# ============================================================
# Complete Validation
# ============================================================

def run_validation(
    document,
    document_dict: dict,
    tolerance: float = DEFAULT_TOLERANCE,
) -> dict[str, Any]:
    """
    Run all deterministic validation checks.

    Returns a structured validation result.
    """

    # --------------------------------------------------------
    # Line items
    # --------------------------------------------------------

    line_items_check = validate_line_items(
        document.line_items,
        tolerance,
    )

    # --------------------------------------------------------
    # Subtotal
    # --------------------------------------------------------

    subtotal_check = validate_subtotal(
        document.line_items,
        document.subtotal,
        tolerance,
    )

    # --------------------------------------------------------
    # Total
    # --------------------------------------------------------

    total_check = validate_total(
        document.subtotal,
        document.tax_amount,
        document.discount,
        document.total,
        tolerance,
    )

    # --------------------------------------------------------
    # Dates
    # --------------------------------------------------------

    date_check = validate_dates(
        document.invoice_date,
        document.due_date,
    )

    # --------------------------------------------------------
    # Required fields
    # --------------------------------------------------------

    missing_fields = validate_required_fields(
        document_dict,
        document.document_type,
    )
    optional_warnings = validate_optional_fields(
        document_dict
    )

    # --------------------------------------------------------
    # Determine overall validity
    # --------------------------------------------------------

    checks = {
        "line_items": line_items_check["passed"],
        "subtotal": subtotal_check["passed"],
        "total_matches": total_check["passed"],
        "dates": date_check["passed"],
    }

    failed_checks = [
        name
        for name, value in checks.items()
        if value is False
    ]

    is_valid = (
        len(missing_fields) == 0
        and len(failed_checks) == 0
    )

    return {
        "is_valid": is_valid,

        "checks": checks,

        "line_items": line_items_check,

        "subtotal": subtotal_check,

        "total": total_check,

        "dates": date_check,

        "missing_fields": missing_fields,

        "failed_checks": failed_checks,

        "warnings": (
            date_check["warnings"]
            + optional_warnings
        ),
    }


def validate_optional_fields(
    document_dict: dict,
) -> list[str]:
    """
    Report useful optional fields that are missing.

    Missing optional information does not invalidate
    the document.
    """

    warnings = []

    if not document_dict.get("currency"):
        warnings.append(
            "Currency was not explicitly present in the document."
        )

    if not document_dict.get("payment_method"):
        warnings.append(
            "Payment method was not explicitly present."
        )

    return warnings