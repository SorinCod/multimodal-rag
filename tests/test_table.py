from app.ingestion.table_extractor import extract_tables

results = extract_tables("data/raw/test_table.pdf")
for t in results:
    print(f"--- Table {t['table_index']} (page {t['page']}, accuracy {t['accuracy']}%) ---")
    print("Columns:", t['columns'])
    for row in t['data']:
        print(row)
    print()