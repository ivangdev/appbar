# Skills y Contexto del Proyecto POS Bar

## Visión General
Sistema POS (Point of Sale) para bar con arquitectura Next.js (frontend) + FastAPI (backend) + PostgreSQL. Desarrollo Spec-Driven (PDR.yaml es la fuente de verdad).

---

## 🔧 Backend Skills (Python/FastAPI)

### FastAPI 0.115+
- **Ubicación**: `backend/app/main.py`, `backend/app/api/v1/`
- **Routers**: `auth.py`, `categories.py`, `products.py`, `tables.py`, `orders.py`, `payments.py`, `reports.py`, `users.py` + WebSocket `app/api/ws.py`
- **Endpoints clave**: login/out con JWT cookie, CRUD mesas/ordenes/items/pagos, reportes diario
- **Pattern**: Spec-First (openapi.yaml define el contrato antes de implementar)

### SQLAlchemy 2.0
- **Ubicación**: `backend/app/models/` (9 tablas: users, categories, products, tables, orders, order_items, payments, payment_allocations)
- **Base**: `DeclarativeBase` (nativo SQLAlchemy 2.0)
- **Relaciones**: `relationship()` con `back_populates`, `cascade="all, delete-orphan"`
- **Constraints**: CheckConstraint, Index, Unique constraints definidos en los modelos
- **Migraciones**: Alembic en `backend/alembic/versions/`
- **Comando**: `alembic revision --autogenerate -m "descripción"` + `alembic upgrade head`

### Pydantic v2 Schemas
- **Ubicación**: `backend/app/schemas/`
- **Patrones**: `UserRead`, `UserCreate`, `UserUpdate`, `ProductCreate`, `ProductRead`, `ProductReadAdmin`
- **Validadores**: `Field(min_length, max_length, ge, le, pattern, regex)`, `validator()` methods
- **Herencia**: `ProductReadAdmin(ProductRead)` para visibilidad de cost admin-only

### Seguridad (JWT + Auth)
- **Ubicación**: `backend/app/core/security.py`
- **Algoritmo**: HS256, JWT en HttpOnly cookie (`access_token`)
- **Config**: `config.py` - `JWT_SECRET`, `JWT_ALGORITHM`, `ACCESS_TOKEN_EXPIRE_HOURS=24`
- **Passwords**: Argon2id via `pwdlib`
- **Dependencias**: `get_current_user`, `require_role()` en `backend/app/api/deps.py`

### Slowapi (Rate Limiting)
- **Ubicación**: `backend/app/core/rate_limit.py` (limiter) + handlers en `main.py`
- **Key function**: `get_remote_address` (por IP)
- **Límites** (`app/core/constants.py`): `AUTH_RATE_LIMIT` 20/minute (login), `WRITE_RATE_LIMIT` 60/minute (pagos), `READ_ONLY_RATE_LIMIT` 120/minute (reportes)
- **Activable**: `RATE_LIMIT_ENABLED` (bool, default true); decorador `@limiter.limit(...)` por ruta; 429 vía `_rate_limit_exceeded_handler`
- **Nota**: slowapi exige granularidad `"N/minute"` (no `"N/min"`)

### Configuración Central
- **Ubicación**: `backend/app/core/config.py`
- **Variables**: PostgreSQL (`POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_HOST`, `POSTGRES_PORT`), JWT, cookie secure flag
- **Carga**: `pydantic-settings` leyendo `.env` desde `infra/.env`

---

## 🎨 Frontend Skills (Next.js 16 + TypeScript)

### Next.js 16 (App Router)
- **Ubicación**: `frontend/app/`, `frontend/components/`, `frontend/hooks/`, `frontend/stores/`
- **Routing**: File-based con `app/[slug]/page.tsx`, `app/dashboard/page.tsx`, etc.
- **Estilos**: Tailwind CSS + shadcn/ui component library
- **Data fetching**: TanStack Query v5 + axios con interceptor JWT

### TypeScript
- **Generación automática**: `npm run gen:types` → `openapi-typescript specs/openapi.yaml -o frontend/lib/api-types.ts` (NO editar a mano)
- **Stores Zustand**: `frontend/stores/auth.ts` (sesión). El resto de datos se manejan con TanStack Query
- **Hooks WS**: `frontend/hooks/use-tables-socket.ts` (WebSocket `/ws/tables`, auth por cookie HttpOnly)

### Testing
- **Unit**: `vitest` en `frontend/tests/`
- **E2E**: `playwright test` - flow: login → mesa → orden → pago → reporte
- **WS E2E**: Conexión WS + broadcast events (`table_status_update`, `order_updated`, `payment_made`)

---

## 🗄️ Infraestructura & DevOps

### PostgreSQL 16
- **Contenedor**: `infra/docker-compose.yml` (servicio `db`)
- **Volumen**: `db_data` persiste datos entre reinicios
- **Healthcheck**: `pg_isready` cada 5s
- **Acceso**: `localhost:5432` en dev, nombre servicio en prod (Dokploy)

