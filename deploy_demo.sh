#!/bin/bash

# Ensure script stops on error
set -e

echo "Starting Deployment for TAMRIS DEMO on Hostinger..."

# Build and start the containers in detached mode using the demo config
echo "Bringing up Docker containers for DEMO..."
docker compose -f docker-compose.demo.yml up --build -d

# Wait a few seconds for DB to be ready
echo "Waiting for PostgreSQL database to initialize..."
sleep 5

# Run migrations
echo "Running database migrations..."
docker compose -f docker-compose.demo.yml exec web-demo python manage.py migrate --noinput

# Collect static files
echo "Collecting static files..."
docker compose -f docker-compose.demo.yml exec web-demo python manage.py collectstatic --noinput

# Seed Roles and Fees
echo "Seeding initial roles and fees..."
docker compose -f docker-compose.demo.yml exec web-demo python manage.py seed_roles
docker compose -f docker-compose.demo.yml exec web-demo python manage.py seed_fees

echo "DEMO Deployment completed successfully! The app should now be running on port 8080."
