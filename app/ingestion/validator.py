# Confidence thresholds - below these, content goes to manual review
OCR_CONFIDENCE_THRESHOLD = 0.60
TABLE_ACCURACY_THRESHOLD = 80.0  # Camelot reports accuracy as 0-100


def validate_page(page: dict) -> dict:
    """
    Adds a 'status' field to a page result: 'accepted' or 'needs_review'.
    Native text pages (no 'ocr_confidence' key) are trusted by default,
    unless the extracted text is empty.
    """
    validated = dict(page)  # copy, don't mutate the original

    if "ocr_confidence" in page:
        # this page went through OCR
        if page["ocr_confidence"] < OCR_CONFIDENCE_THRESHOLD:
            validated["status"] = "needs_review"
            validated["reason"] = f"low OCR confidence ({page['ocr_confidence']})"
        else:
            validated["status"] = "accepted"
    else:
        # native text extraction
        if not page["text"].strip():
            validated["status"] = "needs_review"
            validated["reason"] = "empty text extracted"
        else:
            validated["status"] = "accepted"

    return validated


def validate_table(table: dict) -> dict:
    """
    Adds a 'status' field to a table result: 'accepted' or 'needs_review'.
    """
    validated = dict(table)

    if table["accuracy"] < TABLE_ACCURACY_THRESHOLD:
        validated["status"] = "needs_review"
        validated["reason"] = f"low table extraction accuracy ({table['accuracy']}%)"
    else:
        validated["status"] = "accepted"

    return validated


def validate_pages(pages: list[dict]) -> list[dict]:
    """Applies validate_page to a whole list of pages."""
    return [validate_page(p) for p in pages]


def validate_tables(tables: list[dict]) -> list[dict]:
    """Applies validate_table to a whole list of tables."""
    return [validate_table(t) for t in tables]