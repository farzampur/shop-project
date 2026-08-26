#!/bin/sh

set -e

echo "Waiting for PostgreSQL..."

until python -c "
import os
import psycopg
conn = psycopg.connect(
    dbname=os.environ['DB_NAME'],
    user=os.environ['DB_USER'],
    password=os.environ['DB_PASSWORD'],
    host=os.environ['DB_HOST'],
    port=os.environ['DB_PORT']
)
conn.close()
" 2>/dev/null
do
    sleep 2
done

echo "PostgreSQL is ready."

echo "Running migrations..."
python manage.py migrate --noinput

echo "Collecting static files..."
python manage.py collectstatic --noinput

echo "Starting Shop..."
exec waitress-serve --listen=0.0.0.0:8000 config.wsgi:application