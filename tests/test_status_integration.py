from extractor.status import build_validation_decision


def test_wrong_total_requires_review():

    validation = {
        "is_valid": False,

        "checks": {
            "line_items": True,
            "subtotal": True,
            "total_matches": False,
            "dates": True,
        },

        "missing_fields": [],

        "failed_checks": [
            "total_matches"
        ],

        "warnings": [],

        "line_items": {
            "passed": True,
        },

        "subtotal": {
            "passed": True,
        },

        "total": {
            "passed": False,
        },

        "dates": {
            "passed": True,
        },
    }

    result = build_validation_decision(
        validation
    )

    assert result["status"] == "REVIEW_REQUIRED"

    assert result["is_valid"] is False

    assert result["confidence"] == 0.8

    assert result["confidence_level"] == "MEDIUM"

    assert (
        "Failed validation check: total_matches"
        in result["reasons"]
    )