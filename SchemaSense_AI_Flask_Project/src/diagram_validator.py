from __future__ import annotations

from src.metadata_loader import table_map


def mermaid_entity_name(qualified_name: str) -> str:
    return qualified_name.replace(".", "__").upper()


def build_validated_mermaid(table_names: list[str], max_tables: int = 12) -> dict:
    tables = table_map()
    selected = [name for name in table_names if name in tables]
    unknown = sorted(set(table_names) - set(selected))
    selected = list(dict.fromkeys(selected))

    if unknown:
        raise ValueError(f"Unknown tables cannot be diagrammed: {', '.join(unknown)}")
    if not selected:
        raise ValueError("No verified tables were supplied")
    if len(selected) > max_tables:
        raise ValueError(f"ER diagrams are limited to {max_tables} tables")

    selected_set = set(selected)
    lines = ["erDiagram"]

    for source_name in selected:
        source = tables[source_name]
        for fk in source.foreign_keys:
            if fk.target_table in selected_set:
                source_entity = mermaid_entity_name(source_name)
                target_entity = mermaid_entity_name(fk.target_table)
                label = f"{fk.column}_to_{fk.references_column}".replace("-", "_")
                lines.append(f"    {target_entity} ||--o{{ {source_entity} : {label}")

    for table_name in selected:
        table = tables[table_name]
        lines.append(f"    {mermaid_entity_name(table_name)} {{")
        for column in table.columns:
            data_type = (
                column.data_type.lower()
                .replace(" ", "_")
                .replace("(", "_")
                .replace(")", "")
                .replace(",", "_")
            )
            key = " PK" if column.primary_key else ""
            if any(fk.column == column.name for fk in table.foreign_keys):
                key = " FK" if not key else " PK_FK"
            lines.append(f"        {data_type} {column.name}{key}")
        lines.append("    }")

    return {
        "mermaid": "\n".join(lines),
        "tables": selected,
        "validated": True,
    }

