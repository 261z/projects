from __future__ import annotations

from collections import deque

from src.metadata_loader import table_map


def normalize_table_name(name: str, tables: dict) -> str | None:
    cleaned = name.strip().lower()
    exact = {qualified.lower(): qualified for qualified in tables}
    if cleaned in exact:
        return exact[cleaned]
    matches = [qualified for qualified in tables if qualified.split(".")[-1].lower() == cleaned]
    return matches[0] if len(matches) == 1 else None


def get_relationship_subgraph(table_names: list[str], depth: int = 1) -> dict:
    tables = table_map()
    seeds = []
    unknown = []
    for name in table_names:
        normalized = normalize_table_name(name, tables)
        if normalized:
            seeds.append(normalized)
        else:
            unknown.append(name)

    selected = set(seeds)
    relationships = []
    queue = deque((name, 0) for name in seeds)
    seen_edges = set()

    while queue:
        current, current_depth = queue.popleft()
        for source_name, source_table in tables.items():
            for fk in source_table.foreign_keys:
                target_name = fk.target_table
                if current not in {source_name, target_name}:
                    continue
                edge_key = (source_name, fk.column, target_name, fk.references_column)
                if edge_key not in seen_edges:
                    relationships.append(
                        {
                            "from_table": source_name,
                            "from_column": fk.column,
                            "to_table": target_name,
                            "to_column": fk.references_column,
                            "relationship": fk.relationship,
                            "description": fk.description,
                        }
                    )
                    seen_edges.add(edge_key)
                other = target_name if source_name == current else source_name
                if current_depth < depth and other not in selected:
                    selected.add(other)
                    queue.append((other, current_depth + 1))

    return {
        "tables": sorted(selected),
        "relationships": relationships,
        "unknown_tables": unknown,
    }

