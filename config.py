
import os
from datetime import timedelta, timezone

from models import Terminal

SERVICE_KEY = os.environ.get("SERVICE_KEY", "")
BASE_URL = "https://apis.data.go.kr/B551177/statusOfAllFltDeOdp"
NUM_OF_ROWS = 10000

TERMINALS = [
    Terminal("T1", "P01"),
    Terminal("Con", "P02"),
    Terminal("T2", "P03"),
]

KST = timezone(timedelta(hours=9))

EXCEL_COLUMNS = [
    ("운항일자",      "_date"),
    ("출도착",        "_flight_type"),
    ("편명",          "flight_number"),
    ("I/D",           "type_of_flight"),
    ("STA/STD",       "scheduled_datetime"),
    ("등록기호",      "registration_number"),
    ("ATA/ATD",       "actual_datetime"),
    ("운항여부",      "remark"),
    ("주기장",        "gate_number"),
    ("기종",          "aircraft_type"),
    ("출발지공항명",  "_departure_airport"),
    ("도착지공항명",  "_arrival_airport"),
]
