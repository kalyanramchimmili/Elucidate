import os
import json
import requests

import ingest.config as config
import ingest.ingest as ingestor
import ingest.query as query

dir_path    = os.path.join(os.path.dirname(__file__), '..', 'pdf')
tokens_path = os.path.join(os.path.dirname(__file__), '..', 'tokens.json')

active_state = {
    "collection_id": None,
    "collection": None
}

_active_model = config.LLM_MODEL


# ── Model management ─────────────────────────────────────────

def get_models():
    try:
        res = requests.get(f"{config.OLLAMA_BASE_URL}/api/tags", timeout=3)
        return [m["name"] for m in res.json().get("models", [])]
    except Exception:
        return [config.LLM_MODEL]


def set_model(model_name: str):
    global _active_model
    _active_model = model_name


def get_active_model():
    return _active_model


# ── Token tracking ───────────────────────────────────────────

def _load_tokens():
    if os.path.exists(tokens_path):
        with open(tokens_path) as f:
            return json.load(f)
    return {}


def _save_tokens(data):
    with open(tokens_path, 'w') as f:
        json.dump(data, f)


def add_tokens(pdf_name, count):
    data = _load_tokens()
    key  = pdf_name.replace(".pdf", "").lower()
    data[key] = data.get(key, 0) + count
    _save_tokens(data)


# ── PDF management ───────────────────────────────────────────

def get_pdf_list():
    token_data = _load_tokens()
    files = []
    for file in os.listdir(dir_path):
        if file.endswith('.pdf'):
            key = file.replace(".pdf", "").lower()
            files.append({
                "name": file,
                "tokens": token_data.get(key, 0)
            })
    return files


def initialize_pdf(pdf_name):
    global active_state

    pdf_path        = os.path.join(dir_path, pdf_name)
    collection_name = pdf_name.replace(" ", "_").replace(".pdf", "").lower()

    collection, status = ingestor.initialise(pdf_path, collection_name)

    active_state["collection_id"] = collection_name
    active_state["collection"]    = collection

    _warmup()

    return {"collection_id": collection_name, "status": status}


def ask_pdf(question):
    if active_state["collection"] is None:
        return iter([])

    context = query.retrieve_context(active_state["collection"], question)
    return query.ask_ollama(context, question, model=_active_model)


def _warmup():
    print(f"  Warming up {_active_model}...")
    for _ in query.ask_ollama("", "hello", model=_active_model):
        pass
    print("  Ollama ready.")
