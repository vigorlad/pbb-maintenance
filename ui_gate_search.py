"""
============================================================
ui_gate_search.py - 탭1: 게이트 출도착 조회 UI
============================================================
게이트(주기장) 번호를 입력하면 해당 게이트의 출도착 항공편을 조회합니다.

화면 구성:
  ┌─────────────────────────────────────────┐
  │  [조회 날짜]  [기준 시간]  [게이트 번호]  │  ← 입력 폼
  │              [🔍 조회]                   │  ← 조회 버튼
  ├─────────────────────────────────────────┤
  │  ┌──────────────────────────────────┐   │
  │  │  게이트 230 · 다음 🛬 도착       │   │
  │  │  KE001                          │   │  ← 메인 카드
  │  │  14:30  (크게 표시)              │   │     (가장 가까운 항공편)
  │  │  ETA: 14:30 / STA: 14:20       │   │
  │  └──────────────────────────────────┘   │
  │                                         │
  │  이후 운항 예정 (3건)                    │
  │  ├ 15:20  🛫 출발 | OZ302 | 도쿄       │  ← 후속 리스트
  │  ├ 17:00  🛬 도착 | KE005 | 뉴욕       │
  │  └ 19:30  🛫 출발 | OZ105 | 베이징     │
  └─────────────────────────────────────────┘

동작 흐름:
  1. 날짜/시간/게이트 입력 → 조회 버튼 클릭
  2. 해당 날짜의 도착편 + 출발편 전체 API 호출
  3. 게이트 번호로 필터링 (Master 편만)
  4. 기준 시간 이후의 항공편만 추출
  5. 가장 가까운 편을 카드로, 나머지를 리스트로 표시
============================================================
"""

import streamlit as st
from datetime import datetime

from api import fetch_all_flights
from utils import format_hhmm
from config import KST


# ────────────────────────────────────────────────────────────
# 표시용 헬퍼 함수들
# ────────────────────────────────────────────────────────────
def _type_label(flight_type: str) -> str:
    """출도착 구분을 이모지 포함 라벨로 변환"""
    return "🛬 도착" if flight_type == "A" else "🛫 출발"


def _type_color(flight_type: str) -> str:
    """출도착 구분에 따른 테마 색상 반환 (CSS용)"""
    # 도착: 파란 계열, 출발: 붉은 계열
    return "#1e3a5f" if flight_type == "A" else "#5f1e3a"


def _airport_label(flight_type: str) -> str:
    """도착편이면 '출발지', 출발편이면 '도착지' 라벨"""
    return "출발지" if flight_type == "A" else "도착지"


def _eta_label(flight_type: str) -> str:
    """예상 시각 라벨 (도착편: ETA, 출발편: ETD)"""
    return "예상 도착(ETA)" if flight_type == "A" else "예상 출발(ETD)"


def _sta_label(flight_type: str) -> str:
    """계획 시각 라벨 (도착편: STA, 출발편: STD)"""
    return "계획 도착(STA)" if flight_type == "A" else "계획 출발(STD)"


def _card_background(flight_type: str) -> str:
    """메인 카드의 배경 그라데이션 (도착: 파란색, 출발: 자주색)"""
    if flight_type == "A":
        return "linear-gradient(135deg, #1e3a5f 0%, #2d5986 100%)"
    else:
        return "linear-gradient(135deg, #5f1e3a 0%, #862d59 100%)"


# ────────────────────────────────────────────────────────────
# 데이터 처리 함수들
# ────────────────────────────────────────────────────────────
def _filter_by_gate(flights: list[dict], gate_query: str, flight_type: str) -> list[dict]:
    """
    운항 데이터에서 특정 게이트에 배정된 Master 편만 필터링합니다.

    매개변수:
      flights     : API에서 받은 운항 데이터 리스트
      gate_query  : 조회할 게이트 번호 (대문자, 예: "230", "A10")
      flight_type : "A"(도착) 또는 "D"(출발) - 각 항목에 태그로 추가

    반환값:
      게이트가 일치하는 Master 편 리스트 (각 항목에 _flight_type 키 추가됨)
    """
    result = []
    for item in flights:
        # codeshare가 "Master"가 아닌 항목은 코드쉐어 중복이므로 제외
        if item.get("codeshare") != "Master":
            continue
        # 게이트(주기장) 번호 비교
        fstand = (item.get("fstandPosition") or "").strip().upper()
        if fstand == gate_query:
            item["_flight_type"] = flight_type  # 출도착 구분 태그 추가
            result.append(item)
    return result


def _filter_future_flights(gate_flights: list[dict], cutoff: datetime) -> list[dict]:
    """
    기준 시간(cutoff) 이후의 항공편만 추출합니다.

    각 항공편의 시간은 estimatedDatetime(예상) 또는 scheduleDatetime(계획) 중
    유효한 값을 사용합니다. 파싱된 시간은 _parsed_time 키에 저장됩니다.
    """
    future = []
    for item in gate_flights:
        # 예상 시각을 우선 사용, 없으면 계획 시각 사용
        est = item.get("estimatedDatetime") or ""
        sch = item.get("scheduleDatetime") or ""
        time_str = est if est and est != "-" else sch

        if not time_str or time_str == "-":
            continue

        try:
            flight_dt = datetime.strptime(
                str(time_str).strip(), "%Y%m%d%H%M"
            ).replace(tzinfo=KST)
            item["_parsed_time"] = flight_dt

            # 기준 시간 이후인 항공편만 포함
            if flight_dt >= cutoff:
                future.append(item)
        except ValueError:
            continue

    return future


