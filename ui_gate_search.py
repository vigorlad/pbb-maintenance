
import streamlit as st
from datetime import datetime

from models import FlightType
from services import GateFlight, fetch_gate_flights, filter_future_flights
from utils import format_hhmm
from config import KST


def _color(flight_type: FlightType) -> str:
    return "#1e3a5f" if flight_type is FlightType.ARRIVAL else "#5f1e3a"


def _background(flight_type: FlightType) -> str:
    if flight_type is FlightType.ARRIVAL:
        return "linear-gradient(135deg, #1e3a5f 0%, #2d5986 100%)"
    return "linear-gradient(135deg, #5f1e3a 0%, #862d59 100%)"


def _airport_label(flight_type: FlightType) -> str:
    return "출발지" if flight_type is FlightType.ARRIVAL else "도착지"


def _eta_label(flight_type: FlightType) -> str:
    return "예상 도착(ETA)" if flight_type is FlightType.ARRIVAL else "예상 출발(ETD)"


def _sta_label(flight_type: FlightType) -> str:
    return "계획 도착(STA)" if flight_type is FlightType.ARRIVAL else "계획 출발(STD)"


def _render_flight_row(gf: GateFlight):
    item = gf.item
    ft = gf.flight_type
    display_time = format_hhmm(item.actual_datetime or item.scheduled_datetime)

    st.markdown(f"""
    <div class="next-flight-row" style="border-left-color: {_color(ft)};">
        <span class="nf-time">{display_time}</span>
        &nbsp;&nbsp;
        <span class="nf-info">
            <span class="nf-label">출도착</span> {ft.emoji_label}
            &nbsp;|&nbsp;
            <span class="nf-label">편명</span> {item.flight_number or "-"}
            &nbsp;|&nbsp;
            <span class="nf-label">{_airport_label(ft)}</span> {item.airport_name or "-"}
            &nbsp;|&nbsp;
            <span class="nf-label">상태</span> {item.remark or "-"}
            &nbsp;|&nbsp;
            <span class="nf-label">기종</span> {item.aircraft_type or "-"}
        </span>
    </div>
    """, unsafe_allow_html=True)


def _render_main_card(gf: GateFlight, gate: str):
    item = gf.item
    ft = gf.flight_type
    eta = format_hhmm(item.actual_datetime)
    sta = format_hhmm(item.scheduled_datetime)
    display_time = eta if eta != "-" else sta

    st.markdown(f"""
    <div class="flight-card" style="background: {_background(ft)};">
        <div class="label">게이트 {gate} · 다음 {ft.emoji_label}</div>
        <h2>{item.flight_number or "-"}</h2>
        <div class="time-big">{display_time}</div>
        <div class="label">{_eta_label(ft)}</div>
        <div class="value">{eta}</div>
        <div class="label">{_sta_label(ft)}</div>
        <div class="value">{sta}</div>
        <div class="label">{_airport_label(ft)}</div>
        <div class="value">{item.airport_name or "-"}</div>
        <div class="label">기종</div>
        <div class="value">{item.aircraft_type or "-"}</div>
        <span class="status-badge">{item.remark or "-"}</span>
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
                with st.spinner("운항 데이터 조회 중..."):
                    gate_flights, elapsed = fetch_gate_flights(
                        search_date.strftime("%Y%m%d"),
                        gate_value,
                        search_time.strftime("%H%M"),
                    )

                st.caption(f"조회 소요시간: {elapsed:.2f}초")

                if not gate_flights:
                    st.error(f"게이트 **{gate_value}** 에 배정된 운항편이 없습니다.")
                else:
                    cutoff = datetime.combine(search_date, search_time).replace(tzinfo=KST)
                    future = filter_future_flights(gate_flights, cutoff)

                    if not future:
                        st.info(f"게이트 **{gate_value}** 에 기준 시간 이후 운항편이 없습니다.")
                        st.markdown(f"**{search_date.strftime('%Y-%m-%d')} 해당 게이트 전체 현황:**")
                        gate_flights.sort(key=lambda gf: gf.item.scheduled_datetime)
                        for gf in gate_flights:
                            _render_flight_row(gf)
                    else:
                        _render_main_card(future[0], gate_value)

                        if len(future) > 1:
                            st.markdown(f"**이후 운항 예정 ({len(future) - 1}건)**")
                            for gf in future[1:]:
                                _render_flight_row(gf)

        st.markdown(
            '<div class="gate-caption">게이트 번호 숫자로만 검색하세요</div>',
            unsafe_allow_html=True,
        )
