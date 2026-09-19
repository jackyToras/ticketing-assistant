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

1. **RAG over CAG:** Retrieve only top-4 most relevant policy chunks (via cosine similarity) instead of sending all policies to Gemini. This reduces token use, improves latency, and makes decisions explainable.

2. **JWT + per-ticket authorization:** Stateless authentication with ownership checks. Returns 404 (not 403) on cross-user access to avoid leaking ticket existence.

3. **Pydantic schema + source validation:** Gemini's JSON response is validated against a schema (ensures valid action, confidence 0–1, reason length). Sources are checked against retrieved chunks—if Gemini cites a policy not in the retrieval results, the decision is rejected (prevents hallucination).

4. **Streamlit as thin client:** The UI never touches the database or manages embeddings. All business logic lives in FastAPI. This keeps deployment simple and authorization centralized at the API layer.

