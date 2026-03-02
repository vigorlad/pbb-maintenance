
import streamlit as st
from datetime import datetime

from api import fetch_all_flights
from utils import format_hhmm
from config import KST


def _flight_type_label(flight_type: str) -> str:
    """출도착 구분을 이모지 포함 라벨로 변환"""
    return "🛬 도착" if flight_type == "A" else "🛫 출발"


def _flight_type_color(flight_type: str) -> str:
    """출도착 구분에 따른 테마 색상 반환 (CSS용)"""
    return "#1e3a5f" if flight_type == "A" else "#5f1e3a"


def _airport_label(flight_type: str) -> str:
    """도착편이면 '출발지', 출발편이면 '도착지' 라벨"""
    return "출발지" if flight_type == "A" else "도착지"


def _estimated_time_label(flight_type: str) -> str:
    """예상 시각 라벨 (도착편: ETA, 출발편: ETD)"""
    return "예상 도착(ETA)" if flight_type == "A" else "예상 출발(ETD)"


def _scheduled_time_label(flight_type: str) -> str:
    """계획 시각 라벨 (도착편: STA, 출발편: STD)"""
    return "계획 도착(STA)" if flight_type == "A" else "계획 출발(STD)"


def _card_background(flight_type: str) -> str:
    """메인 카드의 배경 그라데이션 (도착: 파란색, 출발: 자주색)"""
    if flight_type == "A":
        return "linear-gradient(135deg, #1e3a5f 0%, #2d5986 100%)"
    else:
        return "linear-gradient(135deg, #5f1e3a 0%, #862d59 100%)"


def _filter_by_gate(flights: list[dict], gate_query: str, flight_type: str) -> list[dict]:
    result = []
    for item in flights:
        if item.get("codeshare") != "Master":
            continue
        gate_number = (item.get("gate_number") or "").strip().upper()
        if gate_number == gate_query:
            item["_flight_type"] = flight_type
            result.append(item)
    return result


def _filter_future_flights(gate_flights: list[dict], cutoff: datetime) -> list[dict]:
    future_flights = []
    for item in gate_flights:
        scheduled_datetime = item.get("scheduled_datetime") or ""

        if not scheduled_datetime or scheduled_datetime == "-":
            continue

        try:
            parsed_flight_time = datetime.strptime(
                str(scheduled_datetime).strip(), "%Y%m%d%H%M"
            ).replace(tzinfo=KST)
            item["_parsed_time"] = parsed_flight_time

            if parsed_flight_time >= cutoff:
                future_flights.append(item)
        except ValueError:
            continue

    return future_flights


def _render_flight_row(item: dict):
    display_time = format_hhmm(item.get("actual_datetime") or item.get("scheduled_datetime"))
    flight_number = item.get("flight_number", "-")
    airport_name = item.get("airport_name", "-") or "-"
    remark = item.get("remark", "-") or "-"
    aircraft_type = item.get("aircraft_type", "-") or "-"
    flight_type = item.get("_flight_type", "A")

    st.markdown(f"""
    <div class="next-flight-row" style="border-left-color: {_flight_type_color(flight_type)};">
        <span class="nf-time">{display_time}</span>
        &nbsp;&nbsp;
        <span class="nf-info">
            <span class="nf-label">출도착</span> {_flight_type_label(flight_type)}
            &nbsp;|&nbsp;
            <span class="nf-label">편명</span> {flight_number}
            &nbsp;|&nbsp;
            <span class="nf-label">{_airport_label(flight_type)}</span> {airport_name}
            &nbsp;|&nbsp;
            <span class="nf-label">상태</span> {remark}
            &nbsp;|&nbsp;
            <span class="nf-label">기종</span> {aircraft_type}
        </span>
    </div>
    """, unsafe_allow_html=True)


