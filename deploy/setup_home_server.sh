#!/usr/bin/env bash
# 홈서버(우분투 등 리눅스) 1회 설치 스크립트 — 도커 기반.
# 실행: bash setup_home_server.sh
# 다시 실행하면 코드 업데이트 + 이미지 재빌드 + 컨테이너 재시작으로 동작한다.
set -euo pipefail

REPO_URL="https://github.com/vigorlad/pbb-maintenance.git"
APP_DIR="$HOME/pbb-maintenance"
PORT=8501

echo "== 0/4 포트 확인 =="
if ss -tln 2>/dev/null | awk '{print $4}' | grep -q ":$PORT\$"; then
    if ! docker ps --format '{{.Names}}' 2>/dev/null | grep -q '^pbb-maintenance$'; then
        echo "오류: $PORT 포트를 다른 프로그램이 사용 중입니다."
        echo "docker-compose.yml의 ports와 이 스크립트의 PORT 값을 바꾼 뒤 다시 실행하세요."
        exit 1
    fi
    echo "  -> $PORT 포트는 본 컨테이너(pbb-maintenance)가 사용 중 — 계속 진행"
else
    echo "  -> $PORT 포트 비어 있음"
fi

echo "== 1/4 필수 도구 확인 =="
if ! command -v git > /dev/null; then
    sudo apt-get update -y && sudo apt-get install -y git
fi
if ! command -v docker > /dev/null; then
    echo "  -> 도커가 없어 설치합니다 (get.docker.com)"
    curl -fsSL https://get.docker.com | sh
    sudo usermod -aG docker "$USER"
    echo "  -> 설치 완료. 그룹 반영을 위해 재로그인 후 이 스크립트를 다시 실행하세요."
    exit 0
fi

echo "== 2/4 코드 받기 =="
if [ -d "$APP_DIR/.git" ]; then
    git -C "$APP_DIR" pull --ff-only
else
    git clone "$REPO_URL" "$APP_DIR"
fi

echo "== 3/4 서비스 키 설정 =="
ENV_FILE="$APP_DIR/.env"
if [ ! -f "$ENV_FILE" ]; then
    read -rp "공공데이터포털 SERVICE_KEY 입력: " SERVICE_KEY
    printf 'SERVICE_KEY=%s\n' "$SERVICE_KEY" > "$ENV_FILE"
    chmod 600 "$ENV_FILE"
    echo "  -> $ENV_FILE 저장 완료"
else
    echo "  -> 기존 $ENV_FILE 사용"
fi

echo "== 4/4 컨테이너 빌드 및 실행 =="
cd "$APP_DIR"
docker compose up -d --build
sleep 3
docker compose ps

cat <<'GUIDE'

============================================
설치 완료. 외부 공개는 Tailscale Funnel로:

  1) Tailscale 설치 (이미 설치돼 있으면 생략):
     curl -fsSL https://tailscale.com/install.sh | sh
  2) 로그인 (이미 로그인돼 있으면 생략):
     sudo tailscale up
  3) 공개 URL 열기 (재부팅 후에도 유지됨):
     sudo tailscale funnel --bg 8501

  3번 실행 시 출력되는 https://...ts.net 주소가
  접속 주소입니다. (최초 1회는 안내되는 링크에서
  HTTPS/Funnel 활성화 승인이 필요할 수 있음)
============================================
GUIDE
