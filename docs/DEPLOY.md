# Despliegue — POS Bar

Guía operativa para llevar el stack a producción en el VPS, mantenerlo y
verificarlo. La fuente de verdad de las reglas de negocio es `specs/PDR.yaml`.

## 1. Arquitectura

```
navegador ──HTTPS/WSS──> Caddy (:80/:443) ──> frontend (Next.js, :3000)
                                          └──> backend  (FastAPI, :8000) ──> PostgreSQL 16
```

- El frontend hace de proxy same-origin: `/api/*` → backend. Así la cookie
  **HttpOnly** viaja sin CORS.
- Caddy enruta `/ws/*` y `/health*` directo al backend; el resto al frontend
  (ver `infra/Caddyfile`).
- En producción el navegador no necesita saber la URL del backend: deja
  `NEXT_PUBLIC_API_URL` **vacío** para usar el origin actual (`wss://...`).

## 2. Red del servidor

| Nombre | Valor | Uso |
|---|---|---|
| IP pública (WAN del router) | `186.144.148.182` | HTTPS del POS desde cualquier lugar |
| IP del VPS en la VPN | `192.168.80.17` | SSH y administración |
| Router | `192.168.80.1` | Redirección de puertos |

Comprobación en el servidor (necesita `curl`, o `wget -qO-` / `python3`):

```bash
curl -4 -s https://api.ipify.org; echo   # 186.144.148.182
ip -4 -br addr                          # ens18: 192.168.80.17/24
ss -ltnp | grep -E ':(80|443)\b' || echo "libres"
```

### Redirección de puertos (router)

En `http://192.168.80.1` → *Port Forwarding*, añadir:

| Puerto externo | IP interna | Puerto interno | Protocolo |
|---|---|---|---|
| 80 | `192.168.80.17` | 80 | TCP |
| 443 | `192.168.80.17` | 443 | TCP |

El 22 **no** se publica: SSH sigue siendo solo por VPN (el router ya redirige
el puerto externo de OpenVPN). No exponer PostgreSQL ni el backend.

> Docker publica puertos con `iptables` directamente y **ignora `ufw`**. El
> cortafuegos efectivo es el router. Por eso el override de producción no
> publica los puertos internos.

## 3. Dominio gratuito y HTTPS

Caddy obtiene el certificado con el reto **HTTP-01**, que solo necesita el
puerto 80 abierto. No hay que comprar dominio ni usar DNS-01.

Opciones gratuitas:

| Proveedor | Nombre | Comentario |
|---|---|---|
| **DuckDNS** | `posbar.duckdns.org` | Login con GitHub/Google, token inmediato. Recomendado. |
| deSEC | `posbar.dedyn.io` | Requiere registro con correo. Más robusto. |

El registro `A` debe apuntar a `186.144.148.182`. DuckDNS actualiza la IP solo;
con deSEC hay que publicar la IP con su API.

Si el ISP cambia la IP (lo habitual en conexiones residenciales), mantener el
registro actualizado con cron en el VPS:

```cron
*/5 * * * * curl -fsS 'https://www.duckdns.org/update?domains=TU_SUBDOMINIO&token=TU_TOKEN&ip=' >/dev/null 2>&1
```

El `DOMAIN` de `infra/.env` debe ser exactamente ese nombre.

## 3.1. Acceso sin abrir el router (túnel saliente)

Si no se tiene acceso administrativo al router (por ejemplo, equipo gestionado
por el ISP), se puede publicar el POS con un túnel saliente. No abre puertos y
no requiere dominio de pago:

```bash
# En el VPS, una sola vez:
mkdir -p ~/.local/bin
curl -fsSL -o ~/.local/bin/cloudflared \
  https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64
chmod +x ~/.local/bin/cloudflared
```

Servicio `~/.config/systemd/user/cloudflared-posbar.service`:

```ini
[Unit]
Description=Cloudflare Quick Tunnel para POS Bar
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
ExecStart=/home/ivan/.local/bin/cloudflared tunnel --no-autoupdate --url http://localhost:80
Restart=always
RestartSec=5

[Install]
WantedBy=default.target
```

```bash
systemctl --user daemon-reload
systemctl --user enable --now cloudflared-posbar.service
sudo loginctl enable-linger ivan     # para que arranque aunque no haya login
```

