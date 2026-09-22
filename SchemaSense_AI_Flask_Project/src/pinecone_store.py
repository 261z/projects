from __future__ import annotations

import time

from openai import OpenAI
from pinecone import Pinecone, ServerlessSpec

from src.chunker import table_to_document
from src.config import Settings, get_settings
from src.models import SourceRecord, TableMetadata


EMBEDDING_DIMENSIONS = {
    "text-embedding-3-small": 1536,
    "text-embedding-3-large": 3072,
}


class MetadataVectorStore:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        self.settings.require_runtime_keys()
        self.openai = OpenAI(api_key=self.settings.openai_api_key)
        self.pinecone = Pinecone(api_key=self.settings.pinecone_api_key)

    @property
    def dimension(self) -> int:
        try:
            return EMBEDDING_DIMENSIONS[self.settings.openai_embedding_model]
        except KeyError as exc:
            raise ValueError(
                "Set the embedding dimension for the selected model in "
                "src/pinecone_store.py before creating the index."
            ) from exc

    def ensure_index(self) -> None:
        existing = set(self.pinecone.list_indexes().names())
        if self.settings.pinecone_index_name not in existing:
            self.pinecone.create_index(
                name=self.settings.pinecone_index_name,
                dimension=self.dimension,
                metric="cosine",
                spec=ServerlessSpec(
                    cloud=self.settings.pinecone_cloud,
                    region=self.settings.pinecone_region,
                ),
            )
        for _ in range(60):
            description = self.pinecone.describe_index(self.settings.pinecone_index_name)
            if description.status.get("ready"):
                return
            time.sleep(1)
        raise TimeoutError("Pinecone index was not ready after 60 seconds")

    def index(self):
        return self.pinecone.Index(self.settings.pinecone_index_name)

    def embed(self, texts: list[str]) -> list[list[float]]:
        response = self.openai.embeddings.create(
            model=self.settings.openai_embedding_model,
            input=texts,
        )
        return [item.embedding for item in response.data]

    def upsert_tables(self, tables: list[TableMetadata]) -> int:
        self.ensure_index()
        documents = [table_to_document(table) for table in tables]
        vectors = self.embed(documents)
        records = []
        for table, document, vector in zip(tables, documents, vectors, strict=True):
            records.append(
                {
                    "id": table.qualified_name,
                    "values": vector,
                    "metadata": {
                        "document_type": "table_metadata",
                        "schema": table.schema_name,
                        "table": table.table,
                        "qualified_name": table.qualified_name,
                        "tags": table.tags,
                        "text": document,
                    },
                }
            )
        self.index().upsert(vectors=records, namespace=self.settings.pinecone_namespace)
        return len(records)

    def search(
        self,
        query: str,
        top_k: int | None = None,
        schema_filter: str | None = None,
    ) -> list[SourceRecord]:
        query_vector = self.embed([query])[0]
        metadata_filter = {"schema": {"$eq": schema_filter}} if schema_filter else None
        result = self.index().query(
            namespace=self.settings.pinecone_namespace,
            vector=query_vector,
            top_k=min(top_k or self.settings.retrieval_top_k, 10),
            include_metadata=True,
            filter=metadata_filter,
        )
        sources = []
        for match in result.matches:
            if match.score < self.settings.retrieval_min_score:
                continue
            metadata = match.metadata or {}
            sources.append(
                SourceRecord(
                    qualified_name=metadata.get("qualified_name", match.id),
                    score=float(match.score),
                    excerpt=metadata.get("text", ""),
                )
            )
        return sources
