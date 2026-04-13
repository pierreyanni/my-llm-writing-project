# Claude Code — Project Guide

## What this project is

A RAG ingestion pipeline. It downloads personal writing from Dropbox and Google Drive,
extracts text, embeds it with a SentenceTransformer model, and stores it in PostgreSQL
with pgvector. See README.md for the full picture.

## Run order

```bash
python setup_database.py          # first time, or --reset to wipe
python data/dropbox/download_dropbox_files.py
python data/drive/download_drive_files.py
python ingest_data.py
```

All steps are idempotent.

## Key files

| File | Purpose |
|------|---------|
| `setup_database.py` | Creates the `documents` table. Use `--reset` to drop and recreate. |
| `ingest_data.py` | Reads files from `data/*/documents/`, embeds, inserts into DB. |
| `data/utils.py` | Shared `sanitize_filename` and `unique_output_path` helpers. |
| `data/dropbox/download_dropbox_files.py` | Dropbox download + incremental skip. |
| `data/drive/download_drive_files.py` | Google Drive download + incremental skip. |

## Conventions

- New download sources follow the same pattern: download to `data/{source}/documents/`,
  write a `metadata.csv` with at minimum `id`, `name`, `downloaded_name` columns,
  and skip files whose `id` is already in the CSV.
- Shared file utilities go in `data/utils.py`, not inline in each script.
- `ingest_data.py` discovers sources via the `SOURCES` list at the top of the file —
  add new sources there.
- Do not use `setup_database.py --reset` without confirming with the user first.

## Environment

- Credentials live in `.env` (gitignored). See `.env.example` for required vars.
- Google Drive OAuth tokens are cached at `data/drive/token.json` (gitignored).
- Downloaded files are stored under `data/*/documents/` (gitignored).
