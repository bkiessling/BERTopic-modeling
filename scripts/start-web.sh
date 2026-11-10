#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
exec python -m server --port "${PORT:-8000}"
