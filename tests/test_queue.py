from app.ingestion.validator import validate_pages
from app.ingestion.ocr import extract_text_ocr
from app.review_queue.queue_manager import add_to_queue, get_pending_items, approve_item

pages = extract_text_ocr("data/raw/test_scanned.pdf")
validated = validate_pages(pages)

for page in validated:
    if page["status"] == "needs_review":
        item_id = add_to_queue(page, source_file="test_scanned.pdf", item_type="page")
        print("Added to queue:", item_id)

pending = get_pending_items()
print(f"\n{len(pending)} pending item(s) in queue:")
for item in pending:
    print(item["item_id"], "-", item["content"].get("reason", ""))

# if pending:
#     first_id = pending[0]["item_id"]
#     approve_item(first_id, corrected_text="Manually corrected text goes here.")
#     print(f"\nApproved item {first_id}")