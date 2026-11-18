#!/usr/bin/env bash
# Restaura un backup creado por backup.sh. ADVERTENCIA: reemplaza los datos actuales.
# Uso: ./restore.sh backups/posbar-2026-11-18-120000.dump
set -euo pipefail

cd "$(dirname "$0")"

FILE="${1:-}"
if [[ -z "$FILE" || ! -f "$FILE" ]]; then
  echo "Uso: $0 <archivo.dump>" >&2
  exit 1
fi

if [[ ! -f .env ]]; then
  echo "Falta infra/.env" >&2
  exit 1
fi
set -a
# shellcheck disable=SC1091
. ./.env
set +a

: "${POSTGRES_USER:?POSTGRES_USER requerido}"
: "${POSTGRES_DB:?POSTGRES_DB requerido}"

echo "Va a RESTAURAR $FILE sobre la base '$POSTGRES_DB'."
echo "Se recomienda hacer un backup antes (./backup.sh)."
read -r -p "Escribe SI para continuar: " CONFIRM
if [[ "$CONFIRM" != "SI" ]]; then
  echo "Cancelado."
  exit 0
fi

docker compose exec -T db \
  pg_restore -U "$POSTGRES_USER" -d "$POSTGRES_DB" \
  --clean --if-exists --no-owner --no-privileges < "$FILE"

echo "Restore completado. Verifica: curl -fsS http://localhost:8000/health/ready"
