
import streamlit as st
from datetime import datetime, timedelta

import config
import ui_styles
import ui_gate_search
import ui_excel_download

try:
    if "SERVICE_KEY" in st.secrets:
        config.SERVICE_KEY = st.secrets["SERVICE_KEY"]
except Exception:
    pass


st.set_page_config(
    page_title="인천공항 운항현황 PBB_MT",
    page_icon="✈️",
    layout="wide",
)


st.markdown(ui_styles.CSS, unsafe_allow_html=True)


st.markdown(
    '<h2 style="font-size:1.4rem;">'
    '<a href="/" target="_self" style="text-decoration:none;color:inherit;">'
    '✈️ 인천공항 운항현황 PBB_MT</a></h2>',
    unsafe_allow_html=True,
)


today = datetime.now(config.KST).date()     # 오늘 날짜 (KST 기준)
now = datetime.now(config.KST)              # 현재 시각 (KST 기준)
min_date = today + timedelta(days=-3)       # 조회 가능 최소 날짜 (3일 전)
max_date = today + timedelta(days=6)        # 조회 가능 최대 날짜 (6일 후)


tab1, tab2 = st.tabs(["🛬 게이트 출도착 조회", "📊 엑셀 다운로드"])

ui_gate_search.render(tab1, today, now, min_date, max_date)
ui_excel_download.render(tab2, today, min_date, max_date)
