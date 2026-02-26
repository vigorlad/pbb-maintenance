import streamlit as st

from api import fetch_all_flights
from utils import date_range
from config import PASSENGER_TERMINALS, SHEET_ORDER
from excel_export import create_excel_file, file_to_bytes_io

def render(tab, today, min_date, max_date):
    with tab:
        st.caption(f"조회 가능 범위: {min_date} ~ {max_date} (오늘 기준 -3일 ~ +6일)")

        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input(
                "시작일", value=today, min_value=min_date, max_value=max_date
            )
        with col2:
            end_date = st.date_input(
                "종료일", value=today, min_value=min_date, max_value=max_date
            )

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
                for d in dates:
                    st.write(f"📅 {d} 출발편 조회 중...")
                    departures.extend(fetch_all_flights("getFltDeparturesDeOdp", d))
                    st.write(f"📅 {d} 도착편 조회 중...")
                    arrivals.extend(fetch_all_flights("getFltArrivalsDeOdp", d))
                status.update(label="조회 완료!", state="complete")

            terminal_items = {tid: [] for tid in PASSENGER_TERMINALS}
            for item in departures:
                tid = item.get("terminalId", "")
                if tid in PASSENGER_TERMINALS:
                    terminal_items[tid].append((item, "D"))
            for item in arrivals:
                tid = item.get("terminalId", "")
                if tid in PASSENGER_TERMINALS:
                    terminal_items[tid].append((item, "A"))

            if start_str == end_str:
                filename = f"인천공항 운항현황 PBB_MT ({start_str}).xlsx"
            else:
                filename = f"인천공항 운항현황 PBB_MT ({start_str}_{end_str}).xlsx"

            total = sum(len(v) for v in terminal_items.values())
            st.success(f"총 {total}건 조회 완료 (출발 {len(departures)}건, 도착 {len(arrivals)}건)")

            for tid, sheet_name in SHEET_ORDER:
                st.write(f"{sheet_name}: {len(terminal_items[tid])}건")

            st.download_button(
                label="📥 엑셀 다운로드",
                data=file_to_bytes_io(create_excel_file(terminal_items)),
                file_name=filename,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
