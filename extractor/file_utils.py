from pathlib import Path

import fitz

import os

import pytesseract
from PIL import Image

TESSERACT_CMD = os.getenv("TESSERACT_CMD")

if TESSERACT_CMD:
    pytesseract.pytesseract.tesseract_cmd = TESSERACT_CMD

SUPPORTED_EXTENSIONS = {
    ".pdf": "pdf",
    ".txt": "text",
    ".png": "image",
    ".jpg": "image",
    ".jpeg": "image",
}


def detect_file_type(path: str) -> str:
    """
    Detect the supported document type from the file extension.

    Returns:
        pdf, text, or image

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the extension is unsupported.
    """

    file_path = Path(path)

    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    extension = file_path.suffix.lower()

    if extension not in SUPPORTED_EXTENSIONS:
        raise ValueError(
            f"Unsupported file type: {extension}. "
            f"Supported types: {list(SUPPORTED_EXTENSIONS.keys())}"
        )

    return SUPPORTED_EXTENSIONS[extension]


def extract_text_from_pdf(path: str) -> str:
    """
    Extract text from a text-based PDF using PyMuPDF.
    """

    text_parts = []

    with fitz.open(path) as document:
        for page_number, page in enumerate(document, start=1):
            page_text = page.get_text("text")

            if page_text:
                text_parts.append(
                    f"--- Page {page_number} ---\n{page_text}"
                )

    return "\n\n".join(text_parts).strip()


def extract_text_from_txt(path: str) -> str:
    """
    Extract text from a UTF-8 text file.
    """

    with open(path, "r", encoding="utf-8") as file:
        return file.read().strip()


def extract_text_from_image(path: str) -> str:
    """
    Extract text from an image using Tesseract OCR.
    """

    try:
        image = Image.open(path)

        text = pytesseract.image_to_string(
            image,
            lang="eng",
        )

        return text.strip()

    except Exception as exc:
        raise RuntimeError(
            f"OCR failed for image: {path}"
        ) from exc


def extract_text(path: str) -> str:
    """
    Main text extraction entry point.
    """

    file_type = detect_file_type(path)

    if file_type == "pdf":

        text = extract_text_from_pdf(path)

        if not has_extractable_text(text):
            print(
                "Little or no text detected. "
                "Falling back to OCR..."
            )

            text = ocr_pdf(path)

    elif file_type == "text":

        text = extract_text_from_txt(path)

    elif file_type == "image":

        text = extract_text_from_image(path)

    else:

        raise ValueError(
            f"Unsupported file type: {file_type}"
        )

    if not text.strip():
        raise RuntimeError(
            f"No text could be extracted from: {path}"
        )

    return text

def has_extractable_text(text: str, minimum_characters: int = 20) -> bool:
    """
    Determine whether extracted text is substantial enough
    to be useful for downstream processing.
    """

    if not text:
        return False

    normalized = " ".join(text.split())

    return len(normalized) >= minimum_characters

def ocr_pdf(path: str) -> str:
    """
    Render PDF pages as images and run OCR on each page.
    Used when the PDF contains little or no extractable text.
    """

    text_parts = []

    try:
        with fitz.open(path) as document:

            for page_number, page in enumerate(
                document,
                start=1,
            ):
                pixmap = page.get_pixmap(
                    matrix=fitz.Matrix(2, 2),
                    alpha=False,
                )

                image = Image.frombytes(
                    "RGB",
                    [
                        pixmap.width,
                        pixmap.height,
                    ],
                    pixmap.samples,
                )

                page_text = pytesseract.image_to_string(
                    image,
                    lang="eng",
                )

                if page_text.strip():
                    text_parts.append(
                        f"--- Page {page_number} ---\n"
                        f"{page_text.strip()}"
                    )

        return "\n\n".join(text_parts).strip()

    except Exception as exc:
        raise RuntimeError(
            f"OCR failed for PDF: {path}"
        ) from exc