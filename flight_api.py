from __future__ import annotations

from typing import Final, TypeAlias

import requests

import config
from models import FlightItem, FlightType

_session = requests.Session()
_session.headers["User-Agent"] = "Mozilla/5.0 (compatible; PBB-Maintenance/1.0)"

JsonValue: TypeAlias = (
    str | int | float | bool | None | list["JsonValue"] | dict[str, "JsonValue"]
)
JsonObject: TypeAlias = dict[str, JsonValue]

_REQUEST_TIMEOUT: Final = (5, 15)
_REQUEST_ATTEMPTS: Final = 2


class FlightApiError(RuntimeError):
    pass


class FlightApiTimeoutError(FlightApiError):
    def __str__(self) -> str:
        return "공공데이터포털 응답이 지연되고 있습니다. 잠시 후 다시 시도해주세요."


class FlightApiResponseError(FlightApiError):
    def __init__(self, code: str, message: str) -> None:
        self.code = code
        self.message = message
        super().__init__(f"공공데이터포털 오류 ({code}): {message}")


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


def _extract_body(data: JsonValue) -> JsonObject:
    if not isinstance(data, dict):
        raise FlightApiResponseError("INVALID_RESPONSE", "응답 형식을 확인할 수 없습니다.")

    gateway_response = data.get("OpenAPI_ServiceResponse")
    if isinstance(gateway_response, dict):
        gateway_header = gateway_response.get("cmmMsgHeader", {})
        if isinstance(gateway_header, dict):
            code = str(gateway_header.get("returnReasonCode") or "UNKNOWN")
            message = str(
                gateway_header.get("returnAuthMsg")
                or gateway_header.get("errMsg")
                or "알 수 없는 제공사 오류"
            )
            raise FlightApiResponseError(code, message)

    api_response = data.get("response")
    if not isinstance(api_response, dict):
        raise FlightApiResponseError("INVALID_RESPONSE", "응답 본문을 확인할 수 없습니다.")

    header = api_response.get("header", {})
    if isinstance(header, dict):
        code = str(header.get("resultCode") or "00")
        if code != "00":
            message = str(header.get("resultMsg") or "알 수 없는 제공사 오류")
            raise FlightApiResponseError(code, message)

    body = api_response.get("body")
    if not isinstance(body, dict):
        raise FlightApiResponseError("INVALID_RESPONSE", "응답 본문을 확인할 수 없습니다.")
    return body


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

        response = None
        last_timeout = None
        for _ in range(_REQUEST_ATTEMPTS):
            try:
                response = _session.get(url, params=params, timeout=_REQUEST_TIMEOUT)
                break
            except requests.exceptions.Timeout as exc:
                last_timeout = exc
            except requests.exceptions.RequestException as exc:
                raise FlightApiError(
                    "공공데이터포털에 연결할 수 없습니다. 잠시 후 다시 시도해주세요."
                ) from exc
        if response is None:
            raise FlightApiTimeoutError() from last_timeout

        try:
            data = response.json()
        except requests.exceptions.JSONDecodeError as exc:
            raise FlightApiResponseError(
                f"HTTP_{response.status_code}", "제공사 응답을 해석할 수 없습니다."
            ) from exc

        body = _extract_body(data)
        try:
            response.raise_for_status()
        except requests.exceptions.HTTPError as exc:
            raise FlightApiResponseError(
                f"HTTP_{response.status_code}", "HTTP 요청이 실패했습니다."
            ) from exc

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
