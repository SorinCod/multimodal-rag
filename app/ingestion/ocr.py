import easyocr
import fitz
import os
import streamlit as st


@st.cache_resource
def get_reader():
    print("Loading EasyOCR models (takes a few seconds the first time)...")
    return easyocr.Reader(['en'])


def extract_text_ocr(pdf_path: str) -> list[dict]:
    """
    For scanned PDFs: converts each page into an image,
    then runs EasyOCR on each image.
    """
    document = fitz.open(pdf_path)
    reader = get_reader()
    results = []

    os.makedirs("data/raw", exist_ok=True)

    for index, page in enumerate(document):
        pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
        temp_path = f"data/raw/_temp_page_{index}.png"
        pix.save(temp_path)

        detections = reader.readtext(temp_path, detail=1)

        page_text = " ".join([text for (_, text, confidence) in detections])
        avg_confidence = (
            sum(confidence for (_, _, confidence) in detections) / len(detections)
            if detections else 0.0
        )

        results.append({
            "page": index + 1,
            "text": page_text,
            "ocr_confidence": round(avg_confidence, 3)
        })

        os.remove(temp_path)

    document.close()
    return results