El `Caddyfile` incluye un site `http://` catch-all que enruta cualquier Host
recibido por el puerto 80 exactamente igual que el dominio principal
(`/ws/*` y `/health*` al backend, resto al frontend). Así el túnel entra por
Caddy y no hay que duplicar el ruteo.

Para saber la URL asignada:

```bash
journalctl --user -u cloudflared-posbar.service --no-pager -n 80 \
  | grep -oE 'https://[a-z0-9-]+\.trycloudflare\.com' | tail -1
```

**Limitación:** un *Quick Tunnel* asigna una URL aleatoria que cambia cuando se
reinicia el servicio o el servidor. Es adecuada para pruebas y acceso inmediato,
pero **no es una dirección permanente**. Para una URL fija sin tocar el router,
hay que usar un túnel nombrado de Cloudflare con un dominio propio (de pago) o
abrir los puertos 80/443 en el router y usar el dominio gratuito DuckDNS.

## 4. Variables de entorno

Copiar `infra/.env.example` a `infra/.env` en el VPS y ajustar:

| Variable | Producción | Nota |
|---|---|---|
| `APP_ENV` | `production` | Activa la validación de seguridad al arrancar |
| `DOMAIN` | `posbar.duckdns.org` | Lo usa Caddy para el certificado |
| `POSTGRES_DB` / `POSTGRES_USER` | `pos_bar` / `pos_user` | |
| `POSTGRES_PASSWORD` | aleatoria | `openssl rand -base64 24` |
| `JWT_SECRET` | ≥ 48 chars aleatorio | `openssl rand -hex 32` |
| `COOKIE_SECURE` | `True` | Obligatorio con HTTPS |
| `RATE_LIMIT_ENABLED` | `True` | |
| `INITIAL_ADMIN_EMAIL` | tu correo | Se crea si no existe (idempotente) |
| `INITIAL_ADMIN_PASSWORD` | fuerte, distinta de la default | Cámbiala tras el primer login |
| `SEED_DEMO_USERS` | `False` | No crear meseros de ejemplo |
| `NEXT_PUBLIC_API_URL` | **vacío** | Build-time: exige rebuild |

Con `APP_ENV=production` la app **falla al arrancar** si detecta el secreto de
desarrollo, `JWT_SECRET` corto, `COOKIE_SECURE=False`, la password de admin por
defecto o `SEED_DEMO_USERS=True`.

## 5. Despliegue en el VPS

Preparación única (si Docker no está instalado):

```bash
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER && newgrp docker
```

Copiar el repo al servidor y arrancar:

```bash
# Desde tu máquina, con la VPN conectada:
rsync -av --exclude '.git' --exclude 'frontend/node_modules' --exclude 'backend/.venv' \
  /home/krei/Dev/app-bar/ ivan@192.168.80.17:~/app-bar/

# En el VPS:
cd ~/app-bar/infra
cp .env.example .env            # editar según la tabla anterior
chmod 600 .env

docker compose -f docker-compose.yml -f docker-compose.prod.yml \
  --profile proxy up -d --build
docker compose -f docker-compose.yml -f docker-compose.prod.yml ps
```

`infra/docker-compose.prod.yml` usa `ports: !reset []` para quitar los puertos
publicados del compose base. Sin ese override, quedarían expuestos `5432`,
`8000` y `3000`.

Verificación:

```bash
curl -fsS https://TU_DOMINIO/health/ready     # {"status":"ready"}
curl -fsSI https://TU_DOMINIO | head -5       # 200/301 y cabeceras de seguridad
docker compose -f docker-compose.yml -f docker-compose.prod.yml logs --tail=50 caddy
```

Desde el celular **con datos móviles** (sin VPN) comprobar que carga
`https://TU_DOMINIO/login`.

### Actualizaciones

```bash
cd ~/app-bar && git pull
cd infra && docker compose -f docker-compose.yml -f docker-compose.prod.yml \
  --profile proxy up -d --build
```

`NEXT_PUBLIC_API_URL` es un *build arg*: si cambia, hay que recrear la imagen
de frontend (`--build`).

## 6. Desarrollo local

```bash
cd infra && cp .env.example .env
docker compose up --build                       # http://localhost:3000
docker compose --profile proxy up -d --build    # https://pos.localhost
```

Tests y calidad (ver `AGENTS.md`):

