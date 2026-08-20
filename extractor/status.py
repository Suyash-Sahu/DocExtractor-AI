"""
Confidence and status decision engine.

Converts deterministic validation results into:
- ACCEPTED
- REVIEW_REQUIRED

Also generates confidence levels and human-readable reasons.
"""


def determine_status(validation: dict) -> str:
    """
    Determine whether the extracted document can be accepted.

    A document is accepted only when:
    - validation.is_valid is True
    - no required fields are missing
    - no deterministic validation checks failed
    """

    if not validation.get("is_valid", False):
        return "REVIEW_REQUIRED"

    if validation.get("missing_fields"):
        return "REVIEW_REQUIRED"

    if validation.get("failed_checks"):
        return "REVIEW_REQUIRED"

    return "ACCEPTED"


def build_review_reasons(
    validation: dict,
) -> list[str]:
    """
    Convert validation failures into human-readable reasons.
    """

    reasons = []

    for field in validation.get(
        "missing_fields",
        []
    ):
        reasons.append(
            f"Missing required field: {field}"
        )

    for check in validation.get(
        "failed_checks",
        []
    ):
        reasons.append(
            f"Failed validation check: {check}"
        )

    for warning in validation.get(
        "warnings",
        []
    ):
        if warning not in reasons:
            reasons.append(warning)

    return reasons


def calculate_confidence(
    validation: dict,
) -> float:
    """
    Calculate a heuristic confidence score.

    This is NOT an ML probability.
    It represents deterministic validation support.
    """

    score = 1.0

    missing_fields = validation.get(
        "missing_fields",
        []
    )

    score -= (
        0.15 * len(missing_fields)
    )

    failed_checks = validation.get(
        "failed_checks",
        []
    )

    score -= (
        0.20 * len(failed_checks)
    )

    warnings = validation.get(
        "warnings",
        []
    )

    score -= (
        0.03 * len(warnings)
    )

    score = max(
        0.0,
        min(1.0, score)
    )

    return round(score, 2)


def confidence_level(
    score: float,
) -> str:
    """
    Convert numeric confidence into a level.
    """

    if score >= 0.90:
        return "HIGH"

    if score >= 0.70:
        return "MEDIUM"

    return "LOW"


def build_validation_decision(
    validation: dict,
) -> dict:
    """
    Build the final Phase 6 decision.
    """

    status = determine_status(
        validation
    )

    score = calculate_confidence(
        validation
    )

    level = confidence_level(
        score
    )

    if status == "REVIEW_REQUIRED":

        reasons = build_review_reasons(
            validation
        )

    else:

        reasons = []

    return {
        "status": status,

        "is_valid": (
            status == "ACCEPTED"
        ),

        "confidence": score,

        "confidence_level": level,

        "reasons": reasons,

        "warnings": validation.get(
            "warnings",
            []
        ),
    }