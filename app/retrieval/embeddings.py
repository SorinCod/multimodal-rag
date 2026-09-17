from sentence_transformers import SentenceTransformer
import streamlit as st


@st.cache_resource
def get_model():
    print("Loading embedding model...")
    return SentenceTransformer("all-MiniLM-L6-v2")


def split_into_chunks(text: str, chunk_size: int = 400, overlap: int = 80) -> list[str]:
    """
    Splits a long text into smaller overlapping chunks.
    Overlap keeps some context shared between consecutive chunks,
    so a sentence split across a chunk boundary isn't lost entirely.
    """
    text = text.strip()
    if not text:
        return []

    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start += chunk_size - overlap

    return chunks


def generate_embeddings(texts: list[str]) -> list[list[float]]:
    """Generates one embedding vector per input text."""
    model = get_model()
    embeddings = model.encode(texts, show_progress_bar=False)
    return embeddings.tolist()