import os
import json
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

_client = None

MODEL_NAME = "openai/gpt-oss-120b"


def get_client():
    global _client
    if _client is None:
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError("GROQ_API_KEY not found. Check your .env file.")
        _client = Groq(api_key=api_key)
    return _client


def build_context(chunks: list[dict]) -> str:
    """
    Combines retrieved chunks into a single context string,
    labeling each one with its source, so the model (and the
    verification step) can trace claims back to a source.
    """
    parts = []
    for i, chunk in enumerate(chunks):
        source = chunk["metadata"].get("source_file", "unknown")
        page = chunk["metadata"].get("page", "?")
        parts.append(f"[Source {i+1}: {source}, page {page}]\n{chunk['text']}")
    return "\n\n".join(parts)


def generate_answer(user_question: str, relevant_chunks: list[dict]) -> str:
    """
    Generates an answer to the user's question, grounded strictly
    in the provided chunks.
    """
    context = build_context(relevant_chunks)

    system_prompt = (
        "You are a document assistant. Answer the user's question using "
        "ONLY the information in the provided context. If the context does "
        "not contain enough information to answer, say so explicitly instead "
        "of guessing. When you use information from a source, mention which "
        "source number it came from."
    )

    user_prompt = f"Context:\n{context}\n\nQuestion: {user_question}"

    client = get_client()
    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.2,
    )

    return response.choices[0].message.content


def verify_answer(answer: str, relevant_chunks: list[dict]) -> dict:
    """
    Second-pass check: verifies whether the generated answer is actually
    supported by the retrieved context, instead of trusting the first
    generation blindly. Returns {"verified": bool, "explanation": str}.
    """
    context = build_context(relevant_chunks)

    verification_prompt = (
        "You are a fact-checking assistant. Below is a CONTEXT and an ANSWER "
        "generated from it. Check whether every claim in the ANSWER is "
        "actually supported by the CONTEXT. Respond with ONLY a JSON object "
        "with two fields: \"verified\" (true or false) and \"explanation\" "
        "(one short sentence). Do not add any text outside the JSON."
    )

    user_prompt = f"CONTEXT:\n{context}\n\nANSWER:\n{answer}"

    client = get_client()
    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {"role": "system", "content": verification_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.0,
    )

    raw = response.choices[0].message.content.strip()

    try:
        result = json.loads(raw)
        return {
            "verified": bool(result.get("verified", False)),
            "explanation": result.get("explanation", ""),
        }
    except (json.JSONDecodeError, AttributeError):
        return {"verified": False, "explanation": "Could not parse verification response."}