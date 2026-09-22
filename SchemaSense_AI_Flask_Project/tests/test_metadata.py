from src.metadata_loader import load_catalog, table_map


def test_catalog_has_expected_tables_and_relationships():
    catalog = load_catalog()
    relationships = sum(len(table.foreign_keys) for table in catalog.tables)
    assert len(catalog.tables) == 10
    assert relationships == 11


def test_expected_domains_exist():
    tables = table_map(load_catalog())
    assert "aviation.flights" in tables
    assert "booking.bookings" in tables
    assert "operations.uld_assignment" in tables


def test_column_lengths_precision_and_scale_are_available():
    tables = table_map(load_catalog())
    flight_number = next(
        column for column in tables["aviation.flights"].columns
        if column.name == "flight_number"
    )
    bag_weight = next(
        column for column in tables["operations.baggage"].columns
        if column.name == "weight_kg"
    )
    assert flight_number.character_maximum_length == 10
    assert bag_weight.numeric_precision == 6
    assert bag_weight.numeric_scale == 2
