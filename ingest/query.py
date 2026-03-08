"""
query.py — Retrieve context and query Ollama
"""

import requests
import json
from ingest.config import (
    LLM_MODEL,
    OLLAMA_BASE_URL,
    TOP_K,
)


def retrieve_context(collection, query: str) -> str:
    """Retrieve top K relevant chunks for the query."""
    results = collection.query(query_texts=[query], n_results=TOP_K)
    chunks = results["documents"][0]
    return "\n\n---\n\n".join(chunks)


def ask_ollama(context: str, question: str, model: str = None):
    """Stream response tokens from Ollama — yields each token."""
    prompt = f"""You are a helpful assistant. Use the context below to answer the question.
If the answer is not in the context, say so honestly.

Context:
{context}

Question: {question}

Answer:"""

    payload = {
        "model": model or LLM_MODEL,
        "prompt": prompt,
        "stream": True,
    }

    try:
        response = requests.post(
            f"{OLLAMA_BASE_URL}/api/generate",
            json=payload,
            stream=True,
            timeout=60,
        )
    except requests.exceptions.ConnectionError:
        yield "\x01// error: cannot connect to Ollama — is it running? (ollama serve)"
        return
    except requests.exceptions.Timeout:
        yield "\x01// error: Ollama timed out"
        return

    for line in response.iter_lines():
        if line:
            data = json.loads(line)
            if data.get("error"):
                yield f"\x01// error: {data['error']}"
                return
            token = data.get("response", "")
            if token:
                yield token
            if data.get("done"):
                total = data.get("eval_count", 0) + data.get("prompt_eval_count", 0)
                yield f"\x00{total}"
                break

if __name__ == "__main__":
    print("handles queries")