```bash
pytest backend/tests/ -x
npm run lint && npx tsc --noEmit && npx vitest run && npm run build
E2E_BASE_URL=http://localhost:3000 npx playwright test
```

## 7. Alternativa: Dokploy (no usada en esta entrega)

Dokploy es gratuito pero **no proporciona HTTPS gratis**: sus dominios
`sslip.io` integrados son solo HTTP. Requiere un dominio propio y añade
Traefik, Swarm y un panel (~500 MB–1 GB extra). Para un único servicio se
prefirieron Caddy y el compose, que ya están verificados y son reproducibles
desde el repo. Si en el futuro se alojan varias apps en el mismo servidor,
Dokploy pasa a ser una opción razonable.

## 8. Migraciones y seed

- Al arrancar el contenedor: `alembic upgrade head && python -m app.db.seed`.
- Manual:
  ```bash
  docker compose exec backend alembic upgrade head
  docker compose exec backend python -m app.db.seed
  ```
- El seed crea el admin inicial **solo si su email no existe**; nunca
  sobreescribe passwords.
- Reset de password: `PATCH /v1/users/{id}` con `{"password": "..."}` desde
  una sesión de admin (también en Admin → Usuarios).

## 9. Backups de PostgreSQL

Los scripts `infra/backup.sh` e `infra/restore.sh` usan el formato custom de
`pg_dump` (más seguro para restaurar):

```bash
cd ~/app-bar/infra
./backup.sh                      # crea backups/posbar-<fecha>.dump
BACKUP_DIR=/var/backups/posbar ./backup.sh
./restore.sh backups/posbar-2026-11-18-120000.dump
```

Respaldo diario con cron:

```cron
0 3 * * * cd /home/ivan/app-bar/infra && BACKUP_DIR=/var/backups/posbar ./backup.sh >> /var/log/posbar-backup.log 2>&1
```

Recomendaciones:

- Retención mínima: 7 diarios + 4 semanales.
- Guardar copias fuera del VPS (S3/Backblaze/otro host).
- Probar el restore al menos una vez antes de la entrega.
- `docker compose down` **sin** `-v` conserva el volumen `db_data`.

## 10. Rotación de secretos

- `JWT_SECRET`: al cambiarlo se invalidan todas las sesiones. Hazlo fuera de
  horario de servicio.
- `POSTGRES_PASSWORD`: cambiar en la BD y en el entorno del backend a la vez;
  luego reiniciar el backend.
- Passwords de usuarios: reset por admin (ver §8).

## 11. Checklist de producción

- [ ] VPN conectada y acceso verificado a `192.168.80.17`
- [ ] Router redirigiendo 80 y 443 al VPS
- [ ] Dominio gratuito apuntando a `186.144.148.182` y certificado válido
- [ ] Sin puertos 5432/8000/3000 publicados (`docker compose ps`)
- [ ] `APP_ENV=production`, `COOKIE_SECURE=True`, `SEED_DEMO_USERS=False`
- [ ] `JWT_SECRET` y `POSTGRES_PASSWORD` aleatorios y guardados fuera del repo
- [ ] Password del admin inicial cambiada tras el primer login
- [ ] HTTPS válido y WebSocket funcionando por `wss://`
- [ ] `/health` y `/health/ready` en verde
- [ ] Backup automático configurado + restore probado
- [ ] Logs sin errores 5xx en el smoke test (`docs/ACEPTACION.md`)
- [ ] Usuarios reales creados y usuarios demo desactivados

## 12. Troubleshooting

| Síntoma | Causa probable | Acción |
|---|---|---|
| Caddy no obtiene certificado | 80 no redirigido o dominio mal escrito | Revisar router, DNS y `logs caddy` |
| El backend no arranca en prod | Validación de configuración | Leer el error: indica la variable insegura |
| Login responde 401 tras reiniciar | `JWT_SECRET` cambió | Volver a iniciar sesión (esperado) |
| El tablero no se actualiza | WS bloqueado por proxy | Enrutar `/ws/*` al backend y permitir upgrade |
| `401` en el frontend | Cookie `Secure` sobre HTTP | Usar HTTPS o `COOKIE_SECURE=False` en dev |
| 429 en login | Rate limit (20/min por IP) | Esperar la ventana o revisar `RATE_LIMIT_ENABLED` |
| Docker expone puertos que no quería | Falta el override de producción | Usar `-f docker-compose.prod.yml` con `!reset` |
