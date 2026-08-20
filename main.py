"""
Command-line interface for the Document Data Extractor.

Example:

    python main.py --file samples/invoice_layout_a.pdf

Optional:

    python main.py \
        --file samples/invoice_layout_a.pdf \
        --out output
"""

import argparse
import json
from pathlib import Path

from extractor.pipeline import process_document


# ============================================================
# CLI
# ============================================================

def parse_arguments():
    """
    Parse command-line arguments.
    """

    parser = argparse.ArgumentParser(
        description=(
            "AI-powered Document Data Extractor "
            "for invoices and receipts."
        )
    )

    parser.add_argument(
        "--file",
        required=True,
        help=(
            "Path to the document "
            "(PDF, image, or text)."
        ),
    )

    parser.add_argument(
        "--out",
        default="output",
        help=(
            "Directory where the extracted JSON "
            "will be saved. Default: output"
        ),
    )

    return parser.parse_args()


# ============================================================
# Main
# ============================================================

def main():
    """
    Main CLI execution.
    """

    args = parse_arguments()

    input_path = Path(
        args.file
    )

    output_dir = Path(
        args.out
    )

    # --------------------------------------------------------
    # Validate input file
    # --------------------------------------------------------

    if not input_path.exists():

        print(
            f"ERROR: File not found: "
            f"{input_path}"
        )

        raise SystemExit(1)

    if not input_path.is_file():

        print(
            f"ERROR: Path is not a file: "
            f"{input_path}"
        )

        raise SystemExit(1)

    # --------------------------------------------------------
    # Process document
    # --------------------------------------------------------

    print(
        "\n"
        + "=" * 80
    )

    print(
        "DOCUMENT DATA EXTRACTOR"
    )

    print(
        "=" * 80
    )

    print(
        f"\nInput: {input_path}"
    )

    print(
        "\nProcessing document..."
    )

    try:

        result = process_document(
            str(input_path)
        )

    except Exception as exc:

        print(
            "\nERROR:"
        )

        print(
            f"{type(exc).__name__}: "
            f"{exc}"
        )

        raise SystemExit(1)

    # --------------------------------------------------------
    # Create output directory
    # --------------------------------------------------------

    output_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    # --------------------------------------------------------
    # Output filename
    # --------------------------------------------------------

    output_file = (
        output_dir
        / f"{input_path.stem}.json"
    )

    # --------------------------------------------------------
    # Save JSON
    # --------------------------------------------------------

    with output_file.open(
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            result,
            file,
            indent=2,
            ensure_ascii=False,
        )

    # --------------------------------------------------------
    # Display summary
    # --------------------------------------------------------

    validation = result[
        "validation"
    ]

    print(
        "\n"
        + "=" * 80
    )

    print(
        "PROCESSING COMPLETE"
    )

    print(
        "=" * 80
    )

    print(
        f"Document type : "
        f"{result['document_type']}"
    )

    print(
        f"Document ID   : "
        f"{result.get('document_id')}"
    )

    print(
        f"Status        : "
        f"{validation['status']}"
    )

    print(
        f"Confidence    : "
        f"{validation['confidence']}"
    )

    print(
        f"Confidence    : "
        f"{validation['confidence_level']}"
    )

    print(
        f"\nOutput saved  : "
        f"{output_file}"
    )

    print(
        "=" * 80
    )


if __name__ == "__main__":
    main()