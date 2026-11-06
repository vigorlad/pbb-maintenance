from datetime import datetime

from config import KST
from models import FlightItem, FlightType
from services import _filter_by_gate, filter_future_flights


def _flight(number: str, scheduled: str, estimated: str) -> FlightItem:
    return FlightItem(
        flight_number=number,
        scheduled_datetime=f"20261106{scheduled}",
        actual_datetime=f"20261106{estimated}" if estimated else "",
        gate_number="43",
        codeshare="Master",
    )


def test_delayed_flight_whose_scheduled_time_passed_is_still_upcoming() -> None:
    # Given: 계획 16:45, 예상 18:19로 지연된 도착편과 계획 18:50 출발편
    arrivals = _filter_by_gate([_flight("AA281", "1645", "1819")], "43", FlightType.ARRIVAL)
    departures = _filter_by_gate([_flight("AA280", "1850", "")], "43", FlightType.DEPARTURE)
    cutoff = datetime(2026, 11, 6, 17, 45, tzinfo=KST)

    # When
    future = filter_future_flights(arrivals + departures, cutoff)

    # Then
    assert [gf.item.flight_number for gf in future] == ["AA281", "AA280"]


def test_flight_without_estimated_time_uses_scheduled_time() -> None:
    flights = _filter_by_gate([_flight("SQ605", "2315", "")], "43", FlightType.DEPARTURE)

    assert flights[0].parsed_time == datetime(2026, 11, 6, 23, 15, tzinfo=KST)
