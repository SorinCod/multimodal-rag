from app.ingestion.pdf_parser import process_document

result = process_document("data/raw/test_scanned.pdf")
for page in result:
    print(f"--- Page {page['page']} ---")
    print(page['text'][:200])
    print()