import os

CHROMA_DB_PATH = os.getenv("CHROMA_DB_PATH", os.path.join(os.path.dirname(__file__), '..', 'chroma_db'))

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

LLM_MODEL = os.getenv("LLM_MODEL", "llama3.1:8b")

EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")

TOP_K = int(os.getenv("TOP_K", 10))

CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", 2000))

CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", 250))

OLLAMA_CONTEXT_LENGTH = int(os.getenv("OLLAMA_CONTEXT_LENGTH", 8192))