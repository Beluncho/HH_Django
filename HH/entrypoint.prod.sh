#!/bin/sh
set -e

if [ "$DATABASE" = "postgres" ]; then
    echo "Waiting for PostgreSQL at ${POSTGRES_HOST}:${POSTGRES_PORT}..."
    until nc -z "$POSTGRES_HOST" "$POSTGRES_PORT"; do
        sleep 0.2
    done
    echo "PostgreSQL is available."
fi

python manage.py migrate --noinput
python manage.py collectstatic --noinput

exec "$@"
