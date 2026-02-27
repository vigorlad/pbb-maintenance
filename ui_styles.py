"""
============================================================
ui_styles.py - Streamlit 페이지 CSS 스타일
============================================================
웹 페이지의 시각적 디자인을 담당하는 CSS를 정의합니다.

구성:
  - 기본 레이아웃 (상단 여백, 모바일 반응형)
  - 버튼 및 입력 필드 스타일
  - 운항 정보 카드 (.flight-card) - 다음 도착/출발편 강조 표시
  - 운항 리스트 행 (.next-flight-row) - 이후 운항 예정 목록
  - 탭 스타일
============================================================
"""

# Streamlit에 주입할 CSS 문자열
# st.markdown(CSS, unsafe_allow_html=True) 로 사용
CSS = """
<style>
    /* ── 기본 레이아웃 ── */
    /* Streamlit 기본 헤더와 겹치지 않도록 상단 여백 확보 */
    .block-container {
        padding-top: 2rem !important;
    }

    /* ── 모바일 반응형 ── */
    /* 화면 너비 768px 이하(스마트폰)에서 여백 축소 및 탭 크기 조정 */
    @media (max-width: 768px) {
        .block-container {
            padding: 2rem 0.8rem 1rem 0.8rem !important;
        }
        .stTabs [data-baseweb="tab-list"] {
            gap: 0;
        }
        .stTabs [data-baseweb="tab"] {
            padding: 12px 16px;
            font-size: 1rem;
        }
    }

    /* ── 버튼 스타일 ── */
    /* 전체 너비, 큰 텍스트, 둥근 모서리 */
    .stButton > button {
        width: 100%;
        padding: 0.75rem 1.5rem;
        font-size: 1.1rem;
        font-weight: 600;
        border-radius: 12px;
    }

    /* ── 텍스트 입력 필드 스타일 ── */
    .stTextInput > div > div > input {
        font-size: 1.2rem;
        padding: 0.75rem;
        border-radius: 10px;
    }

    /* ── 운항 정보 카드 ── */
    /* 다음 도착/출발편을 크게 보여주는 메인 카드 */
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
    /* 시간을 아주 크게 표시 */
    .flight-card .time-big {
        font-size: 3rem;
        font-weight: 700;
        color: #4dd0e1;
        line-height: 1.1;
        margin: 0.5rem 0;
    }
    /* 라벨 (ETA, STA 등의 제목) */
    .flight-card .label {
        font-size: 0.85rem;
        color: #90caf9;
        margin-bottom: 2px;
    }
    /* 값 (실제 데이터) */
    .flight-card .value {
        font-size: 1.1rem;
        color: #ffffff;
        margin-bottom: 0.6rem;
    }
    /* 운항 상태 뱃지 (출발, 도착, 지연 등) */
    .flight-card .status-badge {
        display: inline-block;
        background: rgba(255,255,255,0.2);
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.9rem;
    }

    /* ── 이후 운항편 리스트 행 ── */
    /* 메인 카드 아래에 나오는 후속 운항편 목록 */
    .next-flight-row {
        background: #f8f9fa;
        border-radius: 10px;
        padding: 0.8rem 1rem;
        margin: 0.4rem 0;
        border-left: 4px solid #1e3a5f;  /* 왼쪽 색상 바 */
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
    .next-flight-row .nf-label {
        font-size: 0.7rem;
        color: #999;
        margin-right: 2px;
    }

    /* ── 탭 스타일 ── */
    .stTabs [data-baseweb="tab-list"] {
        background: #f0f2f6;
        border-radius: 12px;
        padding: 4px;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 10px;
        font-weight: 600;
    }

    /* ── 게이트 안내 캡션 ── */
    .gate-caption {
        text-align: center;
        color: #888;
        font-size: 0.85rem;
        margin-top: 0.5rem;
    }
</style>
"""
