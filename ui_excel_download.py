import streamlit as st

from api import fetch_all_flights
from utils import date_range
from config import TARGET_TERMINAL_MAP, PASSENGER_TERMINALS, SHEET_ORDER, TERMINAL_MAP
from excel_export import create_excel_file, file_to_bytes_io

def render(tab, today, min_date, max_date):
    with tab:
        st.caption(f"조회 가능 범위: {min_date} ~ {max_date} (오늘 기준 -3일 ~ +6일)")

        terminal_column, start_column, end_column = st.columns(3)
        with terminal_column:
            target_terminal = st.selectbox("터미널", ("T1", "Con", "T2"))
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
            target_terminal_key_set = {TARGET_TERMINAL_MAP.get(target_terminal)}
            terminal_key_set = set(TERMINAL_MAP.keys())
            terminal_items = {terminal_id: [] for terminal_id in terminal_key_set}
            print(terminal_items)
            for item in departures:
                scheduled = str(item.get("scheduled_datetime") or "")[:8]
                if scheduled < start_date_string or scheduled > end_date_string:
                    continue
                terminal_id = item.get("terminal_id", "")
                if terminal_id in target_terminal_key_set:
                    terminal_items[terminal_id].append((item, "D"))
            for item in arrivals:
                scheduled = str(item.get("scheduled_datetime") or "")[:8]
                if scheduled < start_date_string or scheduled > end_date_string:
                    continue
                terminal_id = item.get("terminal_id", "")
                if terminal_id in target_terminal_key_set:
                    terminal_items[terminal_id].append((item, "A"))

            if start_date_string == end_date_string:
                filename = f"인천공항 운항현황 PBB_MT ({start_date_string}).xlsx"
            else:
                filename = f"인천공항 운항현황 PBB_MT ({start_date_string}_{end_date_string}).xlsx"

            total = sum(len(value) for value in terminal_items.values())
            st.success(f"총 {total}건 조회 완료")

            for sheet_name, terminal_id in TARGET_TERMINAL_MAP.items():
                st.write(f"{sheet_name}: {len(terminal_items[terminal_id])}건")

            st.download_button(
                label="📥 엑셀 다운로드",
                data=file_to_bytes_io(create_excel_file(terminal_items)),
                file_name=filename,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
