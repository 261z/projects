from __future__ import annotations

import re

from pydantic import BaseModel, Field, model_validator


class ColumnMetadata(BaseModel):
    name: str
    data_type: str
    nullable: bool = True
    description: str
    primary_key: bool = False
    character_maximum_length: int | None = None
    numeric_precision: int | None = None
    numeric_scale: int | None = None

    @model_validator(mode="after")
    def derive_size_attributes(self) -> "ColumnMetadata":
        character_match = re.fullmatch(
            r"(?:VAR)?CHAR\((\d+)\)", self.data_type.strip(), re.IGNORECASE
        )
        numeric_match = re.fullmatch(
            r"(?:DECIMAL|NUMERIC)\((\d+)\s*,\s*(\d+)\)",
            self.data_type.strip(),
            re.IGNORECASE,
        )
        if character_match and self.character_maximum_length is None:
            self.character_maximum_length = int(character_match.group(1))
        if numeric_match:
            if self.numeric_precision is None:
                self.numeric_precision = int(numeric_match.group(1))
            if self.numeric_scale is None:
                self.numeric_scale = int(numeric_match.group(2))
        return self


class ForeignKeyMetadata(BaseModel):
    column: str
    references_schema: str
    references_table: str
    references_column: str
    relationship: str = "many-to-one"
    description: str = ""

    @property
    def target_table(self) -> str:
        return f"{self.references_schema}.{self.references_table}"


class TableMetadata(BaseModel):
    schema_name: str = Field(alias="schema")
    table: str
    description: str
    columns: list[ColumnMetadata]
    foreign_keys: list[ForeignKeyMetadata] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)

    model_config = {"populate_by_name": True}

    @property
    def qualified_name(self) -> str:
        return f"{self.schema_name}.{self.table}"

    @property
    def primary_keys(self) -> list[str]:
        return [column.name for column in self.columns if column.primary_key]

    @model_validator(mode="after")
    def validate_local_columns(self) -> "TableMetadata":
        names = [column.name for column in self.columns]
        if len(names) != len(set(names)):
            raise ValueError(f"Duplicate columns in {self.qualified_name}")
        unknown_fk_columns = {fk.column for fk in self.foreign_keys} - set(names)
        if unknown_fk_columns:
            raise ValueError(
                f"Foreign keys use missing columns in {self.qualified_name}: "
                f"{sorted(unknown_fk_columns)}"
            )
        return self


class MetadataCatalog(BaseModel):
    version: str
    domain: str
    tables: list[TableMetadata]


class SourceRecord(BaseModel):
    qualified_name: str
    score: float | None = None
    excerpt: str = ""


class GuardrailResult(BaseModel):
    allowed: bool
    reason: str | None = None
    safe_message: str | None = None
