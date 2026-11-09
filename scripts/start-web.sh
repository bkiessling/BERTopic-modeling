#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
if [[ ! -f frontend/dist/index.html ]]; then
  echo 'Frontend fehlt. Bitte zuerst: cd frontend && npm ci && npm run build' >&2
  exit 1
fi
exec python -m uvicorn web_api.app:app --host 127.0.0.1 --port "${PORT:-8000}" --workers 1
