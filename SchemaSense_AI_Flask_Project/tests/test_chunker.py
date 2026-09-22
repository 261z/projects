from src.chunker import table_to_document
from src.metadata_loader import table_map


def test_flights_chunk_contains_keys_and_relationships():
    flight = table_map()["aviation.flights"]
    document = table_to_document(flight)
    assert "Qualified name: aviation.flights" in document
    assert "flight_id" in document
    assert "PRIMARY KEY" in document
    assert "aviation.airports.airport_id" in document

