# ✅ POS Bar — Plan de trabajo incremental (specs-first)

Fuente de verdad: `specs/PDR.yaml` (v1.3). Spec REST: `specs/openapi.yaml` (v1.3.0).

## Decisiones cerradas (specs v1.3)
- [x] Dinero en **pesos COP enteros** (sin centavos); redondeo `ROUND_HALF_UP`.
- [x] `product.cost` visible **solo admin**; el mesero ve `price`.
- [x] Editar item: `quantity >= paid_quantity` (si se intenta bajar → 409).
- [x] Cancelar pago en orden `paid` → revierte estado (`paid_at = null`).
- [x] WebSocket autenticado por **cookie HttpOnly** (token nunca en la URL).

## Decisiones cerradas (specs v1.2)
- [x] Mesa enum = `free` / `occupied` (se eliminó `paying`).
- [x] Mesa `free` ⟺ `remaining == 0`; se recalcula tras cada operación.
- [x] Token JWT `access_exp = 24h`, **sin refresh token**.
- [x] Pago parcial **por ítem/cantidad** (pokers) → `payment_allocations`.
- [x] Pago **total** sin seleccionar ítems (auto-asigna pendientes).
- [x] Cancelar pago → orden vuelve a `closed`; si `amount_paid > 0` → `partially_paid`.
- [x] Reportes/cortes en TZ `America/Bogota`.
- [x] Deploy objetivo: **Dokploy** (Docker en VPS) — sin pgAdmin.

## Step 0 — Fundamentos (HECHO)
- [x] `AGENTS.md`, `.gitignore`
- [x] `specs/PDR.yaml` (v1.2)
- [x] `specs/openapi.yaml` (v1.2.0, validado)
- [x] `docs/CLIENT_SPEC.md`
- [x] Estructura de carpetas vacías (`backend/ frontend/ infra/ *.gitkeep`)

## Fase 1 — Base de datos (HECHA)
- [x] `infra/docker-compose.yml` (PostgreSQL 16; sin pgAdmin)
- [x] `infra/.env.example` (DB creds, `JWT_SECRET`, `DATABASE_URL`)
- [x] `backend/alembic.ini` + `backend/alembic/env.py`
- [x] Migración `471de3a826ee_init_schema` alineada a `PDR.yaml`:
  - [x] users, categories, products, tables, orders, order_items, payments, **payment_allocations**
  - [x] 11 `CHECK` (roles, status, métodos, montos, `paid_quantity ≤ quantity`) verificados
  - [x] 1 orden activa por mesa (índice único parcial) verificada
  - [x] `lower(email)` único verificado
- [x] Migración `5b75bd615613_money_and_quantity_as_integer_cop` (dinero/cantidad en enteros COP)
- [x] `alembic upgrade head` verificado (9 tablas: 8 + `alembic_version`; 12 columnas `integer`)

## Fase 2 — Auth (HECHA)
- [x] `app/core/security.py` (Argon2id con `pwdlib` + JWT HS256 con `PyJWT`)
- [x] `app/schemas/user.py` + `app/schemas/auth.py` (Pydantic v2)
- [x] `app/api/deps.py` (`get_current_user` por cookie + `require_role`)
- [x] `app/api/v1/auth.py` (`POST /token`, `POST /logout`, `GET /me`)
- [x] `app/main.py` (FastAPI + router `/v1` + `/health`)
- [x] Cookie HttpOnly (`SameSite=Lax`, `Max-Age=86400`, `Secure` por `COOKIE_SECURE`)
- [x] Seed `app/db/seed.py` — admin@posbar.com / admin12345 · mesero@posbar.com / mesero12345
- [x] Tests `tests/` (9 pasan): security + auth (login, cookie, `/me`, 401/403)
- [x] `ruff` + `mypy --strict` OK

