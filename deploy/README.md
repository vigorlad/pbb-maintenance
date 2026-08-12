# 홈서버 배포 가이드 (리눅스 + Docker + Tailscale Funnel)

공공데이터포털이 Streamlit Community Cloud의 IP 대역(GCP)을 차단하고 있어,
국내 IP를 가진 홈서버에서 앱을 도커 컨테이너로 서비스한다.

## 최초 설치

홈서버에서:

```bash
curl -fsSL https://raw.githubusercontent.com/vigorlad/pbb-maintenance/main/deploy/setup_home_server.sh | bash
```

또는 리포를 받은 뒤 `bash deploy/setup_home_server.sh`.

스크립트가 하는 일:
1. 8501 포트 충돌 확인
2. git/docker 확인 (없으면 설치; 도커를 새로 설치한 경우 재로그인 후 재실행 필요)
3. `~/pbb-maintenance`에 코드 clone (이미 있으면 pull)
4. SERVICE_KEY 입력받아 `.env` 생성 (최초 1회)
5. `docker compose up -d --build` — 부팅 시 자동 시작(restart: unless-stopped)

이후 스크립트 안내에 따라 Tailscale 설치 → `sudo tailscale up` →
`sudo tailscale funnel --bg 8501` 실행하면 `https://…ts.net` 공개 주소가 생긴다.
Funnel 설정은 재부팅 후에도 유지된다.

컨테이너는 호스트의 127.0.0.1:8501에만 바인딩되므로,
Tailscale Funnel을 통하지 않고는 외부에서 직접 접근할 수 없다.

## 코드 업데이트

```bash
cd ~/pbb-maintenance && git pull && docker compose up -d --build
```

(또는 setup 스크립트를 다시 실행해도 된다.)

## 상태 확인

```bash
docker compose ps                        # 컨테이너 상태
docker logs -f pbb-maintenance           # 앱 로그
tailscale funnel status                  # 공개 URL 확인
```

연결 문제가 의심되면 앱 하단의 "🔧 공공데이터포털 연결 진단" 패널을 실행한다.
