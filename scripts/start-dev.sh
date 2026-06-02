#!/usr/bin/env bash
# Start the full local stack: OCR service (:8010), LangGraph agent (:8000),
# Airtable API (:8001), Next.js (:3000).
# Usage:  ./scripts/start-dev.sh
#         ./scripts/start-dev.sh --skip-install

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

SKIP_INSTALL=false
if [[ "${1:-}" == "--skip-install" ]]; then
  SKIP_INSTALL=true
fi

step() { echo ""; echo "==> $*"; }

if [[ ! -f .env ]]; then
  echo "warning: .env not found. Copy .env.example to .env and add your API keys." >&2
fi

VENV_PYTHON="$ROOT/.venv/bin/python"
VENV_PIP="$ROOT/.venv/bin/pip"

if [[ "$SKIP_INSTALL" == false ]]; then
  if [[ ! -x "$VENV_PYTHON" ]]; then
    step "Creating Python virtual environment (.venv)"
    python3 -m venv .venv
  fi

  step "Installing Python dependencies (backend-airtable + agent + OCR service)"
  "$VENV_PIP" install -r requirements.txt

  if [[ ! -d node_modules ]]; then
    step "Installing npm dependencies"
    npm install
  fi
fi

if [[ ! -x "$VENV_PYTHON" ]]; then
  echo "error: virtual environment missing at .venv. Run without --skip-install first." >&2
  exit 1
fi

cleanup() {
  echo ""
  step "Stopping services"
  local pids
  pids="$(jobs -p)"
  if [[ -n "$pids" ]]; then
    kill $pids 2>/dev/null || true
  fi
}
trap cleanup EXIT INT TERM

step "Starting OCR policy service on http://localhost:8010"
( cd ocr-service && exec "$VENV_PYTHON" main.py ) &

step "Starting LangGraph agent on http://localhost:8000"
( cd agent && exec "$VENV_PYTHON" main.py ) &

step "Starting Airtable API on http://localhost:8001"
( cd backend-airtable && exec "$VENV_PYTHON" main.py ) &

step "Starting Next.js on http://localhost:3000"
npm run dev &

echo ""
echo "All services are running in this terminal (Ctrl+C to stop)."
echo "  App:     http://localhost:3000"
echo "  OCR:     http://localhost:8010/health"
echo "  Agent:   http://localhost:8000/copilotkit/health"
echo "  Backend: http://localhost:8001/health"
echo ""
echo "Chat policy uploads need OCR_SERVICE_URL=http://localhost:8010 in .env"
echo "(and Azure DI keys in ocr-service/.env for real PDF summarization)."
echo ""

wait
