from __future__ import annotations

from src.config import Settings, get_settings
from src.diagram_validator import build_validated_mermaid
from src.pinecone_store import MetadataVectorStore
from src.relationship_graph import get_relationship_subgraph
from src.metadata_loader import table_map


class SchemaTools:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        self.vector_store = MetadataVectorStore(self.settings)

    def search_metadata(
        self,
        query: str,
        schema_filter: str | None = None,
        top_k: int = 5,
    ) -> dict:
        sources = self.vector_store.search(
            query=query,
            schema_filter=schema_filter,
            top_k=top_k,
        )
        return {
            "query": query,
            "results": [source.model_dump() for source in sources],
            "enough_evidence": bool(sources),
        }

    def get_relationships(self, table_names: list[str], depth: int = 1) -> dict:
        return get_relationship_subgraph(table_names, depth=min(max(depth, 0), 2))

    def generate_er_diagram(
        self,
        table_names: list[str] | None = None,
        depth: int = 0,
        whole_warehouse: bool = False,
    ) -> dict:
        selected_tables = (
            sorted(table_map().keys())
            if whole_warehouse
            else (table_names or [])
        )

        if not selected_tables:
            return {
                "error": "No tables supplied",
                "message": "Provide table names or set whole_warehouse to true.",
            }

        subgraph = get_relationship_subgraph(selected_tables, depth=0)

        if subgraph["unknown_tables"]:
            return {
                "error": "Unknown or ambiguous tables",
                "unknown_tables": subgraph["unknown_tables"],
            }

        diagram = build_validated_mermaid(
            subgraph["tables"],
            max_tables=self.settings.max_er_tables,
        )
        diagram["relationships"] = subgraph["relationships"]
        return diagram

OPENAI_TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "search_metadata",
            "description": (
                "Semantically search the synthetic warehouse metadata. Use this first for "
                "every new question about schemas, tables, or columns."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                    },
                    "schema_filter": {
                        "type": ["string", "null"],
                        "description": (
                            "Optional exact schema: aviation, booking, or operations."
                        ),
                    },
                    "top_k": {
                        "type": "integer",
                        "minimum": 1,
                        "maximum": 10,
                    },
                },
                "required": ["query"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_relationships",
            "description": (
                "Return verified inbound and outbound PK/FK relationships."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "table_names": {
                        "type": "array",
                        "items": {"type": "string"},
                        "minItems": 1,
                    },
                    "depth": {
                        "type": "integer",
                        "minimum": 0,
                        "maximum": 2,
                    },
                },
                "required": ["table_names"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "generate_er_diagram",
            "description": (
                "Create a validated Mermaid ER diagram. For the entire warehouse, "
                "set whole_warehouse to true and pass an empty table_names list."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "table_names": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": (
                            "Specific fully qualified tables. Use an empty list "
                            "when whole_warehouse is true."
                        ),
                    },
                    "depth": {
                        "type": "integer",
                        "minimum": 0,
                        "maximum": 0,
                    },
                    "whole_warehouse": {
                        "type": "boolean",
                        "description": (
                            "Set true only when the user explicitly requests "
                            "all tables or the entire warehouse."
                        ),
                    },
                },
                "required": ["table_names", "whole_warehouse"],
                "additionalProperties": False,
            },
        },
    },
]

