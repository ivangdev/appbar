#!/usr/bin/env bash
# Backup de PostgreSQL del stack POS Bar (formato custom de pg_dump).
# Uso: ./backup.sh
# Variables opcionales: BACKUP_DIR (default ./backups), RETENTION_DAYS (default 7).
set -euo pipefail

cd "$(dirname "$0")"

if [[ ! -f .env ]]; then
  echo "Falta infra/.env: copia .env.example y configura las variables." >&2
  exit 1
fi
set -a
# shellcheck disable=SC1091
. ./.env
set +a

: "${POSTGRES_USER:?POSTGRES_USER requerido}"
: "${POSTGRES_DB:?POSTGRES_DB requerido}"

BACKUP_DIR="${BACKUP_DIR:-./backups}"
RETENTION_DAYS="${RETENTION_DAYS:-7}"
mkdir -p "$BACKUP_DIR"

STAMP="$(date +%F-%H%M%S)"
TARGET="$BACKUP_DIR/posbar-$STAMP.dump"
TMP="$TARGET.tmp"

docker compose exec -T db \
  pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Fc -Z 6 > "$TMP"
mv "$TMP" "$TARGET"

# Retencion local. Luego copy el archivo a storage externo (S3/Backblaze/otro host).
find "$BACKUP_DIR" -name 'posbar-*.dump' -type f -mtime "+${RETENTION_DAYS}" -delete

echo "Backup creado: $TARGET"
