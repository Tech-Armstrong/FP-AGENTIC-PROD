# syntax=docker/dockerfile:1
#
# Single-container build for the "Chat With Your Data" stack.
# Runs all four services in ONE container, supervised by supervisord:
#   - Next.js frontend        : 3000  (the only port you expose publicly)
#   - LangGraph chat agent     : 8000  (agent/main.py)
#   - Airtable + planning API  : 8001  (backend/airtable_main.py)
#   - OCR policy service       : 8010  (ocr-service/main.py)
#
# Inside the container the frontend reaches the Python services over localhost,
# so the only port that needs to be published is 3000.
#
# Build:  docker build -t chatwithyourdata:latest .
# Run:    docker run --env-file .env -p 3000:3000 chatwithyourdata:latest

# ---------------------------------------------------------------------------
# Stage 1 — build the Next.js frontend (Node 20)
# ---------------------------------------------------------------------------
FROM node:20-bookworm-slim AS web-build
WORKDIR /app

# Install JS deps first (better layer caching).
COPY package.json package-lock.json* ./
RUN npm ci

# Copy the rest of the frontend source and build the production bundle.
COPY tsconfig.json next.config.ts postcss.config.mjs ./
COPY app ./app
COPY components ./components
COPY lib ./lib
COPY public ./public
COPY data ./data
RUN npm run build

# ---------------------------------------------------------------------------
# Stage 2 — final runtime image (Python 3.11 + Node 20 + supervisord)
# ---------------------------------------------------------------------------
FROM python:3.11-slim-bookworm AS runtime

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    NODE_VERSION=20 \
    NEXT_TELEMETRY_DISABLED=1

# System deps: Node.js 20 (for `next start`) + supervisord (process manager) + curl (healthcheck).
RUN apt-get update \
    && apt-get install -y --no-install-recommends curl ca-certificates gnupg supervisor \
    && mkdir -p /etc/apt/keyrings \
    && curl -fsSL https://deb.nodesource.com/gpgkey/nodesource-repo.gpg.key | gpg --dearmor -o /etc/apt/keyrings/nodesource.gpg \
    && echo "deb [signed-by=/etc/apt/keyrings/nodesource.gpg] https://deb.nodesource.com/node_20.x nodistro main" > /etc/apt/sources.list.d/nodesource.list \
    && apt-get update \
    && apt-get install -y --no-install-recommends nodejs \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# --- Python dependencies (all three services share one venv via root requirements.txt) ---
COPY requirements.txt ./
COPY backend/requirements.txt ./backend/requirements.txt
COPY agent/requirements.txt ./agent/requirements.txt
COPY ocr-service/requirements.txt ./ocr-service/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# --- Application source for the Python services ---
COPY agent ./agent
COPY backend ./backend
COPY ocr-service ./ocr-service
COPY Financial_Planning ./Financial_Planning

# --- Built Next.js frontend + the files `next start` needs at runtime ---
COPY --from=web-build /app/.next ./.next
COPY --from=web-build /app/public ./public
COPY --from=web-build /app/node_modules ./node_modules
COPY --from=web-build /app/package.json ./package.json
COPY next.config.ts ./next.config.ts

# --- supervisord config that launches all four processes ---
COPY deploy/supervisord.conf /etc/supervisord.conf

# Default in-container wiring: the frontend talks to the Python services over localhost.
# These can be overridden at runtime; secrets (Azure/Airtable/Tavily) come from --env-file / Azure.
ENV LANGGRAPH_AGENT_URL=http://localhost:8000/copilotkit \
    FASTAPI_BASE_URL=http://localhost:8001 \
    OCR_SERVICE_URL=http://localhost:8010 \
    FASTAPI_PORT=8001 \
    LANGGRAPH_AGENT_PORT=8000 \
    OCR_SERVICE_PORT=8010 \
    PORT=3000

# Only the frontend is published; 8000/8001/8010 stay internal to the container.
EXPOSE 3000

# Basic health: the public frontend responding means supervisord came up.
HEALTHCHECK --interval=30s --timeout=5s --start-period=40s --retries=3 \
    CMD curl -fsS http://localhost:3000 || exit 1

CMD ["/usr/bin/supervisord", "-c", "/etc/supervisord.conf", "-n"]
