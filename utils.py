"""
============================================================
utils.py - 날짜/시간 포맷 변환 유틸리티
============================================================
인천공항 API는 날짜/시간을 "202412220005" 같은 형식(YYYYMMDDHHmm)으로 반환합니다.
이 모듈은 이런 원시 문자열을 사람이 읽기 쉬운 형태로 변환합니다.

변환 예시:
  "202412220005" → "2024-12-22" (날짜만)
  "202412220005" → "0005"       (시간만, HHMM)
  "202412220005" → "00:05"      (시간만, HH:MM 콜론 포함)
============================================================
"""

from __future__ import annotations

from datetime import datetime, timedelta


def fmt_date(raw: str) -> str:
    """
    API 날짜/시간 문자열에서 날짜 부분만 추출합니다.

    예시: "202412220005" → "2024-12-22"
    잘못된 형식이거나 빈 값이면 "-"을 반환합니다.
    """
    if not raw or raw == "-":
        return "-"
    try:
        dt = datetime.strptime(raw.strip(), "%Y%m%d%H%M")
        return dt.strftime("%Y-%m-%d")
    except ValueError:
        return raw


def fmt_time(raw: str) -> str:
    """
    API 날짜/시간 문자열에서 시간 부분만 추출합니다 (HHMM 형식).

    예시: "202412220005" → "0005"
    잘못된 형식이거나 빈 값이면 "-"을 반환합니다.
    """
    if not raw or raw == "-":
        return "-"
    try:
        dt = datetime.strptime(raw.strip(), "%Y%m%d%H%M")
        return dt.strftime("%H%M")
    except ValueError:
        return raw


def format_hhmm(raw: str) -> str:
    """
    API 날짜/시간 문자열을 "HH:MM" 형식으로 변환합니다 (콜론 포함).

    예시: "202412220005" → "00:05"
    내부적으로 fmt_time()을 호출한 뒤 콜론을 삽입합니다.
    """
    t = fmt_time(str(raw or ""))
    # fmt_time이 "0005" 같은 4자리 숫자를 반환하면 콜론 삽입
    if len(t) == 4 and t.isdigit():
        return f"{t[:2]}:{t[2:]}"
    return t


def date_range(start: str, end: str) -> list[str]:
    """
    시작일~종료일 사이의 모든 날짜를 리스트로 반환합니다.

    매개변수:
      start : 시작일 문자열 (형식: "YYYYMMDD")
      end   : 종료일 문자열 (형식: "YYYYMMDD")

    반환값:
      ["20250226", "20250227", "20250228", ...] 형태의 날짜 문자열 리스트

    예시:
      date_range("20250226", "20250228")
      → ["20250226", "20250227", "20250228"]
    """
    s = datetime.strptime(start, "%Y%m%d")
    e = datetime.strptime(end, "%Y%m%d")
    dates = []
    while s <= e:
        dates.append(s.strftime("%Y%m%d"))
        s += timedelta(days=1)
    return dates