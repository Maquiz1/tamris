#!/bin/bash

# Ensure script stops on error
set -e

echo "Starting Deployment for TAMRIS on Hostinger..."

# Build and start the containers in detached mode
echo "Bringing up Docker containers..."
docker compose up --build -d

# Wait a few seconds for DB to be ready
echo "Waiting for PostgreSQL database to initialize..."
sleep 5

# Run migrations
echo "Running database migrations..."
docker compose exec web python manage.py migrate --noinput

# Collect static files
echo "Collecting static files..."
docker compose exec web python manage.py collectstatic --noinput

# Seed Roles and Fees
echo "Seeding initial roles and fees..."
docker compose exec web python manage.py seed_roles
docker compose exec web python manage.py seed_fees

echo "Deployment completed successfully! The app should now be running on port 80."
