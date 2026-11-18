# POS Bar

Sistema de punto de venta para bar: mesas en tiempo real, órdenes, abonos
parciales, pago total y corte del día.

- **Backend**: FastAPI + SQLAlchemy 2 + Alembic + PostgreSQL 16
- **Frontend**: Next.js 16 (App Router) + TypeScript + Tailwind + TanStack Query
- **Infra**: Docker Compose + Caddy (HTTPS/WSS)

La fuente de verdad es [`specs/PDR.yaml`](./specs/PDR.yaml); el contrato REST es
[`specs/openapi.yaml`](./specs/openapi.yaml) (los tipos TS se generan desde ahí).

## Arranque rápido (Docker)

```bash
cd infra
cp .env.example .env          # edita passwords y JWT_SECRET
docker compose up --build
```

| Servicio | URL |
|---|---|
| Frontend | http://localhost:3000 |
| API docs | http://localhost:8000/docs |
| Health | http://localhost:8000/health/ready |

Credenciales seed (dev):

| Rol | Email | Password |
|---|---|---|
| Admin | `admin@posbar.com` | `admin12345` |
| Mesero | `mesero@posbar.com` | `mesero12345` |

> En producción cambia `INITIAL_ADMIN_PASSWORD`, `JWT_SECRET` y
> `POSTGRES_PASSWORD`, y pon `SEED_DEMO_USERS=False`. Ver
> [`docs/DEPLOY.md`](./docs/DEPLOY.md).

## Desarrollo local (sin Docker para el código)

```bash
# 1) PostgreSQL (ejemplo con Docker)
docker run -d --name posbar-db -p 5432:5432 \
  -e POSTGRES_DB=pos_bar -e POSTGRES_USER=pos_user -e POSTGRES_PASSWORD=pos_pass \
  postgres:16-alpine

# 2) Backend
cd backend
python -m venv .venv && . .venv/bin/activate
pip install -e ".[dev]"
alembic upgrade head && python -m app.db.seed
uvicorn app.main:app --reload

# 3) Frontend
cd frontend
npm ci
npm run dev
```

Variables del backend: ver `infra/.env.example`. Para desarrollo local basta con
exportar `POSTGRES_*`, `JWT_SECRET`, `COOKIE_SECURE=False` y
`APP_ENV=development`.

## Scripts

### Backend (`backend/`)

```bash
ruff check . && ruff format --check .
mypy app --strict
alembic upgrade head
python -m app.db.seed
pytest tests/ -q
```

> Los tests esperan una base **vacía** (no siembres antes de correrlos). Usa una
> BD dedicada: crea `pos_bar_test`, aplica `alembic upgrade head` y ejecuta
> `POSTGRES_DB=pos_bar_test pytest tests/ -q`.

### Frontend (`frontend/`)

```bash
npm run lint
npx vitest run
npm run build
npm run gen:types      # regenera lib/api-types.ts desde specs/openapi.yaml
npm run e2e            # requiere el stack levantado + navegadores de Playwright
```

### Operación (`infra/`)

```bash
./backup.sh            # backup de PostgreSQL (formato custom)
./restore.sh backups/posbar-<fecha>.dump
```

## Estructura

```
app-bar/
├── specs/PDR.yaml          # spec maestra (fuente de verdad)
├── specs/openapi.yaml      # contrato REST
├── docs/CLIENT_SPEC.md     # requisitos para el cliente
├── docs/DEPLOY.md          # despliegue, VPN, backups y checklist
├── docs/ACEPTACION.md      # checklist firmable de entrega
├── CHANGELOG.md            # historial de versiones
├── backend/                # FastAPI + SQLAlchemy + Alembic
├── frontend/               # Next.js 16 (App Router)
└── infra/                  # docker-compose, Caddyfile, .env.example
```

## Reglas de negocio clave

- Dinero en **pesos COP enteros** (sin centavos).
- Pagos parciales por ítem/cantidad (`payment_allocations`); el pago total
  auto-asigna los pendientes.
- Anular un pago es **soft-cancel** auditado (`cancelled_at` / `cancelled_by`).
- La mesa queda **libre** solo cuando la orden está `paid` o `cancelled`.
- Una orden cerrada sin pagos se puede cancelar; una orden cerrada no puede
  quedar vacía.
- Reportes en `America/Bogota`, solo órdenes pagadas.

## Seguridad

- JWT en cookie **HttpOnly** (`SameSite=Lax`, `Secure` en producción), 24 h.
- Passwords con **Argon2id** (`pwdlib`).
- Rate limiting con `slowapi` (login, pagos, reportes).
- WebSocket autenticado por cookie; el token nunca viaja en la URL.
- En `APP_ENV=production` la app valida secretos y `COOKIE_SECURE` al arrancar.
