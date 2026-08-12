from __future__ import annotations

import socket
import ssl
import time
from datetime import datetime

import certifi
import requests

import config

_HOST = "apis.data.go.kr"
_PORT = 443
_USER_AGENT = "Mozilla/5.0 (compatible; PBB-Maintenance/1.0)"


def run_diagnostics() -> list[tuple[str, bool, str]]:
    """(단계명, 성공여부, 상세) 목록을 반환한다. 연결 단계가 실패하면 이후 단계는 중단."""
    results: list[tuple[str, bool, str]] = []

    try:
        egress_ip = requests.get("https://api.ipify.org", timeout=10).text.strip()
        results.append(("이 서버의 공인 IP", True, egress_ip))
    except requests.exceptions.RequestException as exc:
        results.append(("이 서버의 공인 IP", False, f"확인 실패 — {exc}"))

    start = time.time()
    try:
        ip = socket.gethostbyname(_HOST)
    except OSError as exc:
        results.append((f"DNS 조회 ({_HOST})", False, str(exc)))
        return results
    results.append((f"DNS 조회 ({_HOST})", True, f"{ip} · {time.time() - start:.2f}초"))

    start = time.time()
    try:
        sock = socket.create_connection((ip, _PORT), timeout=10)
    except OSError as exc:
        results.append(("TCP 연결 (443)", False, f"{exc} — 방화벽/IP 차단 의심"))
        return results
    results.append(("TCP 연결 (443)", True, f"{time.time() - start:.2f}초"))

    start = time.time()
    try:
        tls_context = ssl.create_default_context(cafile=certifi.where())
        tls_sock = tls_context.wrap_socket(sock, server_hostname=_HOST)
        tls_sock.close()
    except (OSError, ssl.SSLError) as exc:
        sock.close()
        results.append(("TLS 핸드셰이크", False, str(exc)))
        return results
    results.append(("TLS 핸드셰이크", True, f"{time.time() - start:.2f}초"))

    start = time.time()
    try:
        response = requests.get(
            f"{config.BASE_URL}/getFltDeparturesDeOdp",
            params={
                "serviceKey": config.SERVICE_KEY,
                "type": "json",
                "numOfRows": 1,
                "pageNo": 1,
                "searchDate": datetime.now(config.KST).strftime("%Y%m%d"),
                "passengerOrCargo": "P",
            },
            headers={"User-Agent": _USER_AGENT},
            timeout=(10, 30),
        )
        results.append(
            ("API 호출 (1건)", response.ok, f"HTTP {response.status_code} · {time.time() - start:.2f}초")
        )
    except requests.exceptions.ConnectTimeout:
        results.append(("API 호출 (1건)", False, "10초 내 TCP 연결 실패 — IP 차단 의심"))
    except requests.exceptions.ReadTimeout:
        results.append(("API 호출 (1건)", False, "연결은 됐지만 30초 내 응답 없음 — 서버 지연/트래픽 제한 의심"))
    except requests.exceptions.RequestException as exc:
        results.append(("API 호출 (1건)", False, str(exc)))

    return results
