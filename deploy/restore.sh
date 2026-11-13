#!/usr/bin/env sh
set -eu

if [ "$#" -ne 1 ]; then
  echo "Usage: $0 <backup.dump>" >&2
  exit 2
fi

BACKUP="$1"
if [ ! -f "$BACKUP" ]; then
  echo "Backup not found: $BACKUP" >&2
  exit 2
fi

CONTAINER="$(docker compose -f docker-compose.prod.yml ps -q db)"
docker cp "$BACKUP" "${CONTAINER}:/tmp/momocode-restore.dump"
docker compose -f docker-compose.prod.yml exec -T db sh -c \
  'pg_restore -U "$POSTGRES_USER" -d "$POSTGRES_DB" --clean --if-exists /tmp/momocode-restore.dump'
docker compose -f docker-compose.prod.yml exec -T db rm -f /tmp/momocode-restore.dump

echo "Restore completed from ${BACKUP}"
