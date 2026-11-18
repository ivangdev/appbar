# Changelog

Todas las versiones relevantes del POS Bar. Formato basado en *Keep a Changelog*.

## [1.0.0] — 2026-11-18

Primera versión de producción (MVP).

### Agregado
- Autenticación con JWT en cookie HttpOnly, Argon2id y rate limiting en login/pagos/reportes.
- Tablero de mesas en tiempo real por WebSocket autenticado por cookie.
- Órdenes: items, notas, cantidades, cierre, cancelación e historial con filtro por fecha.
- Pagos parciales por ítem/cantidad, pago total y anulación de abonos con auditoría
  (`cancelled_at`, `cancelled_by`).
- Reporte diario en `America/Bogota` con exportación CSV.
- Administración de categorías, productos, mesas y usuarios (incluye reset de password).
- Endpoints `/health` y `/health/ready` y validación de configuración de producción.
- Specs sincronizadas: PDR 1.4 y OpenAPI 1.4.0 con tipos TS generados.
- CI con PostgreSQL: lint, tipos, tests, build, contrato OpenAPI, auditoría de
  dependencias de producción y E2E con Docker Compose.
- E2E de flujo completo, WebSocket con dos sesiones, exportación CSV y viewport móvil.
- Scripts de backup/restore de PostgreSQL y guía de despliegue (incluye acceso por VPN).

### Corregido
- Limpieza de notas de ítems (`null`) y bloqueo de mesas por órdenes cerradas vacías.
- WebSocket same-origin cuando `NEXT_PUBLIC_API_URL` está vacío.
- Protección del último administrador activo y del propio usuario.
- Actualización de Next.js 16.4.0 → 16.4.6 (advisory de seguridad).
- Dependencias: `shadcn` movido a desarrollo; `npm audit --omit=dev` queda en 0.

### Verificado
- 74 tests backend, 11 tests frontend, 10 E2E (escritorio + móvil) contra el stack Docker.
- `ruff`, `mypy --strict`, `eslint`, `tsc --noEmit`, `next build` y generación de tipos.
- Backup y restore reales sobre PostgreSQL 16.
