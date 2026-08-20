from extractor.status import (
    determine_status,
    calculate_confidence,
    confidence_level,
    build_review_reasons,
    build_validation_decision,
)


def test_accepted_document():

    validation = {
        "is_valid": True,
        "missing_fields": [],
        "failed_checks": [],
        "warnings": [],
    }

    assert (
        determine_status(validation)
        == "ACCEPTED"
    )


def test_review_required_for_missing_field():

    validation = {
        "is_valid": False,
        "missing_fields": [
            "invoice_date"
        ],
        "failed_checks": [],
        "warnings": [],
    }

    assert (
        determine_status(validation)
        == "REVIEW_REQUIRED"
    )


def test_review_required_for_failed_check():

    validation = {
        "is_valid": False,
        "missing_fields": [],
        "failed_checks": [
            "total_matches"
        ],
        "warnings": [],
    }

    assert (
        determine_status(validation)
        == "REVIEW_REQUIRED"
    )


def test_high_confidence():

    validation = {
        "missing_fields": [],
        "failed_checks": [],
        "warnings": [],
    }

    score = calculate_confidence(
        validation
    )

    assert score == 1.0

    assert (
        confidence_level(score)
        == "HIGH"
    )


def test_confidence_with_warning():

    validation = {
        "missing_fields": [],
        "failed_checks": [],
        "warnings": [
            "Currency missing."
        ],
    }

    score = calculate_confidence(
        validation
    )

    assert score == 0.97


def test_review_reasons():

    validation = {
        "missing_fields": [
            "invoice_date"
        ],
        "failed_checks": [
            "total_matches"
        ],
        "warnings": [],
    }

    reasons = build_review_reasons(
        validation
    )

    assert (
        "Missing required field: invoice_date"
        in reasons
    )

    assert (
        "Failed validation check: total_matches"
        in reasons
    )


def test_complete_decision():

    validation = {
        "is_valid": True,
        "missing_fields": [],
        "failed_checks": [],
        "warnings": [],
    }

    result = build_validation_decision(
        validation
    )

    assert result["status"] == "ACCEPTED"

    assert result["is_valid"] is True

    assert result["confidence"] == 1.0

    assert result["confidence_level"] == "HIGH"

    assert result["reasons"] == []