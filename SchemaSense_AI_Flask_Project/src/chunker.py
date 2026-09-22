from src.models import TableMetadata


def table_to_document(table: TableMetadata) -> str:
    column_lines = []
    for column in table.columns:
        flags = []
        if column.primary_key:
            flags.append("PRIMARY KEY")
        flags.append("NULLABLE" if column.nullable else "NOT NULL")
        if column.character_maximum_length is not None:
            flags.append(f"MAX LENGTH {column.character_maximum_length}")
        if column.numeric_precision is not None:
            flags.append(f"PRECISION {column.numeric_precision}")
        if column.numeric_scale is not None:
            flags.append(f"SCALE {column.numeric_scale}")
        column_lines.append(
            f"- {column.name}: {column.data_type}; {', '.join(flags)}; {column.description}"
        )

    relationship_lines = [
        (
            f"- {table.qualified_name}.{fk.column} -> "
            f"{fk.target_table}.{fk.references_column}; {fk.description}"
        )
        for fk in table.foreign_keys
    ] or ["- No outbound foreign keys"]

    return "\n".join(
        [
            f"Schema: {table.schema_name}",
            f"Table: {table.table}",
            f"Qualified name: {table.qualified_name}",
            f"Description: {table.description}",
            "Columns:",
            *column_lines,
            "Relationships:",
            *relationship_lines,
            f"Tags: {', '.join(table.tags)}",
        ]
    )
