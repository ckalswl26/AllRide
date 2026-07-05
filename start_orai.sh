#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
if [ ! -f .env ]; then
  cp .env.example .env
  echo "[오라이] .env 파일을 생성했습니다. API 키를 입력한 뒤 다시 실행해 주세요."
  exit 1
fi
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
python3 manage.py migrate
python3 manage.py runserver 127.0.0.1:8000
