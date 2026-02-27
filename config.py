
import os
from datetime import timedelta, timezone

SERVICE_KEY = os.environ.get("SERVICE_KEY", "")
BASE_URL = "https://apis.data.go.kr/B551177/statusOfAllFltDeOdp"
NUM_OF_ROWS = 1000

TERMINAL_MAP = {
    "P01": "T1(제1터미널)",
    "P02": "탑승동",
    "P03": "T2(제2터미널)",
}

PASSENGER_TERMINALS = set(TERMINAL_MAP.keys())

SHEET_ORDER = [
    ("P01", "T1"),
    ("P02", "탑승동"),
    ("P03", "T2"),
]

KST = timezone(timedelta(hours=9))

EXCEL_COLUMNS = [
    ("운항일자",      "_date"),                # scheduled_datetime에서 날짜만 추출
    ("출도착",        "_flight_type"),          # "A"(도착) 또는 "D"(출발)
    ("편명",          "flight_number"),         # 항공편명 (예: KE001)
    ("I/D",           "type_of_flight"),        # 국제선(I) / 국내선(D)
    ("STA/STD",       "scheduled_datetime"),    # 계획 시각 (Scheduled)
    ("등록기호",      "registration_number"),   # 항공기 등록번호
    ("ATA/ATD",       "actual_datetime"),       # 실제/예상 시각 (Actual)
    ("운항여부",      "remark"),                # 운항 상태 (출발, 도착, 지연 등)
    ("주기장",        "gate_number"),           # 게이트/주기장 번호
    ("기종",          "aircraft_type"),         # 항공기 기종 (예: B737)
    ("출발지공항명",  "_departure_airport"),    # 도착편이면 출발공항, 아니면 "-"
    ("도착지공항명",  "_arrival_airport"),      # 출발편이면 도착공항, 아니면 "-"
]
