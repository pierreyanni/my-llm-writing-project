# Project TODO

This file tracks the next work items for the repo.

## High priority

- [ ] Add support for ingesting Google Drive documents into the RAG pipeline
- [ ] Add support for ingesting Dropbox documents into the RAG pipeline
- [ ] Add a unified ingestion workflow that can ingest from multiple sources
- [ ] Add documentation for `.env` and database setup
- [ ] Create project-level `CLAUDE.md` in repo root
- [ ] Create global `~/.claude/CLAUDE.md` for personal defaults
- [ ] Add automated tests for ingestion and embedding logic

## Medium priority

- [ ] Add support for Notion exports or Notion API ingestion
- [ ] Add a reusable data schema for documents and metadata
- [ ] Improve metadata capture (source, author, origin path, content type)
- [ ] Add better error handling and retry logging across download/ingest steps
- [ ] Add CLI flags for selecting sources and limiting ingest scope

## Long-term ideas

- [ ] Add a web-based query interface for asking questions over the ingested documents
- [ ] Add source-aware retrieval and answer attribution
- [ ] Add incremental sync so repeated runs only ingest new or changed files
- [ ] Add support for email archives, PDFs, and other text sources

## Notes

- Use this file as the single source of project work in this repo.
- When a task is complete, check it off here and optionally update `README.md` or add a GitHub issue
- If using GitHub issues, link issue IDs to tasks here (e.g. `[#5]`)
