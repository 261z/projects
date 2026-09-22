import json
from functools import lru_cache
from pathlib import Path

from src.config import get_settings
from src.models import MetadataCatalog, TableMetadata


def load_catalog(path: Path | None = None) -> MetadataCatalog:
    metadata_path = path or get_settings().metadata_path
    with metadata_path.open("r", encoding="utf-8") as handle:
        catalog = MetadataCatalog.model_validate(json.load(handle))
    validate_catalog_references(catalog)
    return catalog


def validate_catalog_references(catalog: MetadataCatalog) -> None:
    table_map = {table.qualified_name: table for table in catalog.tables}
    if len(table_map) != len(catalog.tables):
        raise ValueError("Duplicate qualified table names exist in the catalog")

    for table in catalog.tables:
        for foreign_key in table.foreign_keys:
            target = table_map.get(foreign_key.target_table)
            if target is None:
                raise ValueError(
                    f"{table.qualified_name}.{foreign_key.column} references missing table "
                    f"{foreign_key.target_table}"
                )
            target_columns = {column.name for column in target.columns}
            if foreign_key.references_column not in target_columns:
                raise ValueError(
                    f"{table.qualified_name}.{foreign_key.column} references missing column "
                    f"{foreign_key.target_table}.{foreign_key.references_column}"
                )


@lru_cache
def get_catalog() -> MetadataCatalog:
    return load_catalog()


def table_map(catalog: MetadataCatalog | None = None) -> dict[str, TableMetadata]:
    active_catalog = catalog or get_catalog()
    return {table.qualified_name: table for table in active_catalog.tables}

