from app.retrieval.retriever import retrieve_relevant_chunks
from app.generation.llm_client import generate_answer

question = "How did customer retention change?"

relevant_chunks = retrieve_relevant_chunks(question, top_k=3)
answer = generate_answer(question, relevant_chunks)

print("Question:", question)
print("\nAnswer:\n", answer)