from __future__ import annotations

import hashlib
from pathlib import Path

import chromadb

from ..config import settings


class HashEmbeddingFunction:
    """Small offline embedding function suitable for a deterministic local demo."""

    def __init__(self, dimensions: int = 64):
        self.dimensions = dimensions

    def __call__(self, input: list[str]) -> list[list[float]]:
        vectors: list[list[float]] = []
        for text in input:
            raw = hashlib.sha256(text.lower().encode()).digest()
            values = [((byte / 255.0) * 2.0) - 1.0 for byte in raw]
            vectors.append((values * ((self.dimensions // len(values)) + 1))[: self.dimensions])
        return vectors

    def name(self) -> str:
        return "algebramate-hash-embedding"


def get_client() -> chromadb.PersistentClient:
    path = Path(settings.chroma_path)
    if not path.is_absolute():
        path = Path(__file__).resolve().parents[3] / path
    path.mkdir(parents=True, exist_ok=True)
    return chromadb.PersistentClient(path=str(path))


def get_questions_collection():
    return get_client().get_or_create_collection(
        name="algebra_questions",
        embedding_function=HashEmbeddingFunction(),
        metadata={"description": "Approved AlgebraMate SG development questions"},
    )
