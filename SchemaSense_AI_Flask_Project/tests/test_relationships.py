from src.relationship_graph import get_relationship_subgraph


def test_booking_relationships_are_expanded():
    result = get_relationship_subgraph(["booking.bookings"], depth=1)
    assert "booking.passengers" in result["tables"]
    assert "aviation.flights" in result["tables"]
    assert len(result["relationships"]) >= 2


def test_unqualified_unique_name_is_resolved():
    result = get_relationship_subgraph(["uld_assignment"], depth=0)
    assert "operations.uld_assignment" in result["tables"]
    assert not result["unknown_tables"]


def test_unknown_table_is_reported():
    result = get_relationship_subgraph(["made_up_table"], depth=1)
    assert result["unknown_tables"] == ["made_up_table"]

