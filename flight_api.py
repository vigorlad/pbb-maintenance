from __future__ import annotations

import threading

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

import config
from models import FlightItem, FlightType

_thread_local = threading.local()


class FlightApiError(RuntimeError):
    """Sanitized external API failure safe to show in the Streamlit UI."""


def _create_session() -> requests.Session:
    session = requests.Session()
    retry = Retry(
        total=3,
        connect=3,
        read=2,
        status=2,
        backoff_factor=1.5,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=frozenset({"GET"}),
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session


def _get_session() -> requests.Session:
    session = getattr(_thread_local, "session", None)
    if session is None:
        session = _create_session()
        _thread_local.session = session
    return session

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
    if not config.SERVICE_KEY:
        raise FlightApiError(
            "공공데이터포털 서비스키가 설정되지 않았습니다. Streamlit Cloud Secrets에 SERVICE_KEY를 등록해주세요."
        )

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

        try:
            response = _get_session().get(
                url,
                params=params,
                timeout=config.REQUEST_TIMEOUT,
            )
            response.raise_for_status()
            data = response.json()
        except requests.exceptions.ConnectTimeout as exc:
            raise FlightApiError(
                "공공데이터포털 API 연결 시간이 초과되었습니다. 잠시 후 다시 시도해주세요."
            ) from exc
        except requests.exceptions.Timeout as exc:
            raise FlightApiError(
                "공공데이터포털 API 응답 시간이 초과되었습니다. 잠시 후 다시 시도해주세요."
            ) from exc
        except requests.exceptions.HTTPError as exc:
            status_code = exc.response.status_code if exc.response is not None else "unknown"
            if status_code == 401:
                raise FlightApiError(
                    "공공데이터포털 서비스키 인증에 실패했습니다. Streamlit Cloud Secrets의 SERVICE_KEY 값을 확인해주세요."
                ) from exc
            raise FlightApiError(
                f"공공데이터포털 API HTTP 오류가 발생했습니다. 상태코드: {status_code}"
            ) from exc
        except requests.exceptions.RequestException as exc:
            raise FlightApiError(
                "공공데이터포털 API 호출 중 네트워크 오류가 발생했습니다. 잠시 후 다시 시도해주세요."
            ) from exc
        except ValueError as exc:
            raise FlightApiError(
                "공공데이터포털 API 응답을 해석하지 못했습니다. 잠시 후 다시 시도해주세요."
            ) from exc

        if not isinstance(data, dict):
            raise FlightApiError(
                "공공데이터포털 API 응답 형식이 올바르지 않습니다. 잠시 후 다시 시도해주세요."
            )

        response_root = data.get("response", {})
        if not isinstance(response_root, dict):
            raise FlightApiError(
                "공공데이터포털 API 응답 형식이 올바르지 않습니다. 잠시 후 다시 시도해주세요."
            )

        header = response_root.get("header", {})
        result_code = header.get("resultCode")
        if result_code and result_code != "00":
            result_message = header.get("resultMsg") or "알 수 없는 오류"
            raise FlightApiError(
                f"공공데이터포털 API 오류가 발생했습니다. {result_message} ({result_code})"
            )

        body = response_root.get("body", {})
        if not isinstance(body, dict):
            raise FlightApiError(
                "공공데이터포털 API 응답 형식이 올바르지 않습니다. 잠시 후 다시 시도해주세요."
            )

        total_count = body.get("totalCount", 0)
        try:
            total_count = int(total_count)
        except (TypeError, ValueError):
            total_count = 0

        items = body.get("items", [])
        if isinstance(items, dict):
            items = [items]
        elif not isinstance(items, list):
            items = []

        if not items:
            break

        all_items.extend(items)

        if not total_count or len(all_items) >= total_count:
            break

        page_number += 1

    return all_items


def fetch_flights(flight_type: FlightType, search_date: str, **extra_params) -> list[FlightItem]:
    raw_items = _fetch_pages(flight_type.operation, search_date, **extra_params)
    return [_to_flight_item(raw) for raw in raw_items]
