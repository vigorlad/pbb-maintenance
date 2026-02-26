"""
============================================================
excel_export.py - 엑셀 파일 생성
============================================================
운항 데이터를 터미널별 시트로 나누어 엑셀 파일(.xlsx)을 생성합니다.

엑셀 구조:
  - 시트 3개: T1(제1터미널), 탑승동, T2(제2터미널)
  - 각 시트: 헤더(파란 배경) + 데이터 행 + 자동 필터
  - codeshare가 "Master"인 항공편만 포함 (코드쉐어 중복 제거)
  - 예정일시(scheduleDatetime) 기준으로 시간순 정렬

사용 라이브러리: openpyxl
============================================================
"""

from __future__ import annotations

from io import BytesIO
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
from openpyxl.utils import get_column_letter

import config
from utils import fmt_date, fmt_time

# 모든 셀에 적용할 얇은 테두리
THIN_BORDER = Border(
    left=Side(style="thin", color="CCCCCC"),
    right=Side(style="thin", color="CCCCCC"),
    top=Side(style="thin", color="CCCCCC"),
    bottom=Side(style="thin", color="CCCCCC"),
)


# ────────────────────────────────────────────────────────────
# 셀 값 변환 로직
# ────────────────────────────────────────────────────────────
def _resolve_cell_value(item: dict, field: str, flight_type: str) -> str:
    """
    하나의 셀에 들어갈 값을 결정합니다.

    config.EXCEL_COLUMNS에서 "_"로 시작하는 필드는
    API 원본 값이 아니라 가공이 필요한 필드입니다.

    매개변수:
      item        : API에서 받은 운항 데이터 딕셔너리
      field       : 컬럼의 데이터 필드명 (예: "flightId", "_date")
      flight_type : "A"(도착) 또는 "D"(출발)
    """
    if field == "_date":
        # 예정일시에서 날짜만 추출 → "2024-12-22"
        return fmt_date(str(item.get("scheduleDatetime", "") or ""))

    elif field == "_flight_type":
        # 출발/도착 구분 그대로 표시
        return flight_type

    elif field in ("scheduleDatetime", "estimatedDatetime"):
        # 시간 부분만 추출 → "0005"
        return fmt_time(str(item.get(field, "") or ""))

    elif field == "_intl_domestic":
        # 공항명이 국내선 목록에 있으면 "D"(국내), 아니면 "I"(국제)
        airport = item.get("airport", "") or ""
        return "D" if airport in config.DOMESTIC_AIRPORTS else "I"

    elif field == "_dep_airport":
        # 도착편(A)이면 출발공항 표시, 출발편이면 "-"
        return item.get("airport", "-") if flight_type == "A" else "-"

    elif field == "_arr_airport":
        # 출발편(D)이면 도착공항 표시, 도착편이면 "-"
        return item.get("airport", "-") if flight_type == "D" else "-"

    else:
        # 그 외: API 원본 값 그대로 사용
        return item.get(field, "-") or "-"


# ────────────────────────────────────────────────────────────
# 시트 작성
# ────────────────────────────────────────────────────────────
def write_excel_sheet(workbook: Workbook, sheet_name: str, all_items: list[tuple[dict, str]]):
    worksheet = workbook.create_sheet(title=sheet_name)

    # ── 1행: 헤더 작성 ──
    for col_idx, (col_name, _) in enumerate(config.EXCEL_COLUMNS, 1):
        cell = worksheet.cell(row=1, column=col_idx, value=col_name)
        cell.fill = PatternFill(start_color="1F4E79", end_color="1F4E79", fill_type="solid")
        cell.font = Font(name="맑은 고딕", bold=True, color="FFFFFF", size=10)
        cell.alignment = Alignment(horizontal="center", vertical="center")
        cell.border = THIN_BORDER

    # ── 필터링: codeshare가 "Master"인 항공편만 ──
    # 하나의 항공편이 여러 항공사 코드로 공유(codeshare)될 수 있는데,
    # "Master"가 실제 운항사이므로 이것만 남겨 중복을 제거함
    all_items = [(item, ft) for item, ft in all_items
                 if item.get("codeshare") == "Master"]

    # ── 정렬: 예정일시 기준 시간순 ──
    all_items.sort(key=lambda x: x[0].get("scheduleDatetime", "") or "")

    # ── 데이터 행 작성 ──
    for row_idx, (item, flight_type) in enumerate(all_items, 2):
        for col_idx, (_, field) in enumerate(config.EXCEL_COLUMNS, 1):
            value = _resolve_cell_value(item, field, flight_type)
            cell = worksheet.cell(row=row_idx, column=col_idx, value=value)
            cell.font = Font(name="맑은 고딕", size=10)
            cell.alignment = Alignment(horizontal="center", vertical="center")
            cell.border = THIN_BORDER

    # ── 컬럼 너비 자동 조절 ──
    # 한글은 2칸, 영문/숫자는 1칸으로 계산하여 적절한 너비 설정
    for col_idx in range(1, len(config.EXCEL_COLUMNS) + 1):
        max_len = 0
        for row in worksheet.iter_rows(min_col=col_idx, max_col=col_idx, values_only=True):
            val = str(row[0]) if row[0] else ""
            length = sum(2 if ord(c) > 127 else 1 for c in val)
            max_len = max(max_len, length)
        worksheet.column_dimensions[get_column_letter(col_idx)].width = max(max_len + 3, 10)

    # ── 자동 필터 설정 (엑셀에서 드롭다운 필터 사용 가능) ──
    worksheet.auto_filter.ref = worksheet.dimensions

def create_excel_file(terminal_items: dict[str, list[tuple[dict, str]]]) -> Workbook:
    """
    터미널별 데이터를 받아 완성된 엑셀 워크북을 생성합니다.

    매개변수:
      terminal_items : {터미널ID: [(운항데이터, 출도착구분), ...]} 딕셔너리
                       예: {"P01": [({...}, "D"), ...], "P02": [...], "P03": [...]}

    반환값:
      시트 3개(T1, 탑승동, T2)가 포함된 openpyxl Workbook 객체
    """
    wb = Workbook()
    wb.remove(wb.active)  # 기본 빈 시트 제거

    # config.SHEET_ORDER 순서대로 시트 생성
    for tid, sheet_name in config.SHEET_ORDER:
        items = terminal_items.get(tid, [])
        write_excel_sheet(wb, sheet_name, items)

    return wb

def file_to_bytes_io(wb: Workbook) -> BytesIO:
    output = BytesIO()
    wb.save(output)
    output.seek(0)
    return output