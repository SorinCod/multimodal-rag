import json
import os
import uuid
from datetime import datetime

QUEUE_FILE = "data/review_queue.json"


def _load_queue() -> list[dict]:
    """Reads the queue file, or returns an empty list if it doesn't exist yet."""
    if not os.path.exists(QUEUE_FILE):
        return []
    with open(QUEUE_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def _save_queue(queue: list[dict]) -> None:
    os.makedirs(os.path.dirname(QUEUE_FILE), exist_ok=True)
    with open(QUEUE_FILE, "w", encoding="utf-8") as f:
        json.dump(queue, f, indent=2, ensure_ascii=False)


def add_to_queue(item: dict, source_file: str, item_type: str) -> str:
    """
    Adds an item (a page or a table dict, already validated as 'needs_review')
    to the review queue. Returns the generated item_id.
    """
    queue = _load_queue()

    entry = {
        "item_id": str(uuid.uuid4()),
        "source_file": source_file,
        "item_type": item_type,
        "content": item,
        "queue_status": "pending",
        "added_at": datetime.now().isoformat(),
    }

    queue.append(entry)
    _save_queue(queue)
    return entry["item_id"]


def get_pending_items() -> list[dict]:
    """Returns all items still waiting for review."""
    queue = _load_queue()
    return [item for item in queue if item["queue_status"] == "pending"]


def approve_item(item_id: str, corrected_text: str = None) -> bool:
    """
    Marks an item as approved. Optionally overwrites its text
    with a human-corrected version before approving.
    Returns True if the item was found and updated.
    """
    queue = _load_queue()

    for item in queue:
        if item["item_id"] == item_id:
            if corrected_text is not None:
                item["content"]["text"] = corrected_text
            item["queue_status"] = "approved"
            item["reviewed_at"] = datetime.now().isoformat()
            _save_queue(queue)
            return True

    return False


def reject_item(item_id: str, reason: str = None) -> bool:
    """Marks an item as rejected (won't be added to the vector store)."""
    queue = _load_queue()

    for item in queue:
        if item["item_id"] == item_id:
            item["queue_status"] = "rejected"
            item["rejection_reason"] = reason
            item["reviewed_at"] = datetime.now().isoformat()
            _save_queue(queue)
            return True

    return False


def reset_queue() -> None:
    """Clears the entire review queue, discarding pending/approved/rejected items."""
    _save_queue([])