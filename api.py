"""
============================================================
api.py - 인천공항 공공데이터 API 호출
============================================================
공공데이터포털(data.go.kr)의
'인천국제공항 항공기 운항 현황 상세(statusOfAllFltDeOdp)' API를 호출합니다.

사용하는 오퍼레이션(operation):
  - getFltArrivalsDeOdp   : 도착편 조회
  - getFltDeparturesDeOdp : 출발편 조회

API는 한 번에 최대 1000건까지 반환하므로,
전체 데이터를 얻으려면 페이지를 넘기며 반복 호출해야 합니다.
============================================================
"""

import requests
import config


def fetch_all_flights(operation: str, search_date: str) -> list[dict]:
    """
    지정한 오퍼레이션(출발/도착)의 전체 운항 데이터를 수집합니다.

    동작 방식:
      1. pageNo=1부터 API 호출 시작
      2. 응답에서 items(운항 데이터 리스트)를 꺼내 누적
      3. 누적 건수가 totalCount에 도달하면 종료
      4. 아직 남았으면 pageNo를 1 증가시켜 다음 페이지 호출

    매개변수:
      operation   : API 오퍼레이션명
                    "getFltArrivalsDeOdp" (도착) 또는
                    "getFltDeparturesDeOdp" (출발)
      search_date : 조회 날짜 문자열 (형식: "YYYYMMDD", 예: "20250226")

    반환값:
      운항 데이터 딕셔너리의 리스트
      각 딕셔너리는 flightId, scheduleDatetime, fstandPosition 등의 키를 포함
    """
    url = f"{config.BASE_URL}/{operation}"
    all_items = []  # 전체 결과를 누적할 리스트
    page = 1

    while True:
        # API 요청 파라미터 구성
        params = {
            "serviceKey": config.SERVICE_KEY,  # 인증키
            "type": "json",                    # 응답 형식 (JSON)
            "numOfRows": config.NUM_OF_ROWS,   # 한 페이지당 건수
            "pageNo": page,                    # 현재 페이지 번호
            "searchDate": search_date,         # 조회 날짜
        }

        print(f"  [{operation}] 페이지 {page} 요청 중...")
        resp = requests.get(url, params=params, timeout=30)
        resp.raise_for_status()  # HTTP 에러 시 예외 발생
        data = resp.json()

        # 응답 구조: { "response": { "body": { "totalCount": N, "items": [...] } } }
        body = data.get("response", {}).get("body", {})
        total_count = body.get("totalCount", 0)  # 전체 데이터 건수
        items = body.get("items", [])             # 이번 페이지 데이터

        if not items:
            break

        all_items.extend(items)
        print(f"  [{operation}] 페이지 {page}: {len(items)}건 수신 "
              f"(누적 {len(all_items)}/{total_count})")

        # 전체 데이터를 다 가져왔으면 종료
        if len(all_items) >= total_count:
            break

        page += 1

    return all_items