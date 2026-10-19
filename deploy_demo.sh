#!/bin/bash
#
# Deploy TAMRIS DEMO on Hostinger. Same order as deploy_live.sh, so the demo is a
# real rehearsal of the live deployment: back up, build, migrate, then switch.
#
# To rehearse with real data, restore a copy of the live database into the demo
# database first (see the note printed at the end).

set -euo pipefail

COMPOSE="docker compose -f docker-compose.demo.yml"
BACKUP_DIR="${BACKUP_DIR:-$HOME/backups/demo}"
STAMP="$(date +%F_%H%M)"
mkdir -p "$BACKUP_DIR"

echo "Starting Deployment for TAMRIS DEMO on Hostinger..."

# 1. Backup -------------------------------------------------------------------
if $COMPOSE ps --status running --services 2>/dev/null | grep -qx db-demo; then
    echo "Backing up the demo database to $BACKUP_DIR/db_$STAMP.dump ..."
    $COMPOSE exec -T db-demo sh -c 'pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Fc' > "$BACKUP_DIR/db_$STAMP.dump"
    git rev-parse HEAD > "$BACKUP_DIR/commit_$STAMP.txt" 2>/dev/null || true
fi

# 2. Build --------------------------------------------------------------------
echo "Building the new image..."
$COMPOSE build web-demo

# 3. Migrate ------------------------------------------------------------------
$COMPOSE up -d db-demo
for i in $(seq 1 30); do
    if $COMPOSE exec -T db-demo sh -c 'pg_isready -U "$POSTGRES_USER" -d "$POSTGRES_DB"' >/dev/null 2>&1; then break; fi
    sleep 2
done
echo "Migrations that will run:"
$COMPOSE run --rm web-demo python manage.py migrate --plan
echo "Running database migrations..."
$COMPOSE run --rm web-demo python manage.py migrate --noinput

# 4. Switch -------------------------------------------------------------------
echo "Switching to the new code..."
$COMPOSE up -d

$COMPOSE exec -T web-demo python manage.py store_existing_numbers
$COMPOSE exec -T web-demo python manage.py collectstatic --noinput
$COMPOSE exec -T web-demo python manage.py seed_roles
$COMPOSE exec -T web-demo python manage.py seed_fees

echo
echo "DEMO Deployment completed successfully! The app should now be running on port 8080."
echo
echo "To rehearse with a copy of live data (run BEFORE this script next time):"
echo "  docker compose exec -T db sh -c 'pg_dump -U \"\$POSTGRES_USER\" -d \"\$POSTGRES_DB\" -Fc' > /tmp/live.dump"
echo "  $COMPOSE exec -T db-demo sh -c 'pg_restore --clean --if-exists --no-owner -U \"\$POSTGRES_USER\" -d \"\$POSTGRES_DB\"' < /tmp/live.dump"
echo "Uploaded files are not copied; documents will show as missing links on the demo."
