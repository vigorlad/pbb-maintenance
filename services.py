from __future__ import annotations

import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from datetime import datetime
from typing import Callable

from config import KST, TERMINALS
from models import FlightItem, FlightType
from flight_api import fetch_flights


@dataclass(slots=True)
class GateFlight:
    item: FlightItem
    flight_type: FlightType
    parsed_time: datetime


@dataclass(slots=True)
class TaggedFlight:
    item: FlightItem
    flight_type: FlightType


# ── Gate Search ──

def fetch_gate_flights(
    search_date: str,
    gate: str,
    search_from: str,
) -> tuple[list[GateFlight], float]:
    start = time.time()

    with ThreadPoolExecutor(max_workers=2) as executor:
        future_arrivals = executor.submit(
            fetch_flights, FlightType.ARRIVAL, search_date, searchFrom=search_from,
        )
        future_departures = executor.submit(
            fetch_flights, FlightType.DEPARTURE, search_date, searchFrom=search_from,
        )
        arrivals = future_arrivals.result()
        departures = future_departures.result()

    elapsed = time.time() - start
    print(f"[게이트 조회] API 병렬 소요시간: {elapsed:.2f}초")

    result = (
        _filter_by_gate(arrivals, gate, FlightType.ARRIVAL)
        + _filter_by_gate(departures, gate, FlightType.DEPARTURE)
    )
    return result, elapsed


def filter_future_flights(
    gate_flights: list[GateFlight],
    cutoff: datetime,
) -> list[GateFlight]:
    future = [gf for gf in gate_flights if gf.parsed_time >= cutoff]
    future.sort(key=lambda gf: gf.parsed_time)
    return future


def _filter_by_gate(
    flights: list[FlightItem],
    gate: str,
    flight_type: FlightType,
) -> list[GateFlight]:
    result: list[GateFlight] = []
    for item in flights:
        if not item.is_master:
            continue
        if item.gate_number.strip().upper() != gate:
            continue
        parsed = _parse_scheduled(item.scheduled_datetime)
        if parsed is None:
            continue
        result.append(GateFlight(item=item, flight_type=flight_type, parsed_time=parsed))
    return result


def _parse_scheduled(raw: str) -> datetime | None:
    if not raw or raw == "-":
        return None
    try:
        return datetime.strptime(raw.strip(), "%Y%m%d%H%M").replace(tzinfo=KST)
    except ValueError:
        return None


# ── Excel Download ──

def fetch_excel_data(
    dates: list[str],
    target_terminal_id: str,
    progress_callback: Callable[[str, str], None] | None = None,
) -> dict[str, list[TaggedFlight]]:
    terminal_items: dict[str, list[TaggedFlight]] = {t.terminal_id: [] for t in TERMINALS}

    for date_string in dates:
        if progress_callback:
            progress_callback(date_string, "departure")
        departures = fetch_flights(FlightType.DEPARTURE, date_string)

        if progress_callback:
            progress_callback(date_string, "arrival")
        arrivals = fetch_flights(FlightType.ARRIVAL, date_string)

        for flight_type, flights in ((FlightType.DEPARTURE, departures), (FlightType.ARRIVAL, arrivals)):
            for item in flights:
                if item.terminal_id == target_terminal_id:
                    terminal_items[item.terminal_id].append(
                        TaggedFlight(item=item, flight_type=flight_type)
                    )

    return terminal_items
