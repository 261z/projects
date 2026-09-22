from src.metadata_loader import load_catalog


if __name__ == "__main__":
    catalog = load_catalog()
    relationship_count = sum(len(table.foreign_keys) for table in catalog.tables)
    print(
        f"Valid metadata: {len(catalog.tables)} tables and "
        f"{relationship_count} foreign-key relationships."
    )

