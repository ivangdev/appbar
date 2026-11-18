# Despliegue — POS Bar

Guía operativa para llevar el stack a producción (VPS con Dokploy o Docker
Compose + Caddy) y mantenerlo.

## 1. Arquitectura

```
navegador ──HTTPS/WSS──> Caddy ──> frontend (Next.js, :3000)
                              └──> backend  (FastAPI,  :8000) ──> PostgreSQL 16
```

- El frontend hace de proxy same-origin: `/api/*` → backend. Así la cookie
  **HttpOnly** viaja sin CORS.
- El WebSocket (`/ws/tables`) va directo al backend (Caddy lo enruta).
- En producción el navegador no necesita saber la URL del backend: deja
  `NEXT_PUBLIC_API_URL` **vacío** para usar el origin actual.

## 2. Variables de entorno

Copia `infra/.env.example` a `infra/.env` (o configúralas en Dokploy).

| Variable | Producción | Nota |
|---|---|---|
| `APP_ENV` | `production` | Activa la validación de seguridad al arrancar |
| `POSTGRES_DB` / `POSTGRES_USER` | los tuyos | |
| `POSTGRES_PASSWORD` | aleatoria | `openssl rand -base64 24` |
| `POSTGRES_HOST` | `db` (compose) | En Dokploy, el host interno del servicio |
| `JWT_SECRET` | ≥ 32 chars aleatorio | `openssl rand -hex 32` |
| `COOKIE_SECURE` | `True` | Obligatorio con HTTPS |
| `RATE_LIMIT_ENABLED` | `True` | |
| `INITIAL_ADMIN_EMAIL` | tu correo | Se crea si no existe (idempotente) |
| `INITIAL_ADMIN_PASSWORD` | ≥ 8 chars, distinta del default | Cámbiala tras el primer login |
| `SEED_DEMO_USERS` | `False` | No crear meseros de ejemplo |
| `NEXT_PUBLIC_API_URL` | vacío (mismo origen) | Build-time: exige rebuild |
| `DOMAIN` | `pos.tudominio.com` | Solo perfil `proxy` (Caddy) |

Con `APP_ENV=production` la app **falla al arrancar** si detecta el secreto de
desarrollo, `JWT_SECRET` corto, `COOKIE_SECURE=False`, la password de admin por
defecto o `SEED_DEMO_USERS=True`.

## 3. Despliegue con Docker Compose

```bash
cd infra
cp .env.example .env      # editar según la tabla anterior
docker compose up -d --build
docker compose ps
curl -fsS http://localhost:8000/health/ready
```

Con HTTPS/WSS (Caddy + Let's Encrypt):

```bash
docker compose --profile proxy up -d --build
```

Caddy usa `DOMAIN`; para pruebas locales `pos.localhost` funciona sin DNS.

## 4. Despliegue en Dokploy

1. Crear un proyecto y una base **PostgreSQL** (o usar el servicio `db` del
   compose). Anotar host/puerto/credenciales internas.
2. Servicio **backend**:
   - Build context: `backend/` (Dockerfile incluido).
   - Variables: las de la tabla (con `POSTGRES_HOST` = host interno de la BD).
   - Puerto: `8000`. Healthcheck: `/health/ready`.
   - El `CMD` ya ejecuta `alembic upgrade head` + seed idempotente al arrancar.
3. Servicio **frontend**:
   - Build context: `frontend/`.
   - Build args: `NEXT_PUBLIC_API_URL=""` y
     `API_INTERNAL_URL=http://<backend-interno>:8000`.
   - Puerto: `3000`.
4. Dominio + TLS: apuntar el dominio al frontend. Caddy/Dokploy debe enrutar
   `/ws/*` al backend (WebSocket) y el resto al frontend, o exponer el backend
   en un subdominio y poner esa URL en `NEXT_PUBLIC_API_URL`.
5. Smoke test: login → abrir mesa → agregar ítem → abono parcial → pago total →
   corte del día. Verificar que otra sesión ve la mesa cambiar sin recargar.

## 5. Migraciones y seed

- Al arrancar el contenedor: `alembic upgrade head && python -m app.db.seed`.
- Manual:
  ```bash
  docker compose exec backend alembic upgrade head
  docker compose exec backend python -m app.db.seed
  ```
- El seed crea el admin inicial **solo si su email no existe**; nunca
  sobreescribe passwords.
- Reset de password de un usuario: `PATCH /v1/users/{id}` con `{"password": "..."}`
  usando una sesión de admin (también disponible en Admin → Usuarios).

## 6. Backups de PostgreSQL

Respaldo diario (ejemplo con cron en el host):

```bash
docker compose exec -T db pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" \
  | gzip > /var/backups/posbar-$(date +%F).sql.gz
```

Restore:

```bash
gunzip -c /var/backups/posbar-2026-11-18.sql.gz \
  | docker compose exec -T db psql -U "$POSTGRES_USER" -d "$POSTGRES_DB"
```

Recomendaciones:

- Retención mínima: 7 diarios + 4 semanales.
- Guardar copias fuera del VPS (S3/Backblaze/otro host).
- Probar el restore al menos una vez antes de la entrega.
- `docker compose down` **sin** `-v` conserva el volumen `db_data`.

## 7. Rotación de secretos

- `JWT_SECRET`: al cambiarlo se invalidan todas las sesiones (los usuarios
  vuelven a hacer login). Hazlo fuera de horario de servicio.
- `POSTGRES_PASSWORD`: cambiar en la BD y en el entorno del backend a la vez;
  luego reiniciar el backend.
- Passwords de usuarios: reset por admin (ver §5).

## 8. Checklist de producción

- [ ] `APP_ENV=production`, `COOKIE_SECURE=True`, `SEED_DEMO_USERS=False`
- [ ] `JWT_SECRET` y `POSTGRES_PASSWORD` aleatorios y guardados en el gestor de secretos
- [ ] Password del admin inicial cambiada tras el primer login
- [ ] HTTPS válido y WebSocket funcionando por `wss://`
- [ ] `/health` y `/health/ready` en verde
- [ ] Backup automático configurado + restore probado
- [ ] Logs accesibles y sin errores 5xx en el smoke test
- [ ] Usuarios reales creados y usuarios demo desactivados
- [ ] Tag de release y handover entregados

## 9. Troubleshooting

| Síntoma | Causa probable | Acción |
|---|---|---|
| El backend no arranca en prod | Validación de configuración | Leer el error: indica la variable insegura |
| Login responde 401 tras reiniciar | `JWT_SECRET` cambió | Volver a iniciar sesión (esperado) |
| El tablero no se actualiza | WS bloqueado por proxy | Enrutar `/ws/*` al backend y permitir upgrade |
| `401` en el frontend | Cookie `Secure` sobre HTTP | Usar HTTPS o `COOKIE_SECURE=False` en dev |
| 429 en login | Rate limit (20/min por IP) | Esperar la ventana o revisar `RATE_LIMIT_ENABLED` |
