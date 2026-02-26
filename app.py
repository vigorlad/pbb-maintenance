import streamlit as st
from io import BytesIO
from datetime import datetime, timedelta, timezone
from openpyxl import Workbook

from airflight_excel import (
    fetch_all_flights, write_sheet, date_range, fmt_time,
    PASSENGER_TERMINALS, SERVICE_KEY,
)
import airflight_excel

# st.secrets에 SERVICE_KEY가 있으면 덮어쓰기
if "SERVICE_KEY" in st.secrets:
    airflight_excel.SERVICE_KEY = st.secrets["SERVICE_KEY"]

st.set_page_config(
    page_title="인천공항 운항현황",
    page_icon="✈️",
    layout="wide",
)

# ── 모바일 친화적 CSS ─────────────────────────────────────
st.markdown("""
<style>
    /* 모바일 반응형 */
    @media (max-width: 768px) {
        .block-container {
            padding: 1rem 0.8rem !important;
        }
        .stTabs [data-baseweb="tab-list"] {
            gap: 0;
        }
        .stTabs [data-baseweb="tab"] {
            padding: 12px 16px;
            font-size: 1rem;
        }
    }

    /* 버튼 크기 확대 */
    .stButton > button {
        width: 100%;
        padding: 0.75rem 1.5rem;
        font-size: 1.1rem;
        font-weight: 600;
        border-radius: 12px;
    }

    /* 입력 필드 크기 */
    .stTextInput > div > div > input {
        font-size: 1.2rem;
        padding: 0.75rem;
        border-radius: 10px;
    }

    /* 결과 카드 스타일 */
    .flight-card {
        background: linear-gradient(135deg, #1e3a5f 0%, #2d5986 100%);
        border-radius: 16px;
        padding: 1.5rem;
        color: white;
        margin: 1rem 0;
        box-shadow: 0 4px 15px rgba(0,0,0,0.15);
    }
    .flight-card h2 {
        margin: 0 0 0.3rem 0;
        font-size: 1.6rem;
        color: #ffffff;
    }
    .flight-card .time-big {
        font-size: 3rem;
        font-weight: 700;
        color: #4dd0e1;
        line-height: 1.1;
        margin: 0.5rem 0;
    }
    .flight-card .label {
        font-size: 0.85rem;
        color: #90caf9;
        margin-bottom: 2px;
    }
    .flight-card .value {
        font-size: 1.1rem;
        color: #ffffff;
        margin-bottom: 0.6rem;
    }
    .flight-card .status-badge {
        display: inline-block;
        background: rgba(255,255,255,0.2);
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.9rem;
    }

    /* 추가 편 리스트 */
    .next-flight-row {
        background: #f8f9fa;
        border-radius: 10px;
        padding: 0.8rem 1rem;
        margin: 0.4rem 0;
        border-left: 4px solid #1e3a5f;
    }
    .next-flight-row .nf-time {
        font-size: 1.3rem;
        font-weight: 700;
        color: #1e3a5f;
    }
    .next-flight-row .nf-info {
        font-size: 0.9rem;
        color: #555;
    }

    /* 탭 스타일 */
    .stTabs [data-baseweb="tab-list"] {
        background: #f0f2f6;
        border-radius: 12px;
        padding: 4px;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 10px;
        font-weight: 600;
    }

    /* 캡션 스타일 */
    .gate-caption {
        text-align: center;
        color: #888;
        font-size: 0.85rem;
        margin-top: 0.5rem;
    }
</style>
""", unsafe_allow_html=True)

st.markdown(
    '<h1><a href="/" target="_self" style="text-decoration:none;color:inherit;">✈️ 인천공항 운항현황</a></h1>',
    unsafe_allow_html=True,
)

KST = timezone(timedelta(hours=9))
today = datetime.now(KST).date()
now = datetime.now(KST)
min_date = today + timedelta(days=-3)
max_date = today + timedelta(days=6)