def _render_main_card(nearest_flight: dict, gate_query: str):
    flight_type = nearest_flight.get("_flight_type", "A")

    estimated_time_formatted = format_hhmm(nearest_flight.get("actual_datetime"))
    scheduled_time_formatted = format_hhmm(nearest_flight.get("scheduled_datetime"))
    display_time = estimated_time_formatted if estimated_time_formatted != "-" else scheduled_time_formatted

    flight_number = nearest_flight.get("flight_number", "-")
    airport_name = nearest_flight.get("airport_name", "-") or "-"
    aircraft_type = nearest_flight.get("aircraft_type", "-") or "-"
    remark = nearest_flight.get("remark", "-") or "-"

    st.markdown(f"""
    <div class="flight-card" style="background: {_card_background(flight_type)};">
        <div class="label">게이트 {gate_query} · 다음 {_flight_type_label(flight_type)}</div>
        <h2>{flight_number}</h2>
        <div class="time-big">{display_time}</div>
        <div class="label">{_estimated_time_label(flight_type)}</div>
        <div class="value">{estimated_time_formatted}</div>
        <div class="label">{_scheduled_time_label(flight_type)}</div>
        <div class="value">{scheduled_time_formatted}</div>
        <div class="label">{_airport_label(flight_type)}</div>
        <div class="value">{airport_name}</div>
        <div class="label">기종</div>
        <div class="value">{aircraft_type}</div>
        <span class="status-badge">{remark}</span>
    </div>
    """, unsafe_allow_html=True)


def render(tab, today, now, min_date, max_date):
    with tab:
        st.markdown(f"현재: **{now.strftime('%Y-%m-%d %H:%M')}** (KST)")

        date_column, time_column, gate_column = st.columns([1, 1, 1])
        with date_column:
            search_date = st.date_input(
                "조회 날짜",
                value=today,
                min_value=min_date,
                max_value=max_date,
                key="gate_date",
            )
        with time_column:
            search_time = st.time_input(
                "기준 시간",
                value=now.time().replace(second=0, microsecond=0),
                key="gate_time",
            )
        with gate_column:
            gate_input = st.text_input(
                "게이트(주기장) 번호",
                placeholder="예: 43, 123 ...",
                key="gate_input",
            )

        gate_value = gate_input.strip()

        if st.button("🔍 조회", type="primary", key="gate_search"):
            if not gate_value:
                st.warning("게이트 번호를 입력해주세요.")
            elif not gate_value.isdigit():
                st.warning("게이트 번호는 숫자만 입력 가능합니다.")
            else:
                gate_query = gate_value
                search_date_string = search_date.strftime("%Y%m%d")

                with st.spinner("운항 데이터 조회 중..."):
                    arrivals = fetch_all_flights("getFltArrivalsDeOdp", search_date_string)
                    departures = fetch_all_flights("getFltDeparturesDeOdp", search_date_string)

                gate_flights = (
                    _filter_by_gate(arrivals, gate_query, "A") +
                    _filter_by_gate(departures, gate_query, "D")
                )

                if not gate_flights:
                    st.error(f"게이트 **{gate_query}** 에 배정된 운항편이 없습니다.")
                else:
                    cutoff = datetime.combine(search_date, search_time).replace(tzinfo=KST)
                    future_flights = _filter_future_flights(gate_flights, cutoff)

                    if not future_flights:
                        st.info(f"게이트 **{gate_query}** 에 기준 시간 이후 운항편이 없습니다.")
                        st.markdown(f"**{search_date.strftime('%Y-%m-%d')} 해당 게이트 전체 현황:**")
                        gate_flights.sort(key=lambda x: x.get("scheduled_datetime", "") or "")
                        for item in gate_flights:
                            _render_flight_row(item)
                    else:
                        future_flights.sort(key=lambda x: x["_parsed_time"])
                        _render_main_card(future_flights[0], gate_query)

                        if len(future_flights) > 1:
                            st.markdown(f"**이후 운항 예정 ({len(future_flights) - 1}건)**")
                            for item in future_flights[1:]:
                                _render_flight_row(item)

        st.markdown(
            '<div class="gate-caption">게이트 번호 숫자로만 검색하세요</div>',
            unsafe_allow_html=True,
        )
