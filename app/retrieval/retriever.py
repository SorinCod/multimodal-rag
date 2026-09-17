from app.retrieval.embeddings import generate_embeddings
from app.retrieval.vector_store import query


def retrieve_relevant_chunks(user_question: str, top_k: int = 5, source_file: str = None) -> list[dict]:
    """
    Given a user question, returns the most relevant chunks
    from the vector store, along with their metadata.
    If source_file is given, restricts the search to that document only.
    """
    question_embedding = generate_embeddings([user_question])[0]
    results = query(question_embedding, top_k=top_k, source_file=source_file)

    relevant_chunks = []
    documents = results["documents"][0]
    metadatas = results["metadatas"][0]
    distances = results["distances"][0]

    for doc, meta, distance in zip(documents, metadatas, distances):
        relevant_chunks.append({
            "text": doc,
            "metadata": meta,
            "distance": distance,
        })

    return relevant_chunks