## Fase 3 — Catálogo (HECHA)
- [x] `app/schemas/category.py`, `app/schemas/product.py`
- [x] `api/v1/categories.py` — GET (activas para mesero) + POST/PUT/DELETE (admin, soft-delete)
- [x] `api/v1/products.py` — GET `?category_id=` + POST/PUT/DELETE (admin)
- [x] `cost` visible **solo admin** (union `ProductRead | ProductReadAdmin`, verificado)
- [x] Rutas alineadas a la spec: `/categories/{id}`, `/products/{id}`
- [x] Tests `tests/test_catalog.py` (17 tests en total, todos pasan)

## Fase 4 — POS (HECHA)
- [x] `app/schemas/table.py`, `app/schemas/order.py`, `app/schemas/payment.py`
- [x] `app/services/orders.py` (recalculo de montos + transiciones de estado + eventos)
- [x] `api/v1/tables.py` — GET (mesero/admin) + POST/PATCH/DELETE (admin)
- [x] `orders`: open → close → pay (parcial por ítem / total) → paid / cancelled
- [x] `GET /orders?table_id=` (orden activa de la mesa; 404 si no hay)
- [x] `order_items` add/edit/delete (409 si `quantity < paid_quantity`; no borrar ítem con pagos)
- [x] `pay` con `allocations:[{item_id, quantity}]` + pago total sin allocations
- [x] `payments/{id}/cancel` (revierte allocations; orden → `closed` si `amount_paid==0`)
- [x] `orders/history` (TZ `America/Bogota`)
- [x] WebSocket `/ws/tables` (auth por cookie HttpOnly; eventos `new_order`, `order_closed`,
      `order_cancelled`, `order_updated`, `payment_made`, `order_paid`, `payment_cancelled`,
      `table_status_update`)
- [x] Tests `tests/{test_tables,test_orders,test_payments,test_ws}.py` (43 en total, todos pasan)
- [x] `ruff` + `mypy --strict` OK

## Fase 5 — Reporting (HECHA)
- [x] `app/schemas/report.py` (DailyReport, ReportByTable, ReportByProduct)
- [x] `api/v1/reports.py` — `GET /reports/daily?date=` (TZ `America/Bogota`, solo órdenes `paid`)
- [x] `reports/daily` (by_table, by_product, total) — alcance `waiter`+`admin`
- [x] Tests `tests/test_reports.py` (52 en total, todos pasan)
- [x] Endpoints de usuarios `api/v1/users.py` (GET/POST/PATCH/DELETE, soft-deactivate)
- [x] `ruff` + `mypy --strict` OK

## Fase 6 — Frontend (Next 16 App Router + TS + Tailwind + shadcn/ui) (HECHA)
- [x] Scaffold: `package.json` (Next 16.4, React 19, TanStack Query v5, axios, Zustand),
      `tsconfig.json`, `next.config.ts` (rewrite `/api/*` + `output: standalone`),
      `postcss.config.mjs` (Tailwind v4), `eslint.config.mjs` (flat), `vitest.config.ts`
- [x] `lib/api.ts` (axios + cookie), `lib/api-types.ts` (**generado** por `npm run gen:types`),
      `lib/types.ts` (derivado del contrato), `lib/utils.ts` (`cn`, `formatCOP`),
      `hooks/use-tables-socket.ts` (WebSocket por cookie), `stores/auth.ts` (Zustand)
- [x] UI primitives `components/ui/{button,input,card}.tsx`
- [x] Layout + `RequireAuth` + `Nav` (cookie, redirect a `/login`)
- [x] Página login + protector de rutas (cookie)
- [x] Dashboard mesas (grid free/occupied, vivo por WebSocket)
- [x] Vista orden: agregar items, notas, **abonar ítems (pokers)**, **pagar total**, cancelar pago/orden
- [x] Corte de día (waiter+admin)
- [x] Admin: categorías/productos/mesas/usuarios CRUD (con `cost` solo admin)
- [x] `npm run build` OK · `npm run lint` OK · `vitest` (8 tests) OK · `prettier` OK

