#!/bin/sh
set -e

echo "Waiting for database..."
until python -c "
import sys
import psycopg2
try:
    psycopg2.connect('${DATABASE_URL}')
except Exception as e:
    sys.exit(1)
" 2>/dev/null; do
  sleep 1
done
echo "Database is ready."

echo "Running migrations..."
alembic upgrade head

echo "Starting server..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000