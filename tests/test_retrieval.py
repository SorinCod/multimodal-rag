from app.retrieval.embeddings import split_into_chunks, generate_embeddings
from app.retrieval.vector_store import add_chunks
from app.retrieval.retriever import retrieve_relevant_chunks

sample_text = """
The company's Q3 revenue grew by 12% compared to last quarter.
This growth was mainly driven by the new product line launched in July.
Customer retention also improved significantly, reaching 89%.
The support team reduced average response time to under two hours.
"""

chunks = split_into_chunks(sample_text, chunk_size=100, overlap=20)
embeddings = generate_embeddings(chunks)
metadatas = [{"source_file": "sample.txt", "page": 1} for _ in chunks]

add_chunks(chunks, embeddings, metadatas)
print(f"Added {len(chunks)} chunks to the vector store.")

results = retrieve_relevant_chunks("How did customer retention change?")
for r in results:
    print(f"[distance: {r['distance']:.3f}] {r['text']}")