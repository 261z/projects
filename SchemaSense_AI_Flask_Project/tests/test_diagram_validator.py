import pytest

from src.diagram_validator import build_validated_mermaid


def test_booking_diagram_contains_verified_entities():
    result = build_validated_mermaid(
        ["booking.passengers", "booking.bookings", "aviation.flights"]
    )
    assert result["validated"] is True
    assert "BOOKING__PASSENGERS" in result["mermaid"]
    assert "BOOKING__BOOKINGS" in result["mermaid"]
    assert "AVIATION__FLIGHTS" in result["mermaid"]


def test_unknown_table_is_rejected():
    with pytest.raises(ValueError, match="Unknown tables"):
        build_validated_mermaid(["aviation.flights", "aviation.crew"])

