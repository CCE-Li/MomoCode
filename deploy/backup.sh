#!/usr/bin/env sh
set -eu

STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
mkdir -p backups
TARGET="backups/momocode-${STAMP}.dump"

docker compose -f docker-compose.prod.yml exec -T db sh -c \
  'pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Fc > /tmp/momocode-backup.dump'
docker cp "$(docker compose -f docker-compose.prod.yml ps -q db):/tmp/momocode-backup.dump" "$TARGET"
docker compose -f docker-compose.prod.yml exec -T db rm -f /tmp/momocode-backup.dump

echo "Backup written to ${TARGET}"
