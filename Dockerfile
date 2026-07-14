# Single-container deployment: the Next.js frontend is statically exported and
# served by FastAPI alongside the API, so the browser talks to one origin.
# Targets Hugging Face Spaces (Docker SDK), which expects the app on port 7860.

# ---------- Stage 1: build the frontend ----------
FROM node:22-alpine AS frontend

WORKDIR /build

# Install deps first so this layer caches across source-only changes.
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci

COPY frontend/ ./

# Empty = same origin. The deployed frontend calls /api/... on its own host.
ENV NEXT_PUBLIC_API_URL=""

# `output: 'export'` in next.config.ts writes the site to ./out
RUN npm run build


# ---------- Stage 2: runtime ----------
FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    ENVIRONMENT=production \
    STATIC_DIR=/app/static \
    PORT=7860

WORKDIR /app

COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ ./
COPY --from=frontend /build/out ./static
COPY docker-entrypoint.sh ./

# Hugging Face Spaces runs containers as uid 1000; matching it avoids
# permission surprises on any mounted paths.
RUN chmod +x docker-entrypoint.sh \
    && useradd -m -u 1000 appuser \
    && chown -R appuser:appuser /app
USER appuser

EXPOSE 7860

# Fail the container's health status if the API stops answering.
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD python -c "import urllib.request,os,sys; sys.exit(0 if urllib.request.urlopen(f'http://127.0.0.1:{os.environ.get(\"PORT\",7860)}/api/health').status==200 else 1)"

CMD ["./docker-entrypoint.sh"]