### Docker & Docker Compose
- **Ubicación**: `infra/`
- **Comando**: `cd infra && docker compose up --build`
- **Servicios**: `db` (PostgreSQL 16), `backend` (FastAPI), `frontend` (Next.js standalone)
- **Caddyfile**: HTTPS/Let's Encrypt automático para producción

### Caddy & SSL
- **Ubicación**: `infra/Caddyfile`
- **Función**: Proxy reverso, HTTPS automático Let's Encrypt, WSS para WebSockets
- **Producción**: Dominio DuckDNS/real domain
- **Desarrollo**: HTTP localhost

### Variables de Entorno
- **Plantilla**: `infra/.env.example` (nunca commiteado, solo `.env.local`)
- **Variables críticas**: `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `JWT_SECRET`, `ACCESS_TOKEN_EXPIRE_HOURS`
- **Regla**: `.env` en `.gitignore`, secrets en Dokploy UI para producción

---

## 📐 Arquitectura & Patrones

### Spec-First (Regla AGENTS.md)
1. Modificar `specs/openapi.yaml` (contrato OpenAPI 3.1)
2. Actualizar `PDR.yaml` (requerimientos maestros)
3. Implementar en `backend/app/`
4. Generar migración: `alembic revision --autogenerate -m "descripción"`
5. Ejecutar: `alembic upgrade head`
6. Actualizar types frontend: `npm run gen:types` (en `frontend/`)
7. Lint/typecheck: `ruff check backend/` + `mypy backend/app --strict`
8. Tests: `pytest backend/tests/ -x` + `npx playwright test`

### Arquitectura Modular (PDR.yaml)
- **Bounded Contexts**: auth, pos, catalog, reporting, inventory
- **Sin DDD pesado**: Arquitectura simple y clara
- **Responsabilidad clara**: Cada contexto duele su dominio
- **Escalable a microservicios futuros**

### Lint + Type Check (Calidad)
- **Ruff**: `ruff check backend/` / `ruff format backend/`
  - `line-length = 100`, `select = ["E", "F", "W", "I", "UP", "B", "SIM"]`, `ignore = ["E501"]`
- **Mypy strict**: `mypy backend/app --strict` (`strict = true` en `pyproject.toml`)
- **Commit conventions**: `feat: ...`, `fix: ...`, `docs: ...`, `refactor: ...`

### Testing en Capas
- **Unit**: `pytest` - services, scopes, cálculos de pagos parciales
- **Integration**: Endpoints reales con BD en memoria
- **E2E**: `playwright` - flow completo login→mesa→orden→pago→reporte
- **Contract**: `pact` - schemas frontend <-> backend (planeado)
- **Security**: `owasp-zap` - escaneo de endpoints

---

## 📦 Dependencias Clave (pyproject.toml)

### Producción
- `fastapi>=0.115`, `uvicorn[standard]>=0.32`
- `sqlalchemy>=2.0.36`, `psycopg[binary]>=3.2`
- `alembic>=1.14`, `pydantic-settings>=2.6`
- `slowapi>=0.2.0` (rate-limiting), `python-dotenv>=1.0`
- `pwdlib[argon2]` (hash passwords), `pyjwt>=2.9`, `email-validator>=2.2`

### Desarrollo
- `ruff>=0.8` (lint + format), `mypy>=1.13` (types estrictos)
- `pytest>=8.3`, `pytest-asyncio>=0.25`, `httpx>=0.28`
- `openapi-typescript>=7.4` (generar types frontend)

---

## 🚀 Flujo de Trabajo Recomendado

```
1. Modificar specs/openapi.yaml (nuevo endpoint o cambio)
2. Actualizar PDR.yaml si cambia lógica de negocio
3. Implementar en backend/app/ (routers + services + models)
4. Generar migración: alembic revision --autogenerate -m "feat:..."
5. Aplicar: alembic upgrade head
6. Actualizar types frontend: `npm run gen:types` (en `frontend/`)
7. Lint/typecheck: ruff check backend/ && mypy backend/app --strict
8. Tests: pytest backend/tests/ -x && npx playwright test
9. Docker: cd infra && docker compose up --build
```

---

## 📋 Resumen Rápido

| Área | Skill Principal | Herramienta |
|------|----------------|-------------|
| Backend | FastAPI + SQLAlchemy 2.0 | `uvicorn`, `alembic`, `psycopg` |
| Security | JWT + Argon2id | `fastapi`, `pwdlib`, `pyjwt` |
| Rate Limit | slowapi | `SlowAPIMiddleware`, `Limiter` |
| Lint/Types | Ruff + Mypy | `ruff check`, `mypy --strict` |
| Testing | pytest + Playwright | `pytest`, `npx playwright test` |
| API Contract | OpenAPI 3.1 | `specs/openapi.yaml`, `PDR.yaml` |
| Infra | Docker + Caddy | `docker compose`, `Caddyfile` |
| Frontend | Next.js 16 + TS | `app router`, `tanstack query`, `zustand` |

---

**Fuente de verdad**: `specs/PDR.yaml` (requerimientos técnicos) + `specs/openapi.yaml` (contrato API)
**Convenciones**: `AGENTS.md` (lint, types, commits) + `Commit conventions` (conventional commits)