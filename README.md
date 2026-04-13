my-llm-writing-project
======================

A RAG pipeline that ingests personal writing from Dropbox and Google Drive into a
PostgreSQL + pgvector database for semantic search. The end goal is a searchable
archive of 20+ years of writing, queryable with natural language.

## What it does

1. Downloads `.txt`, `.docx`, and `.pptx` files from Dropbox and Google Drive
2. Extracts plain text from each file
3. Embeds the text with `sentence-transformers/all-MiniLM-L6-v2` (384-dim vectors)
4. Stores content, embeddings, and metadata in PostgreSQL via pgvector
5. Tracks downloaded files so repeated runs only process new documents

## Prerequisites

- Python 3.13+
- PostgreSQL with the pgvector extension
- A `.env` file (copy `.env.example` and fill in your values)
- Dropbox access token (see `.env.example`)
- Google Drive OAuth credentials (see `.env.example`)

### Database setup

Run once as a superuser to create the database and enable the vector extension:

```bash
createdb rag_db
psql -d rag_db -c 'CREATE EXTENSION IF NOT EXISTS vector;'
```

Then run the schema setup:

```bash
python setup_database.py
```

Use `--reset` to wipe and recreate the table (destructive):

```bash
python setup_database.py --reset
```

## Quick start

```bash
# 1. Install dependencies
uv sync

# 2. Set up environment
cp .env.example .env
# Edit .env with your credentials

# 3. Create the database schema
python setup_database.py

# 4. Download documents from your sources
python data/dropbox/download_dropbox_files.py
python data/drive/download_drive_files.py

# 5. Ingest into the database
python ingest_data.py
```

Steps 4 and 5 are idempotent — safe to re-run. Already-downloaded and
already-ingested files are skipped automatically.

## Project structure

```
.
├── data/
│   ├── utils.py                        # Shared filename helpers
│   ├── dropbox/
│   │   ├── download_dropbox_files.py   # Download from Dropbox
│   │   └── documents/                  # Downloaded files + metadata.csv (gitignored)
│   └── drive/
│       ├── download_drive_files.py     # Download from Google Drive
│       ├── credentials.json            # OAuth credentials (gitignored)
│       ├── token.json                  # Cached OAuth token (gitignored)
│       └── documents/                  # Downloaded files + metadata.csv (gitignored)
├── ingest_data.py                      # Embed and insert into DB
├── setup_database.py                   # Create DB schema
├── main.py                             # Sanity check
├── .env.example                        # Environment variable template
└── TODO.md                             # Project task tracking
```

## Project tracking

See [TODO.md](TODO.md) for the current task list and next priorities.
