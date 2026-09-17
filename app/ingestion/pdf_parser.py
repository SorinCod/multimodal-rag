import fitz  # PyMuPDF - for reading PDF structure
import os


def is_valid_pdf(pdf_path: str) -> tuple[bool, str]:
    """
    Checks whether a file is a readable, non-empty PDF before running
    it through the pipeline. Returns (is_valid, error_message).
    error_message is empty when is_valid is True.
    """
    if not os.path.exists(pdf_path):
        return False, "File not found."

    if os.path.getsize(pdf_path) == 0:
        return False, "The file is empty (0 bytes)."

    try:
        document = fitz.open(pdf_path)
    except Exception as e:
        return False, f"The file could not be opened as a PDF: {e}"

    if document.page_count == 0:
        document.close()
        return False, "The PDF has no pages."

    document.close()
    return True, ""


def has_native_text(pdf_path: str, char_threshold: int = 50) -> bool:
    """
    Checks whether the PDF has directly extractable text (not just a scanned image).
    Opens each page and counts extracted characters.
    """
    document = fitz.open(pdf_path)
    total_chars = 0

    for page in document:
        page_text = page.get_text()
        total_chars += len(page_text.strip())

    document.close()

    return total_chars > char_threshold


def extract_native_text(pdf_path: str) -> list[dict]:
    """
    Extracts text directly from the PDF (no OCR), page by page.
    """
    document = fitz.open(pdf_path)
    results = []

    for index, page in enumerate(document):
        results.append({
            "page": index + 1,
            "text": page.get_text().strip()
        })

    document.close()
    return results


def process_document(pdf_path: str) -> list[dict]:
    """
    Entry point: validates the file first, then decides between
    text extraction and OCR.
    """
    from app.ingestion.ocr import extract_text_ocr

    is_valid, error_message = is_valid_pdf(pdf_path)
    if not is_valid:
        raise ValueError(f"Invalid PDF: {error_message}")

    if has_native_text(pdf_path):
        print(f"[{pdf_path}] native text detected, direct extraction")
        return extract_native_text(pdf_path)
    else:
        print(f"[{pdf_path}] no native text, applying OCR")
        return extract_text_ocr(pdf_path)