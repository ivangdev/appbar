# AGENTS.md — Convenciones del repositorio

## Project Purpose
POS web para bar: Next.js (frontend) + FastAPI (backend) + PostgreSQL. Spec-Driven Development (PDR.yaml es la fuente de verdad).

## Project Structure
```
app-bar/
├── specs/PDR.yaml          # Spec maestra (requerimientos técnicos)
├── docs/CLIENT_SPEC.md     # Requisitos para cliente
├── AGENTS.md               # Este archivo
├── backend/                # FastAPI + SQLAlchemy + Alembic
├── frontend/               # Next.js 16 (App Router, TypeScript)
└── infra/                  # docker-compose, Caddyfile, .env.example
```

## How to Run Locally
```bash
cd infra
cp .env.example .env
docker compose up --build
# Backend: http://localhost:8000/docs
# Frontend: http://localhost:3000
```

## Backend — FastAPI
- Lint: `ruff check backend/` / `ruff format backend/`
- Types: `mypy backend/app --strict`
- Tests: `pytest backend/tests/ -x`
- Migrations: `alembic upgrade head` (dir: `backend/`)
- Regla: **Spec-First** → siempre que endpoints cambian, actualizar `specs/openapi.yaml` y `PDR.yaml` primero.

## Frontend — Next.js
- Dev: `npm run dev` (en frontend/)
- Lint: `npm run lint` / `npm run format`
- Tests: `npx playwright test`

## Security
- JWT en HttpOnly cookie (`SameSite=Lax`, `Secure`).
- Passwords con Argon2id (`pwdlib`).
- Rate-limit con `slowapi`.
- Nada de secrets en código → usar `.env`.

## Commit conventions
`feat: ...`, `fix: ...`, `docs: ...`, `refactor: ...` (conventional commits)
