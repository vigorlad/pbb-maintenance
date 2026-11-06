import pytest

import services
from excel_export import create_excel_file
from models import FlightItem, FlightType


def _flights(flight_type: FlightType, search_date: str) -> list[FlightItem]:
    return [
        FlightItem(flight_number="KE001", scheduled_datetime=f"{search_date}0900",
                   terminal_id="P03", codeshare="Master"),
        FlightItem(flight_number="DL001", scheduled_datetime=f"{search_date}0900",
                   terminal_id="P03", codeshare="Slave"),
        FlightItem(flight_number="OZ001", scheduled_datetime=f"{search_date}1000",
                   terminal_id="P01", codeshare="Master"),
    ]


def test_excel_data_contains_only_master_flights_of_selected_terminal(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Given
    monkeypatch.setattr(services, "fetch_flights", _flights)

    # When
    terminal_items = services.fetch_excel_data(["20260818"], "P03")

    # Then
    assert list(terminal_items) == ["P03"]
    assert [tf.item.flight_number for tf in terminal_items["P03"]] == ["KE001", "KE001"]


def test_workbook_has_one_sheet_whose_rows_match_reported_count(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Given
    monkeypatch.setattr(services, "fetch_flights", _flights)
    terminal_items = services.fetch_excel_data(["20260818"], "P03")
    reported_count = sum(len(v) for v in terminal_items.values())

    # When
    workbook = create_excel_file(terminal_items)

    # Then
    assert workbook.sheetnames == ["T2"]
    assert workbook["T2"].max_row - 1 == reported_count


def test_workbook_keeps_selected_sheet_when_no_flights(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(services, "fetch_flights", lambda *args, **kwargs: [])

    workbook = create_excel_file(services.fetch_excel_data(["20260818"], "P02"))

    assert workbook.sheetnames == ["Con"]
