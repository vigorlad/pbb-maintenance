import streamlit as st

from config import TERMINALS
from services import fetch_excel_data
from utils import date_range
from excel_export import create_excel_file, file_to_bytes_io


def render(tab, today, min_date, max_date):
    with tab:
        st.caption(f"조회 가능 범위: {min_date} ~ {max_date} (오늘 기준 -3일 ~ +6일)")

        terminal_column, start_column, end_column = st.columns(3)
        with terminal_column:
            terminal_names = [t.name for t in TERMINALS]
            target_terminal = st.selectbox("터미널", terminal_names)
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

            terminal_id_map = {t.name: t.terminal_id for t in TERMINALS}
            target_terminal_id = terminal_id_map[target_terminal]

            with st.status(f"{len(dates)}일간 데이터 조회 중...", expanded=True) as status:
                def on_progress(date_string, phase):
                    label = "출발편" if phase == "departure" else "도착편"
                    st.write(f"📅 {date_string} {label} 조회 중...")

                terminal_items = fetch_excel_data(dates, target_terminal_id, progress_callback=on_progress)
                status.update(label="조회 완료!", state="complete")

            if start_date_string == end_date_string:
                filename = f"인천공항 운항현황 PBB_MT {target_terminal} ({start_date_string}).xlsx"
            else:
                filename = f"인천공항 운항현황 PBB_MT {target_terminal} ({start_date_string}_{end_date_string}).xlsx"

            total = sum(len(v) for v in terminal_items.values())
            st.success(f"총 {total}건 조회 완료")
            st.write(f"{target_terminal}: {len(terminal_items[target_terminal_id])}건")

            st.download_button(
                label="📥 엑셀 다운로드",
                data=file_to_bytes_io(create_excel_file(terminal_items)),
                file_name=filename,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