tab1, tab2 = st.tabs(["🛬 게이트 도착 조회", "📊 엑셀 다운로드"])

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 탭1: 게이트 도착 조회
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
with tab1:
    st.markdown(f"현재: **{now.strftime('%Y-%m-%d %H:%M')}** (KST)")

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

    if st.button("🔍 조회", type="primary", key="gate_search"):
        if not gate_input.strip():
            st.warning("게이트 번호를 입력해주세요.")
        else:
            gate_query = gate_input.strip().upper()
            search_date_str = search_date.strftime("%Y%m%d")

            with st.spinner("운항 데이터 조회 중..."):
                arrivals = fetch_all_flights("getFltArrivalsDeOdp", search_date_str)
                departures = fetch_all_flights("getFltDeparturesDeOdp", search_date_str)

            # 해당 게이트 필터링 (출도착 구분 태그 추가)
            gate_flights = []
            for item in arrivals:
                fstand = (item.get("fstandPosition") or "").strip().upper()
                if fstand == gate_query:
                    item["_flight_type"] = "A"
                    gate_flights.append(item)
            for item in departures:
                fstand = (item.get("fstandPosition") or "").strip().upper()
                if fstand == gate_query:
                    item["_flight_type"] = "D"
                    gate_flights.append(item)

            if not gate_flights:
                st.error(f"게이트 **{gate_query}** 에 배정된 운항편이 없습니다.")
            else:
                # 선택한 날짜+시간 기준으로 필터링
                cutoff = datetime.combine(search_date, search_time).replace(tzinfo=KST)
                future_flights = []
                for item in gate_flights:
                    est = item.get("estimatedDatetime") or ""
                    sch = item.get("scheduleDatetime") or ""
                    time_str = est if est and est != "-" else sch
                    if not time_str or time_str == "-":
                        continue
                    try:
                        flight_dt = datetime.strptime(str(time_str).strip(), "%Y%m%d%H%M").replace(tzinfo=KST)
                        item["_parsed_time"] = flight_dt
                        if flight_dt >= cutoff:
                            future_flights.append(item)
                    except ValueError:
                        continue

                def _format_hhmm(raw):
                    t = fmt_time(str(raw or ""))
                    if len(t) == 4 and t.isdigit():
                        return f"{t[:2]}:{t[2:]}"
                    return t

                def _type_label(ft):
                    return "🛬 도착" if ft == "A" else "🛫 출발"

                def _type_color(ft):
                    return "#1e3a5f" if ft == "A" else "#5f1e3a"

                def _airport_label(ft):
                    return "출발지" if ft == "A" else "도착지"

                def _eta_label(ft):
                    return "예상 도착(ETA)" if ft == "A" else "예상 출발(ETD)"

                def _sta_label(ft):
                    return "계획 도착(STA)" if ft == "A" else "계획 출발(STD)"

                if not future_flights:
                    st.info(f"게이트 **{gate_query}** 에 기준 시간 이후 운항편이 없습니다.")
                    st.markdown(f"**{search_date.strftime('%Y-%m-%d')} 해당 게이트 전체 현황:**")
                    gate_flights.sort(key=lambda x: x.get("scheduleDatetime", "") or "")
                    for item in gate_flights:
                        t = _format_hhmm(item.get("estimatedDatetime") or item.get("scheduleDatetime"))
                        fid = item.get("flightId", "-")
                        rmk = item.get("remark", "-") or "-"
                        ap = item.get("airport", "-") or "-"
                        ft = item.get("_flight_type", "A")
                        st.markdown(f"""
                        <div class="next-flight-row" style="border-left-color: {_type_color(ft)};">
                            <span class="nf-time">{t}</span>
                            &nbsp;&nbsp;
                            <span class="nf-info">{_type_label(ft)} | {fid} | {ap} | {rmk}</span>
                        </div>
                        """, unsafe_allow_html=True)
                else:
                    future_flights.sort(key=lambda x: x["_parsed_time"])
                    nf = future_flights[0]
                    ft = nf.get("_flight_type", "A")

                    est_fmt = _format_hhmm(nf.get("estimatedDatetime"))
                    sch_fmt = _format_hhmm(nf.get("scheduleDatetime"))
                    display_time = est_fmt if est_fmt != "-" else sch_fmt
                    flight_id = nf.get("flightId", "-")
                    airport = nf.get("airport", "-") or "-"
                    aircraft = nf.get("aircraftSubtype", "-") or "-"
                    remark = nf.get("remark", "-") or "-"
                    card_bg = "linear-gradient(135deg, #1e3a5f 0%, #2d5986 100%)" if ft == "A" else "linear-gradient(135deg, #5f1e3a 0%, #862d59 100%)"

                    st.markdown(f"""
                    <div class="flight-card" style="background: {card_bg};">
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

                    # 이후 운항편 리스트
                    if len(future_flights) > 1:
                        st.markdown(f"**이후 운항 예정 ({len(future_flights) - 1}건)**")
                        for item in future_flights[1:]:
                            t = _format_hhmm(item.get("estimatedDatetime") or item.get("scheduleDatetime"))
                            fid = item.get("flightId", "-")
                            ap = item.get("airport", "-") or "-"
                            rmk = item.get("remark", "-") or "-"
                            ift = item.get("_flight_type", "A")
                            st.markdown(f"""
                            <div class="next-flight-row" style="border-left-color: {_type_color(ift)};">
                                <span class="nf-time">{t}</span>
                                &nbsp;&nbsp;
                                <span class="nf-info">{_type_label(ift)} | {fid} | {ap} | {rmk}</span>
                            </div>
                            """, unsafe_allow_html=True)

    st.markdown('<div class="gate-caption">주기장 번호는 공항 게이트 번호와 동일합니다</div>', unsafe_allow_html=True)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 탭2: 엑셀 다운로드 (기존 기능)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
with tab2:
    st.caption(f"조회 가능 범위: {min_date} ~ {max_date} (오늘 기준 -3일 ~ +6일)")

    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("시작일", value=today, min_value=min_date, max_value=max_date)
    with col2:
        end_date = st.date_input("종료일", value=today, min_value=min_date, max_value=max_date)

    if start_date > end_date:
        st.error("시작일이 종료일보다 클 수 없습니다.")
        st.stop()

    if st.button("조회 및 엑셀 생성", type="primary", key="excel_gen"):
        start_str = start_date.strftime("%Y%m%d")
        end_str = end_date.strftime("%Y%m%d")
        dates = date_range(start_str, end_str)

        departures = []
        arrivals = []

        with st.status(f"{len(dates)}일간 데이터 조회 중...", expanded=True) as status:
            for i, d in enumerate(dates):
                st.write(f"📅 {d} 출발편 조회 중...")
                departures.extend(fetch_all_flights("getFltDeparturesDeOdp", d))
                st.write(f"📅 {d} 도착편 조회 중...")
                arrivals.extend(fetch_all_flights("getFltArrivalsDeOdp", d))
            status.update(label="조회 완료!", state="complete")

        # 터미널별 분류
        terminal_items = {tid: [] for tid in PASSENGER_TERMINALS}
        for item in departures:
            tid = item.get("terminalId", "")
            if tid in PASSENGER_TERMINALS:
                terminal_items[tid].append((item, "D"))
        for item in arrivals:
            tid = item.get("terminalId", "")
            if tid in PASSENGER_TERMINALS:
                terminal_items[tid].append((item, "A"))

        # 엑셀 생성
        wb = Workbook()
        wb.remove(wb.active)

        sheet_order = [
            ("P01", "T1"),
            ("P02", "탑승동"),
            ("P03", "T2"),
        ]
        for tid, sheet_name in sheet_order:
            items = terminal_items[tid]
            write_sheet(wb, sheet_name, items)

        # BytesIO에 저장
        output = BytesIO()
        wb.save(output)
        output.seek(0)

        if start_str == end_str:
            filename = f"인천공항_운항현황_{start_str}.xlsx"
        else:
            filename = f"인천공항_운항현황_{start_str}_{end_str}.xlsx"

        # 결과 요약
        total = sum(len(v) for v in terminal_items.values())
        st.success(f"총 {total}건 조회 완료 (출발 {len(departures)}건, 도착 {len(arrivals)}건)")

        for tid, sheet_name in sheet_order:
            st.write(f"  {sheet_name}: {len(terminal_items[tid])}건")

        st.download_button(
            label="📥 엑셀 다운로드",
            data=output,
            file_name=filename,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
