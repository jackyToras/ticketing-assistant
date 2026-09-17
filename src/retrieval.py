"""Small, local retrieval pipeline for the supplied policy documents."""

import json
from pathlib import Path

import numpy as np
from google import genai
from google.genai import types

from src.config import PROJECT_ROOT, settings


KNOWLEDGE_BASE_DIR = PROJECT_ROOT / "knowledge_base"
CACHE_FILE = PROJECT_ROOT / ".cache" / "policy_embeddings.json"
EMBEDDING_MODEL = "gemini-embedding-001"


class RetrievalError(RuntimeError):
    pass


class PolicyRetriever:
    def __init__(self) -> None:
        if not settings.gemini_api_key:
            raise RetrievalError("GEMINI_API_KEY is not configured in the local .env file")
        self.client = genai.Client(api_key=settings.gemini_api_key)
        self.documents = self._load_documents()
        self.embeddings = self._load_or_create_embeddings()

    @staticmethod
    def _load_documents() -> list[dict[str, str]]:
        documents = []
        for path in sorted(KNOWLEDGE_BASE_DIR.glob("*.md")):
            text = path.read_text(encoding="utf-8").strip()
            # The supplied files are short, but splitting by policy rule keeps retrieval precise.
            chunks = [chunk.strip() for chunk in text.split("\n\n") if chunk.strip()]
            for index, chunk in enumerate(chunks):
                documents.append({"source": path.name, "chunk_id": str(index), "text": chunk})
        if not documents:
            raise RetrievalError("No policy documents were found in knowledge_base")
        return documents

    def _load_or_create_embeddings(self) -> np.ndarray:
        if CACHE_FILE.exists():
            cached = json.loads(CACHE_FILE.read_text(encoding="utf-8"))
            cached_documents = cached.get("documents", [])
            if cached_documents == self.documents:
                return np.asarray(cached["embeddings"], dtype=float)

        response = self.client.models.embed_content(
            model=EMBEDDING_MODEL,
            contents=[document["text"] for document in self.documents],
            config=types.EmbedContentConfig(task_type="RETRIEVAL_DOCUMENT", output_dimensionality=768),
        )
        embeddings = np.asarray([embedding.values for embedding in response.embeddings], dtype=float)
        CACHE_FILE.parent.mkdir(exist_ok=True)
        CACHE_FILE.write_text(
            json.dumps({"documents": self.documents, "embeddings": embeddings.tolist()}), encoding="utf-8"
        )
        return embeddings

    def retrieve(self, query: str, limit: int = 4) -> list[dict[str, str | float]]:
        response = self.client.models.embed_content(
            model=EMBEDDING_MODEL,
            contents=query,
            config=types.EmbedContentConfig(task_type="RETRIEVAL_QUERY", output_dimensionality=768),
        )
        query_embedding = np.asarray(response.embeddings[0].values, dtype=float)
        scores = (self.embeddings @ query_embedding) / (
            np.linalg.norm(self.embeddings, axis=1) * np.linalg.norm(query_embedding)
        )
        top_indices = np.argsort(scores)[-limit:][::-1]
        return [{**self.documents[index], "score": float(scores[index])} for index in top_indices]
