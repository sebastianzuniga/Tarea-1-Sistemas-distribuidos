#!/bin/sh

until redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" ping; do
  >&2 echo "Redis no está disponible - esperando..."
  sleep 2
done

>&2 echo "Redis está listo - iniciando aplicación..."
exec "$@"