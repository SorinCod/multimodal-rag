import chromadb
import streamlit as st

COLLECTION_NAME = "documents"


@st.cache_resource
def get_collection():
    client = chromadb.PersistentClient(path="data/chroma_db")
    return client.get_or_create_collection(name=COLLECTION_NAME)


def add_chunks(chunks: list[str], embeddings: list[list[float]], metadatas: list[dict]) -> None:
    """
    Adds chunks with their embeddings and metadata to the vector store.
    metadatas should contain things like {"source_file": ..., "page": ...}
    so results can be traced back to their origin later.
    """
    collection = get_collection()
    ids = [f"chunk_{collection.count() + i}" for i in range(len(chunks))]

    collection.add(
        ids=ids,
        embeddings=embeddings,
        documents=chunks,
        metadatas=metadatas,
    )


def query(query_embedding: list[float], top_k: int = 5, source_file: str = None) -> dict:
    """
    Finds the top_k most similar chunks to the given query embedding,
    optionally restricted to a single source file.
    """
    collection = get_collection()
    where_filter = {"source_file": source_file} if source_file else None
    return collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k,
        where=where_filter,
    )


def list_source_files() -> list[str]:
    """Returns the distinct source file names currently stored in the vector store."""
    collection = get_collection()
    all_items = collection.get()
    sources = {meta.get("source_file") for meta in all_items["metadatas"] if meta}
    return sorted(sources)


def reset_vector_store() -> None:
    """
    Deletes all chunks from the vector store and clears the cached
    collection object, so a fresh one is created on next access.
    """
    collection = get_collection()
    all_items = collection.get()
    if all_items["ids"]:
        collection.delete(ids=all_items["ids"])

    get_collection.clear()