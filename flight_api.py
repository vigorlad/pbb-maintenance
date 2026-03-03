from __future__ import annotations

import requests

import config
from models import FlightItem, FlightType

_session = requests.Session()

_API_FIELD_MAP = {
    "flightId":          "flight_number",
    "scheduleDatetime":  "scheduled_datetime",
    "estimatedDatetime": "actual_datetime",
    "airport":           "airport_name",
    "aircraftSubtype":   "aircraft_type",
    "aircraftRegNo":     "registration_number",
    "fstandPosition":    "gate_number",
    "remark":            "remark",
    "terminalId":        "terminal_id",
    "codeshare":         "codeshare",
    "typeOfFlight":      "type_of_flight",
}


def _to_flight_item(raw: dict) -> FlightItem:
    kwargs = {}
    for api_name, field_name in _API_FIELD_MAP.items():
        value = raw.get(api_name)
        if value is not None:
            kwargs[field_name] = str(value)
    return FlightItem(**kwargs)


def _fetch_pages(operation: str, search_date: str, **extra_params) -> list[dict]:
    url = f"{config.BASE_URL}/{operation}"
    all_items: list[dict] = []
    page_number = 1

    while True:
        params = {
            "serviceKey": config.SERVICE_KEY,
            "type": "json",
            "numOfRows": config.NUM_OF_ROWS,
            "pageNo": page_number,
            "searchDate": search_date,
            "passengerOrCargo": "P",
            **extra_params,
        }

        response = _session.get(url, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()

        body = data.get("response", {}).get("body", {})
        total_count = body.get("totalCount", 0)
        items = body.get("items", [])

        if not items:
            break

        all_items.extend(items)

        if len(all_items) >= total_count:
            break

        page_number += 1

    return all_items


def fetch_flights(flight_type: FlightType, search_date: str, **extra_params) -> list[FlightItem]:
    raw_items = _fetch_pages(flight_type.operation, search_date, **extra_params)
    return [_to_flight_item(raw) for raw in raw_items]
