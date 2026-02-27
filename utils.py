from __future__ import annotations

from datetime import datetime, timedelta


def format_date(raw_datetime: str) -> str:
    if not raw_datetime or raw_datetime == "-":
        return "-"
    try:
        parsed_datetime = datetime.strptime(raw_datetime.strip(), "%Y%m%d%H%M")
        return parsed_datetime.strftime("%Y-%m-%d")
    except ValueError:
        return raw_datetime


def format_time(raw_datetime: str) -> str:
    if not raw_datetime or raw_datetime == "-":
        return "-"
    try:
        parsed_datetime = datetime.strptime(raw_datetime.strip(), "%Y%m%d%H%M")
        return parsed_datetime.strftime("%H%M")
    except ValueError:
        return raw_datetime


def format_hhmm(raw_datetime: str) -> str:
    time_string = format_time(str(raw_datetime or ""))
    # format_time이 "0005" 같은 4자리 숫자를 반환하면 콜론 삽입
    if len(time_string) == 4 and time_string.isdigit():
        return f"{time_string[:2]}:{time_string[2:]}"
    return time_string


def date_range(start: str, end: str) -> list[str]:
    start_datetime = datetime.strptime(start, "%Y%m%d")
    end_datetime = datetime.strptime(end, "%Y%m%d")
    dates = []
    while start_datetime <= end_datetime:
        dates.append(start_datetime.strftime("%Y%m%d"))
        start_datetime += timedelta(days=1)
    return dates
