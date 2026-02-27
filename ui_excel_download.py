import streamlit as st

from api import fetch_all_flights
from utils import date_range
from config import PASSENGER_TERMINALS, SHEET_ORDER
from excel_export import create_excel_file, file_to_bytes_io

def render(tab, today, min_date, max_date):
    with tab:
        st.caption(f"조회 가능 범위: {min_date} ~ {max_date} (오늘 기준 -3일 ~ +6일)")

        start_column, end_column = st.columns(2)
        with start_column:
            start_date = st.date_input(
                "시작일", value=today, min_value=min_date, max_value=max_date
            )
        with end_column:
            end_date = st.date_input(
                "종료일", value=today, min_value=min_date, max_value=max_date
            )

        if start_date > end_date:
            st.error("시작일이 종료일보다 클 수 없습니다.")
            st.stop()

        if st.button("조회 및 엑셀 생성", type="primary", key="excel_gen"):
            start_date_string = start_date.strftime("%Y%m%d")
            end_date_string = end_date.strftime("%Y%m%d")
            dates = date_range(start_date_string, end_date_string)

            departures = []
            arrivals = []

            with st.status(f"{len(dates)}일간 데이터 조회 중...", expanded=True) as status:
                for date_string in dates:
                    st.write(f"📅 {date_string} 출발편 조회 중...")
                    departures.extend(fetch_all_flights("getFltDeparturesDeOdp", date_string))
                    st.write(f"📅 {date_string} 도착편 조회 중...")
                    arrivals.extend(fetch_all_flights("getFltArrivalsDeOdp", date_string))
                status.update(label="조회 완료!", state="complete")

            terminal_items = {terminal_id: [] for terminal_id in PASSENGER_TERMINALS}
            for item in departures:
                terminal_id = item.get("terminal_id", "")
                if terminal_id in PASSENGER_TERMINALS:
                    terminal_items[terminal_id].append((item, "D"))
            for item in arrivals:
                terminal_id = item.get("terminal_id", "")
                if terminal_id in PASSENGER_TERMINALS:
                    terminal_items[terminal_id].append((item, "A"))

            if start_date_string == end_date_string:
                filename = f"인천공항 운항현황 PBB_MT ({start_date_string}).xlsx"
            else:
                filename = f"인천공항 운항현황 PBB_MT ({start_date_string}_{end_date_string}).xlsx"

            total = sum(len(value) for value in terminal_items.values())
            st.success(f"총 {total}건 조회 완료 (출발 {len(departures)}건, 도착 {len(arrivals)}건)")

            for terminal_id, sheet_name in SHEET_ORDER:
                st.write(f"{sheet_name}: {len(terminal_items[terminal_id])}건")

            st.download_button(
                label="📥 엑셀 다운로드",
                data=file_to_bytes_io(create_excel_file(terminal_items)),
                file_name=filename,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
