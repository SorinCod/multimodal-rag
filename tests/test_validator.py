from app.ingestion.pdf_parser import process_document
from app.ingestion.table_extractor import extract_tables
from app.ingestion.validator import validate_pages, validate_tables

pages = process_document("data/raw/test_scanned.pdf")
validated_pages = validate_pages(pages)
for p in validated_pages:
    print(p["page"], p["status"], p.get("reason", ""))

tables = extract_tables("data/raw/test_table.pdf")
validated_tables = validate_tables(tables)
for t in validated_tables:
    print(t["table_index"], t["status"], t.get("reason", ""))