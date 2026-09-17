import streamlit as st
import pandas as pd
from app.review_queue.queue_manager import get_pending_items, approve_item, reject_item
from app.ingestion.table_extractor import table_to_dataframe, table_to_text


def render_review_queue(on_approve=None):
    """
    Renders the human review queue as a Streamlit page.
    on_approve: optional callback called with (text, metadata) after
    an item is approved, so approved content can be embedded and
    added to the vector store.
    """
    st.header("Review Queue")

    pending = get_pending_items()

    if not pending:
        st.info("No items waiting for review. Everything looks good!")
        return

    st.write(f"**{len(pending)}** item(s) waiting for review.")

    for item in pending:
        with st.container(border=True):
            st.subheader(f"{item['item_type'].capitalize()} from {item['source_file']}")
            st.caption(f"Reason: {item['content'].get('reason', 'unknown')}")

            if item["item_type"] == "table":
                st.dataframe(table_to_dataframe(item["content"]))
                text_for_approval = table_to_text(item["content"])
            else:
                original_text = item["content"].get("text", "")
                st.text_area(
                    "Extracted text (edit if needed before approving):",
                    value=original_text,
                    key=f"text_{item['item_id']}",
                    height=150,
                )
                text_for_approval = None

            col1, col2 = st.columns(2)

            with col1:
                if st.button("Approve", key=f"approve_{item['item_id']}"):
                    if item["item_type"] == "table":
                        corrected = text_for_approval
                    else:
                        corrected = st.session_state[f"text_{item['item_id']}"]

                    approve_item(item["item_id"], corrected_text=corrected)

                    if corrected and corrected.strip():
                        if on_approve is not None:
                            metadata = {
                                "source_file": item["source_file"],
                                "page": item["content"].get("page", "?"),
                            }
                            on_approve(corrected, metadata)
                        st.success("Approved and added to the knowledge base.")
                    else:
                        st.warning("Approved, but the text was empty — nothing was added to the knowledge base.")

                    st.rerun()

            with col2:
                if st.button("Reject", key=f"reject_{item['item_id']}"):
                    reject_item(item["item_id"], reason="Rejected during manual review")
                    st.warning("Rejected.")
                    st.rerun()