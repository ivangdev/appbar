# =============================================================================
# backend/Dockerfile — POS Bar API (FastAPI)
# Build multi-stage ligero. Ejecuta migraciones Alembic antes de arrancar uvicorn.
# =============================================================================
FROM python:3.12-slim AS runtime

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Dependencias del sistema (psycopg[binary] y argon2 no las necesitan, pero curl
# se usa para el HEALTHCHECK).
RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

# Instala el paquete (dependencias + app). Se copia solo lo necesario del codigo.
COPY pyproject.toml ./
COPY app ./app
RUN pip install --upgrade pip && pip install .

# Codigo de migraciones y configuracion de Alembic.
COPY alembic.ini ./
COPY alembic ./alembic

EXPOSE 8000

HEALTHCHECK --interval=15s --timeout=5s --start-period=30s --retries=5 \
    CMD curl -fsS http://localhost:8000/health/ready || exit 1

# Aplica migraciones, crea el admin inicial (idempotente) y levanta el servidor.
# --proxy-headers + forwarded-allow-ips: confia en X-Forwarded-For de Caddy/Next
# para que el rate-limit y los logs vean la IP real del cliente.
CMD ["sh", "-c", "alembic upgrade head && python -m app.db.seed && exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --proxy-headers --forwarded-allow-ips='*'"]