## Fase 7 — Infra / Deploy (Dokploy)
- [x] `backend/Dockerfile` (python 3.12-slim, multi-stage, healthcheck, `alembic upgrade head` al arrancar)
- [x] `frontend/Dockerfile` (node 22-alpine, standalone) + `public/`
- [x] `.dockerignore` backend y frontend
- [x] `infra/docker-compose.yml` — stack completo (db + backend + frontend)
- [x] `infra/Caddyfile` (HTTPS + reverse proxy: `/ws/*` → backend, resto → frontend)
- [x] `infra/.env.example` ampliado (`COOKIE_SECURE`, `NEXT_PUBLIC_API_URL`)
- [x] Post-deploy hook: `alembic upgrade head` (en el `CMD` del Dockerfile backend)
- [x] Hardening: rate-limit (`slowapi`) conectado — login `20/min`, pagos `60/min`,
      reportes `120/min` (429 documentado en OpenAPI); `RATE_LIMIT_ENABLED` configurable;
      uvicorn con `--proxy-headers` para IP real tras Caddy. CORS no hace falta
      (proxy same-origin); `COOKIE_SECURE=True` en producción.
- [x] Lint/types/tests:
  - Backend `ruff check` · `mypy --strict` · `pytest` (53 ✓)
  - Frontend `npm run lint` · `npm run build` · `vitest` (8 ✓)
  - OpenAPI validado (`$ref` rotos = 0)

## Estado de validación continua
- [x] `openapi.yaml` válido + refs OK (v1.3.0)
- [x] Migraciones alineadas al `PDR.yaml` (spec-driven)
- [x] 53 tests backend pasando (`pytest tests/ -q`)
- [x] Frontend construye y pasa lint + vitest

## Incidencias
- [x] Reparados `app/api/v1/auth.py` y `app/schemas/user.py` (habían quedado como
      stubs rotos por un escritor concurrente) y `app/schemas/product.py`
      (`ConfigDict(strategy="lax")` inválido).
- [x] `app/core/constants.py` y `app/core/rate_limit.py` **adoptados**: constantes
      usadas por el rate-limit (`AUTH_RATE_LIMIT`, `WRITE_RATE_LIMIT`, `READ_ONLY_RATE_LIMIT`).
- [x] Rate-limit con `slowapi` conectado (login/pagos/reportes) + test `test_rate_limit.py`.
- [x] **Consistencia spec↔código**: la spec declaraba el evento WS `item_paid` que el backend
      nunca emite; se corrigió a los 8 eventos reales (`table_status_update`, `new_order`,
      `order_updated`, `order_closed`, `order_cancelled`, `payment_made`, `payment_cancelled`,
      `order_paid`) en `openapi.yaml` y `PDR.yaml`.
- [x] **Contrato tipado**: `openapi-typescript` (devDep `^7.4`) + script `gen:types`;
      `lib/types.ts` ahora deriva de `lib/api-types.ts` (generado). `OrderRead`/`DailyReport`
      marcados como requeridos en la spec para reflejar la respuesta real.
- [x] **Bug**: `logout()` del store re-lanzaba el error → `router.replace("/login")` no corría.
      Ahora limpia la sesión local siempre.
- [x] Tests unitarios nuevos: `tests/auth-store.test.ts` + `tests/use-tables-socket.test.ts`.
- [x] E2E completo `e2e/full-flow.spec.ts` (login→catálogo→mesa→orden→pago→reporte).
- [ ] E2E Playwright (`frontend/e2e/`) requiere `npx playwright install` (navegadores)
      y el stack levantado (`docker compose up`); no se ejecutó en este entorno.
- [ ] No se pudo *construir* las imágenes Docker aquí (usuario `krei` sin acceso al
      daemon Docker). Los Dockerfile/compose se validaron estáticamente.