# ────────────────────────────────────────────────────────────
# UI 렌더링 함수들
# ────────────────────────────────────────────────────────────
def _render_flight_row(item: dict):
    """운항편 한 줄(리스트 행)을 HTML로 렌더링합니다."""
    t = format_hhmm(item.get("estimatedDatetime") or item.get("scheduleDatetime"))
    fid = item.get("flightId", "-")
    ap = item.get("airport", "-") or "-"
    rmk = item.get("remark", "-") or "-"
    ft = item.get("_flight_type", "A")

    st.markdown(f"""
    <div class="next-flight-row" style="border-left-color: {_type_color(ft)};">
        <span class="nf-time">{t}</span>
        &nbsp;&nbsp;
        <span class="nf-info">{_type_label(ft)} | {fid} | {ap} | {rmk}</span>
    </div>
    """, unsafe_allow_html=True)


def _render_main_card(nf: dict, gate_query: str):
    """가장 가까운 항공편을 큰 카드로 렌더링합니다."""
    ft = nf.get("_flight_type", "A")

    est_fmt = format_hhmm(nf.get("estimatedDatetime"))
    sch_fmt = format_hhmm(nf.get("scheduleDatetime"))
    display_time = est_fmt if est_fmt != "-" else sch_fmt

    flight_id = nf.get("flightId", "-")
    airport = nf.get("airport", "-") or "-"
    aircraft = nf.get("aircraftSubtype", "-") or "-"
    remark = nf.get("remark", "-") or "-"

    st.markdown(f"""
    <div class="flight-card" style="background: {_card_background(ft)};">
        <div class="label">게이트 {gate_query} · 다음 {_type_label(ft)}</div>
        <h2>{flight_id}</h2>
        <div class="time-big">{display_time}</div>
        <div class="label">{_eta_label(ft)}</div>
        <div class="value">{est_fmt}</div>
        <div class="label">{_sta_label(ft)}</div>
        <div class="value">{sch_fmt}</div>
        <div class="label">{_airport_label(ft)}</div>
        <div class="value">{airport}</div>
        <div class="label">기종</div>
        <div class="value">{aircraft}</div>
        <span class="status-badge">{remark}</span>
    </div>
    """, unsafe_allow_html=True)


# ────────────────────────────────────────────────────────────
# 메인: 탭1 전체 렌더링
# ────────────────────────────────────────────────────────────
def render(tab, today, now, min_date, max_date):
    """
    탭1(게이트 출도착 조회)의 전체 UI를 렌더링합니다.

    매개변수:
      tab      : Streamlit 탭 컨테이너 (st.tabs()에서 반환)
      today    : 오늘 날짜 (date 객체)
      now      : 현재 시각 (datetime 객체, KST)
      min_date : 조회 가능 최소 날짜
      max_date : 조회 가능 최대 날짜
    """
    with tab:
        # ── 현재 시간 표시 ──
        st.markdown(f"현재: **{now.strftime('%Y-%m-%d %H:%M')}** (KST)")

        # ── 입력 폼: 3열 레이아웃 ──
        gcol1, gcol2, gcol3 = st.columns([1, 1, 1])
        with gcol1:
            search_date = st.date_input(
                "조회 날짜",
                value=today,
                min_value=min_date,
                max_value=max_date,
                key="gate_date",
            )
        with gcol2:
            search_time = st.time_input(
                "기준 시간",
                value=now.time().replace(second=0, microsecond=0),
                key="gate_time",
            )
        with gcol3:
            gate_input = st.text_input(
                "게이트(주기장) 번호",
                placeholder="예: 230, A10 ...",
                key="gate_input",
            )

        # ── 조회 버튼 ──
        if st.button("🔍 조회", type="primary", key="gate_search"):
            if not gate_input.strip():
                st.warning("게이트 번호를 입력해주세요.")
            else:
                gate_query = gate_input.strip().upper()
                search_date_str = search_date.strftime("%Y%m%d")

                # ── API 호출: 도착편 + 출발편 ──
                with st.spinner("운항 데이터 조회 중..."):
                    arrivals = fetch_all_flights("getFltArrivalsDeOdp", search_date_str)
                    departures = fetch_all_flights("getFltDeparturesDeOdp", search_date_str)

                # ── 게이트 기준 필터링 ──
                gate_flights = (
                    _filter_by_gate(arrivals, gate_query, "A") +
                    _filter_by_gate(departures, gate_query, "D")
                )

                if not gate_flights:
                    st.error(f"게이트 **{gate_query}** 에 배정된 운항편이 없습니다.")
                else:
                    # ── 기준 시간 이후 항공편 추출 ──
                    cutoff = datetime.combine(search_date, search_time).replace(tzinfo=KST)
                    future_flights = _filter_future_flights(gate_flights, cutoff)

                    if not future_flights:
                        # 기준 시간 이후 편이 없으면 → 해당 게이트의 전체 편 표시
                        st.info(f"게이트 **{gate_query}** 에 기준 시간 이후 운항편이 없습니다.")
                        st.markdown(f"**{search_date.strftime('%Y-%m-%d')} 해당 게이트 전체 현황:**")
                        gate_flights.sort(key=lambda x: x.get("scheduleDatetime", "") or "")
                        for item in gate_flights:
                            _render_flight_row(item)
                    else:
                        # ── 가장 가까운 항공편을 메인 카드로 ──
                        future_flights.sort(key=lambda x: x["_parsed_time"])
                        _render_main_card(future_flights[0], gate_query)

                        # ── 이후 운항 예정 리스트 ──
                        if len(future_flights) > 1:
                            st.markdown(f"**이후 운항 예정 ({len(future_flights) - 1}건)**")
                            for item in future_flights[1:]:
                                _render_flight_row(item)

        # ── 하단 안내 문구 ──
        st.markdown(
            '<div class="gate-caption">주기장 번호는 공항 게이트 번호와 동일합니다</div>',
            unsafe_allow_html=True,
        )
