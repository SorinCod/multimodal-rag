import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import streamlit as st

from app.ingestion.pdf_parser import process_document
from app.ingestion.table_extractor import extract_tables, table_to_text, table_to_dataframe
from app.ingestion.validator import validate_pages, validate_tables
from app.review_queue.queue_manager import add_to_queue, reset_queue
from app.review_queue.review_ui import render_review_queue
from app.retrieval.embeddings import split_into_chunks, generate_embeddings
from app.retrieval.vector_store import add_chunks, list_source_files, reset_vector_store
from app.retrieval.retriever import retrieve_relevant_chunks
from app.generation.llm_client import generate_answer, verify_answer


st.set_page_config(page_title="Multimodal Document RAG", layout="wide")


def embed_and_store(text: str, metadata: dict) -> None:
    """Chunks a piece of text, embeds it, and stores it in the vector store."""
    chunks = split_into_chunks(text, chunk_size=400, overlap=80)
    if not chunks:
        return
    embeddings = generate_embeddings(chunks)
    metadatas = [metadata for _ in chunks]
    add_chunks(chunks, embeddings, metadatas)


def process_uploaded_file(uploaded_file) -> dict:
    """
    Runs the full ingestion pipeline on an uploaded PDF:
    extraction -> validation -> accepted content goes straight to the
    vector store, rejected/low-confidence content goes to the review queue.
    Tables are extracted first; pages that contain a table are excluded
    from raw text embedding, to avoid embedding the same information twice.
    Raises ValueError if the uploaded file is not a valid PDF.
    """
    os.makedirs("data/raw", exist_ok=True)
    save_path = os.path.join("data/raw", uploaded_file.name)
    with open(save_path, "wb") as f:
        f.write(uploaded_file.getbuffer())

    summary = {
        "accepted_pages": 0,
        "queued_pages": 0,
        "tables_found": 0,
        "tables_queued": 0,
        "tables": [],
    }

    validated_tables = []
    try:
        tables = extract_tables(save_path)
        validated_tables = validate_tables(tables)
        summary["tables_found"] = len(validated_tables)
        summary["tables"] = validated_tables

        for table in validated_tables:
            if table["status"] == "accepted":
                table_text = table_to_text(table)
                metadata = {
                    "source_file": uploaded_file.name,
                    "page": table["page"],
                    "type": "table",
                }
                embed_and_store(table_text, metadata)
            else:
                add_to_queue(table, source_file=uploaded_file.name, item_type="table")
                summary["tables_queued"] += 1
    except Exception:
        pass  # scanned PDFs have no table structure Camelot can read

    pages_with_tables = {t["page"] for t in validated_tables}

    # process_document raises ValueError if the file is not a valid PDF -
    # this propagates up to the caller in main.py, which shows a clean error
    pages = process_document(save_path)
    validated_pages = validate_pages(pages)

    for page in validated_pages:
        metadata = {"source_file": uploaded_file.name, "page": page["page"]}
        if page["status"] == "accepted":
            if page["page"] not in pages_with_tables:
                embed_and_store(page["text"], metadata)
            summary["accepted_pages"] += 1
        else:
            add_to_queue(page, source_file=uploaded_file.name, item_type="page")
            summary["queued_pages"] += 1

    return summary


# --- UI: three bordered columns, all visible at once ---

st.title("Multimodal Document RAG")

with st.expander("Reset knowledge base"):
    st.write("This will permanently delete all processed documents and the review queue.")
    if st.button("Clear everything", type="primary"):
        reset_vector_store()
        reset_queue()
        st.success("Knowledge base cleared.")
        st.rerun()

col_upload, col_chat, col_review = st.columns(3)

with col_upload:
    with st.container(border=True):
        st.header("Upload & Process")
        uploaded_file = st.file_uploader("Choose a PDF file", type=["pdf"])

        if uploaded_file is not None:
            max_size_mb = 20
            if uploaded_file.size > max_size_mb * 1024 * 1024:
                st.error(f"File too large ({uploaded_file.size / 1024 / 1024:.1f} MB). Please upload a file under {max_size_mb} MB.")
                uploaded_file = None

        if uploaded_file is not None and st.button("Process document"):
            with st.spinner("Processing document..."):
                try:
                    summary = process_uploaded_file(uploaded_file)
                except ValueError as e:
                    st.error(f"Could not process this file: {e}")
                    summary = None

            if summary is not None:
                st.success("Done.")
                st.write(f"- Pages accepted: **{summary['accepted_pages']}**")
                st.write(f"- Pages queued: **{summary['queued_pages']}**")
                st.write(f"- Tables found: **{summary['tables_found']}** (queued: {summary['tables_queued']})")

                for table in summary["tables"]:
                    status_label = "Accepted" if table["status"] == "accepted" else "Sent to review"
                    st.caption(f"Table on page {table['page']} - accuracy {table['accuracy']}% - {status_label}")
                    st.dataframe(table_to_dataframe(table))

with col_chat:
    with st.container(border=True):
        st.header("Chat")

        available_files = list_source_files()
        selected_file = st.selectbox(
            "Search within:",
            options=["All documents"] + available_files,
        )
        source_filter = None if selected_file == "All documents" else selected_file

        question = st.text_input("Your question:")

        if question:
            with st.spinner("Thinking..."):
                relevant_chunks = retrieve_relevant_chunks(question, top_k=5, source_file=source_filter)
                answer = generate_answer(question, relevant_chunks)
                verification = verify_answer(answer, relevant_chunks)

            st.write(answer)

            if verification["verified"]:
                st.success(f"Verified: {verification['explanation']}")
            else:
                st.warning(f"Not fully verified: {verification['explanation']}")

            with st.expander("Sources used"):
                for chunk in relevant_chunks:
                    source = chunk["metadata"].get("source_file", "unknown")
                    page = chunk["metadata"].get("page", "?")
                    st.caption(f"{source}, page {page} (distance: {chunk['distance']:.3f})")
                    st.text(chunk["text"][:200])

with col_review:
    with st.container(border=True):
        render_review_queue(on_approve=embed_and_store)