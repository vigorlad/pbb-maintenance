
import requests
import config

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


def _convert_to_internal(raw_item: dict) -> dict:
    return {
        internal_name: raw_item.get(api_name)
        for api_name, internal_name in _API_FIELD_MAP.items()
        if raw_item.get(api_name) is not None
    }


def _fetch_raw_flights(operation: str, search_date: str) -> list[dict]:
    url = f"{config.BASE_URL}/{operation}"
    all_items = []
    page_number = 1

    while True:
        params = {
            "serviceKey": config.SERVICE_KEY,
            "type": "json",
            "numOfRows": config.NUM_OF_ROWS,
            "pageNo": page_number,
            "searchDate": search_date,
        }

        print(f"  [{operation}] 페이지 {page_number} 요청 중...")
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()

        body = data.get("response", {}).get("body", {})
        total_count = body.get("totalCount", 0)
        items = body.get("items", [])

        if not items:
            break

        all_items.extend(items)
        print(f"  [{operation}] 페이지 {page_number}: {len(items)}건 수신 "
              f"(누적 {len(all_items)}/{total_count})")

        if len(all_items) >= total_count:
            break

        page_number += 1

    return all_items


def fetch_all_flights(operation: str, search_date: str) -> list[dict]:
    raw_items = _fetch_raw_flights(operation, search_date)
    return [_convert_to_internal(raw_item) for raw_item in raw_items]
