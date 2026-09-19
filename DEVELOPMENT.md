# Development Process

## Overview

This project is a small end-to-end support-ticket decision assistant using FastAPI, Streamlit, SQLite, JWT authentication, local policy retrieval, and Gemini.

## Building this Project

Architecture and project planning: Independent work.

Code implementation, debugging, testing, and documentation: 
Developed with AI assistance (CODEX) for faster iteration.

All design decisions, RAG pipeline logic, authorization and api endpoints checks, and validation 
strategies were architected and done independently.

## Development Approach

1. Defined the SQLite schema and authentication flow first.
2. Built FastAPI routes and tested JWT authentication and authorization via postman.
3. Implemented a lightweight local retrieval pipeline over the supplied policy files.
4. Added Gemini structured output with Pydantic validation and evidence-source validation.
5. Built the Streamlit interface over HTTP rather than accessing the database directly.
6. Added automated tests and a supplied-case evaluation runner.

## Ownership and Verification

All generated code was reviewed and adapted during implementation. The API was tested with a real synthetic damaged-order scenario; it returned `REQUEST_PHOTOS` and cited `damaged_goods.md`. Automated tests verify registration/login, that one user cannot retrieve another user's ticket, and decision persistence. The supplied-case runner provides a repeatable final evaluation.

## Key Engineering Decisions

- SQLite keeps the intentionally small assignment local and simple.
- Local JSON-cached Gemini embeddings plus NumPy cosine similarity provide RAG without a hosted vector database.
- Gemini receives only the incoming ticket and retrieved policy evidence, and its response is constrained to a validated schema.
- Missing information is explicitly directed to produce `NEEDS_MORE_INFORMATION` instead of a guessed decision.
