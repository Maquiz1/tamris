#!/bin/bash
#
# Deploy TAMRIS (LIVE) on Hostinger.
#
# Order matters on a running system:
#   1. back up the database and uploaded files
#   2. build the new image while the old site keeps serving
#   3. migrate the database (new migrations only add fields, so the old code keeps working)
#   4. switch the containers to the new code
#
# Usage: ./deploy_live.sh            (from the project folder, after git pull)
# Backups go to $BACKUP_DIR (default ~/backups). Copy them off the server regularly.

set -euo pipefail

BACKUP_DIR="${BACKUP_DIR:-$HOME/backups}"
STAMP="$(date +%F_%H%M)"
mkdir -p "$BACKUP_DIR"

echo "Starting Deployment for TAMRIS (LIVE) on Hostinger..."

# 1. Backups -------------------------------------------------------------------
if docker compose ps --status running --services 2>/dev/null | grep -qx db; then
    echo "Backing up the database to $BACKUP_DIR/db_$STAMP.dump ..."
    docker compose exec -T db sh -c 'pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Fc' > "$BACKUP_DIR/db_$STAMP.dump"
    if [ ! -s "$BACKUP_DIR/db_$STAMP.dump" ]; then
        echo "Database backup is empty. Stopping before any change is made." >&2
        exit 1
    fi

    MEDIA_VOLUME="$(docker volume ls --format '{{.Name}}' | grep -E '(^|_)media_volume$' | grep -v demo | head -n1 || true)"
    if [ -n "$MEDIA_VOLUME" ]; then
        echo "Backing up uploaded files ($MEDIA_VOLUME) to $BACKUP_DIR/media_$STAMP.tar.gz ..."
        docker run --rm -v "$MEDIA_VOLUME":/data:ro -v "$BACKUP_DIR":/backup alpine tar czf "/backup/media_$STAMP.tar.gz" -C /data .
    fi
    git rev-parse HEAD > "$BACKUP_DIR/commit_$STAMP.txt" 2>/dev/null || true
else
    echo "Database container is not running yet (first deployment?): skipping backup."
fi

# 2. Build ---------------------------------------------------------------------
echo "Building the new image (the current site keeps running)..."
docker compose build web

# 3. Migrate -------------------------------------------------------------------
echo "Starting the database if needed..."
docker compose up -d db
for i in $(seq 1 30); do
    if docker compose exec -T db sh -c 'pg_isready -U "$POSTGRES_USER" -d "$POSTGRES_DB"' >/dev/null 2>&1; then break; fi
    sleep 2
done

echo "Migrations that will run:"
docker compose run --rm web python manage.py migrate --plan
echo "Running database migrations..."
docker compose run --rm web python manage.py migrate --noinput

# 4. Switch --------------------------------------------------------------------
echo "Switching to the new code..."
docker compose up -d

echo "Storing numbers for anything the old code changed during the switch..."
docker compose exec -T web python manage.py store_existing_numbers

echo "Collecting static files..."
docker compose exec -T web python manage.py collectstatic --noinput

echo "Seeding roles and fees (existing values are kept)..."
docker compose exec -T web python manage.py seed_roles
docker compose exec -T web python manage.py seed_fees

echo
echo "Deployment completed successfully! The app should now be running on port 80."
echo "Backups: $BACKUP_DIR (db_$STAMP.dump, media_$STAMP.tar.gz)"
echo
echo "Renewal reminders run once a day. If not set up yet, add this line with 'crontab -e':"
echo "  0 7 * * * cd $(pwd) && docker compose exec -T web python manage.py send_renewal_reminders >> $BACKUP_DIR/reminders.log 2>&1"
echo
echo "To roll back the code:    git checkout \$(cat $BACKUP_DIR/commit_$STAMP.txt) && docker compose build web && docker compose up -d"
echo "To restore the database:  docker compose exec -T db sh -c 'pg_restore --clean --if-exists -U \"\$POSTGRES_USER\" -d \"\$POSTGRES_DB\"' < $BACKUP_DIR/db_$STAMP.dump"
