from src.config import get_settings
from src.metadata_loader import get_catalog
from src.pinecone_store import MetadataVectorStore


if __name__ == "__main__":
    settings = get_settings()
    settings.require_runtime_keys()
    catalog = get_catalog()
    count = MetadataVectorStore(settings).upsert_tables(catalog.tables)
    print(
        f"Upserted {count} table documents to index "
        f"'{settings.pinecone_index_name}', namespace '{settings.pinecone_namespace}'."
    )

