# ---------- Stage 1: build the React frontend ----------
FROM node:20-alpine AS frontend
WORKDIR /app/frontend
# Resolve dependencies for the *container* platform (Tailwind v4's lightningcss
# ships per-OS native binaries; a Windows-generated lockfile would miss them).
COPY frontend/package.json ./
RUN npm install --no-audit --no-fund
COPY frontend/ ./
RUN npm run build

# ---------- Stage 2: build the FastAPI backend + serve everything ----------
FROM python:3.12-slim AS backend
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1
WORKDIR /app

COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/app ./app
COPY backend/alembic ./alembic
COPY backend/alembic.ini ./

# Serve the built frontend from FastAPI's static dir
COPY --from=frontend /app/frontend/dist ./static

EXPOSE 8000
# Bind to $PORT when the platform provides one (Render/Cloud Run), else 8000.
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
