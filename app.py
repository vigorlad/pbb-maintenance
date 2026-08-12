
import os

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


# 앱은 홈서버에서 서비스한다. 홈서버 표시(DEPLOY_ENV=home)가 없는 곳
# (예: 구 Streamlit Cloud 주소)에서는 새 주소로 이동시킨다.
_HOME_URL = "https://wheon-cloud.tail8f80bb.ts.net/"


def _is_home_server() -> bool:
    if os.environ.get("DEPLOY_ENV") == "home":
        return True
    try:
        return st.secrets.get("DEPLOY_ENV") == "home"
    except Exception:
        return False


try:
    _secrets_val = st.secrets.get("DEPLOY_ENV")
except Exception as exc:
    _secrets_val = f"<error: {exc}>"
st.caption(
    f"debug: env={os.environ.get('DEPLOY_ENV')!r} · secrets={_secrets_val!r} "
    f"· home={_is_home_server()}"
)

if not _is_home_server():
    # Streamlit 안에서 스크립트 실행은 불가능하므로(컴포넌트 iframe은
    # 샌드박스, markdown의 이벤트 핸들러는 React가 차단) 자동 이동은
    # meta refresh로, 실패 대비는 수동 버튼으로 처리한다.
    st.markdown(
        f'<meta http-equiv="refresh" content="0; url={_HOME_URL}">',
        unsafe_allow_html=True,
    )
    st.markdown(
        f"### 앱 주소가 이전되었습니다\n"
        f"잠시 후 자동으로 이동합니다. 이동하지 않으면 아래 버튼을 눌러주세요."
    )
    st.link_button("새 주소로 이동 →", _HOME_URL)
    st.stop()


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
