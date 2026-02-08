my-llm-writing-project
======================

A minimal example that wires together Postgres + pgvector, a SentenceTransformer model, and a pair of scripts that embed sample text and store it with metadata. The goal is to provide a simple starting point for experimenting with retrieval-augmented generation workflows.
The final goal is to build a database with all my writings in electronic form (dropbox, google drive, notion, emails, etc), use a RAG and LLM pipeline to answer all sorts of questions about what I wrote over the last 20 years.


What it does
- Runs a basic greeting via `main.py` to verify the environment.
- Creates a Postgres schema with a `documents` table and vector column (`setup_database.py`).
- Loads the SentenceTransformer model `all-MiniLM-L6-v2`, generates embeddings for sample snippets, and stores them with metadata (`ingest_data.py`).
- Can be extended by swapping in your own text to turn this into a small RAG sandbox.

Prerequisites
- Python 3.13+
- Postgres with the pgvector extension installed and reachable from this machine
- A `.env` (or environment variables) supplying `DB_HOST`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`

Quick start
- `pip install -e .` to install dependencies
- `python main.py` to confirm the environment works
- `python setup_database.py` to create the table and enable vector storage
- `python ingest_data.py` to embed the provided sample documents (swap in your own content when ready)

How to use your own data
- Edit the `documents_to_ingest` list in `ingest_data.py` with your text and metadata.
- Rerun `python ingest_data.py`; it will generate new embeddings and insert them.
