<div align="center">

# Elucidate

**A fully local, privacy-first PDF question-answering app.**
Upload PDFs, ask questions in natural language, get streamed answers — no internet, no API keys, no data leaves your machine.

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-3.x-000000?style=for-the-badge&logo=flask&logoColor=white)](https://flask.palletsprojects.com)
[![Ollama](https://img.shields.io/badge/Ollama-Local_LLM-FF6B35?style=for-the-badge)](https://ollama.com)
[![ChromaDB](https://img.shields.io/badge/ChromaDB-Vector_Store-8B5CF6?style=for-the-badge)](https://www.trychroma.com)
[![License](https://img.shields.io/badge/License-MIT-22C55E?style=for-the-badge)](LICENSE)

</div>

---

## What is Elucidate?

Elucidate is a **RAG (Retrieval-Augmented Generation)** application that runs entirely on your machine. It chunks your PDFs into searchable pieces, embeds them using `sentence-transformers`, stores them in ChromaDB, and answers your questions by retrieving the most relevant chunks and feeding them to a local Ollama LLM.

```
┌─────────────┐    chunk + embed    ┌──────────────┐
│  PDF Upload │ ──────────────────► │   ChromaDB   │
└─────────────┘                     └──────┬───────┘
                                           │ top-K chunks
┌─────────────┐    stream answer    ┌──────▼───────┐
│    You      │ ◄────────────────── │    Ollama    │
└─────────────┘                     └──────────────┘
```

---

## Pick your model — based on RAM

| RAM | Recommended Model | Pull Command |
|-----|-------------------|--------------|
| **8 GB** | `llama3.2:latest` *(3B — fast, lightweight)* | `ollama pull llama3.2:latest` |
| **16 GB+** | `llama3.1:8b` *(8B — richer reasoning)* | `ollama pull llama3.1:8b` |

> You can switch models live in the UI without restarting.

---

## Deployment

### Option 1 — Local

```bash
# 1. Clone & setup
git clone <repo-url>
cd Elucidate
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# 2. Start Ollama and pull a model
#Download ollama
curl -fsSL https://ollama.com/install.sh | sh
ollama serve                     # separate terminal
ollama pull llama3.2:latest      # 8 GB RAM
# or
ollama pull llama3.1:8b          # 16 GB+ RAM

# 3. Run
python -m app.Elucidate
```

Open **http://localhost:3000**

---

### Option 2 — Docker

Runs Elucidate and Ollama as two containers. Ollama reuses models already pulled on your machine via a shared volume.

**Prerequisites:** Docker + Docker Compose installed.

```bash
#Download ollama
curl -fsSL https://ollama.com/install.sh | sh
# Pull your model first (one time)
ollama pull llama3.2:latest      # 8 GB RAM
# or
ollama pull llama3.1:8b          # 16 GB+ RAM

# Build and start
docker compose up --build
```

Open **http://localhost:3000**

> **Note:** The Docker setup uses more conservative defaults (smaller chunks, lower context length) to fit comfortably in a container. See the config table below.
>
> `chroma_db` and `.venv` are excluded from the image via `.dockerignore`. Embeddings are persisted on your host via the `./chroma_db:/app/chroma_db` volume — they survive container restarts.

To stop:
```bash
docker compose down
```

To rebuild after code changes:
```bash
docker compose up --build
```

---

## Configuration

All values are read from environment variables with sensible defaults. Override them in `docker-compose.yml` or export them before running locally.

| Variable | Local Default | Docker Default | Description |
|----------|--------------|----------------|-------------|
| `LLM_MODEL` | `llama3.1:8b` | `llama3.2:latest` | Ollama model to use |
| `EMBEDDING_MODEL` | `all-MiniLM-L6-v2` | `all-MiniLM-L6-v2` | Sentence-transformers model |
| `CHUNK_SIZE` | `2000` | `1000` | Characters per chunk |
| `CHUNK_OVERLAP` | `250` | `150` | Overlap between chunks |
| `TOP_K` | `10` | `5` | Chunks retrieved per query |
| `OLLAMA_CONTEXT_LENGTH` | `8192` | `4096` | LLM context window |
| `OLLAMA_BASE_URL` | `http://localhost:11434` | `http://ollama:11434` | Ollama endpoint |
| `CHROMA_DB_PATH` | `./chroma_db` | `/app/chroma_db` | Vector DB path |

---

## Project Structure

```
Elucidate/
│
├── app/
│   ├── Elucidate.py          # Flask app — all routes
│   ├── Operations.py         # Business logic, model management, token tracking
│   └── templates/
│       ├── base.html         # Shared layout, CSS variables, nav
│       ├── index.html        # PDF library page
│       ├── book.html         # Split view: PDF viewer + chat
│       └── error.html        # 404 page
│
├── ingest/
│   ├── ingest.py             # PDF extraction, chunking, ChromaDB storage
│   ├── query.py              # Chunk retrieval + Ollama streaming
│   └── config.py             # All config — reads from env vars
│
├── Dockerfile
├── docker-compose.yml
├── .dockerignore             # Excludes .venv, __pycache__, chroma_db, .git
├── pdf/                      # Uploaded PDFs (auto-created)
├── chroma_db/                # Vector database (persisted via Docker volume)
├── tokens.json               # Cumulative token usage per PDF
└── requirements.txt
```

---

## Usage

| Step | Action |
|------|--------|
| **1. Upload** | Click `[ + UPLOAD PDF ]` — file is chunked and indexed automatically |
| **2. Open** | Click a PDF card from the library |
| **3. Ask** | Type your question in the chat panel on the right |
| **4. Switch model** | Use the model dropdown in the chat header — takes effect on the next question |

---

## API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/pdfs` | List all PDFs with token usage counts |
| `POST` | `/api/initialise` | Upload + index a PDF |
| `POST` | `/api/ask` | Ask a question — streams plain-text response |
| `GET` | `/api/models` | List all locally available Ollama models |
| `POST` | `/api/model` | Switch active model `{ "model": "llama3.1:8b" }` |
| `GET` | `/pdf/<name>` | Serve the raw PDF file for the viewer |

---

## Troubleshooting

<details>
<summary><b>// error: cannot connect to Ollama</b></summary>

**Local:** Ollama isn't running. Start it:
```bash
ollama serve
```

**Docker:** The Ollama container may still be starting. Wait ~10s and retry, or check:
```bash
docker logs elucidate-ollama
```
</details>

<details>
<summary><b>// error: model not found</b></summary>

The selected model hasn't been pulled yet:
```bash
ollama pull llama3.2:latest
```
In Docker, models are read from `~/.ollama` on your host machine via the volume mount — pull on the host, not inside the container.
</details>

<details>
<summary><b>ModuleNotFoundError on startup</b></summary>

Run from the project root with venv active:
```bash
source .venv/bin/activate
python -m app.Elucidate
```
</details>

<details>
<summary><b>Responses feel slow or cut off</b></summary>

Try a lighter model (`llama3.2:latest`) or reduce `OLLAMA_CONTEXT_LENGTH` and `TOP_K` in your env / `docker-compose.yml`.
</details>

---

## Stack

| Layer | Technology |
|-------|-----------|
| Web framework | Flask |
| LLM inference | Ollama (local) |
| Vector store | ChromaDB |
| Embeddings | `sentence-transformers` — `all-MiniLM-L6-v2` |
| PDF parsing | pypdf |
| Frontend | Vanilla HTML/CSS/JS, JetBrains Mono |
