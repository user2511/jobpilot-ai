# backend/utils/pdf_parser.py
# Extracts raw text from PDF bytes using PyMuPDF (fitz).

import fitz  # PyMuPDF
from backend.utils.logger import get_logger

logger = get_logger(__name__)


def extract_text_from_pdf(file_bytes: bytes) -> str:
    """
    Extract all text from a PDF given its raw bytes.
    Preserves page order. Strips excessive whitespace.

    Args:
        file_bytes: Raw PDF file content

    Returns:
        Clean extracted text string

    Raises:
        ValueError: If PDF cannot be opened or has no text
    """
    try:
        # Open PDF from bytes (not a file path)
        doc = fitz.open(stream=file_bytes, filetype="pdf")

        if doc.page_count == 0:
            raise ValueError("PDF has no pages")

        pages_text = []
        for page_num in range(doc.page_count):
            page = doc[page_num]
            text = page.get_text("text")
            if text.strip():
                pages_text.append(text.strip())

        doc.close()

        if not pages_text:
            raise ValueError("No text could be extracted from PDF. It may be image-only.")

        full_text = "\n\n".join(pages_text)

        # Clean up excessive whitespace while preserving structure
        lines = [line.strip() for line in full_text.splitlines()]
        cleaned = "\n".join(line for line in lines if line)

        logger.info(f"PDF extracted: {len(cleaned)} chars from {len(pages_text)} pages")
        return cleaned

    except fitz.FileDataError as e:
        logger.error(f"Invalid PDF file: {e}")
        raise ValueError(f"Could not open PDF: {e}")
    except Exception as e:
        logger.error(f"PDF extraction failed: {e}")
        raise
