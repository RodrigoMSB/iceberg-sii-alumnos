#!/usr/bin/env sh
#
# Crea, si no existen, la base y el rol que Hue usa para su estado interno.
#
# Lo ejecuta el servicio 'hue-init' del compose antes de que Hue arranque, con
# la imagen de postgres (que ya trae psql). Es IDEMPOTENTE: en un ambiente ya
# creado no hace nada, y si la clave del .env cambio, la sincroniza.
#
# Hace falta porque la imagen de postgres solo corre sus scripts de
# /docker-entrypoint-initdb.d la PRIMERA vez que inicializa el volumen, y
# POSTGRES_DB solo crea una base. Sin esto, un ambiente nuevo levanta Hue
# contra una base que no existe y el contenedor queda reintentando.
set -eu

HOST="${HUE_DB_HOST:-postgres}"
ADMIN_USER="${POSTGRES_ADMIN_USER:-hive}"
NOMBRE="${HUE_DB_NAME:-hue}"
USUARIO="${HUE_DB_USER:-hue_app}"
: "${HUE_DB_PASSWORD:?falta HUE_DB_PASSWORD}"
: "${PGPASSWORD:?falta PGPASSWORD (clave del usuario administrador)}"

psql_admin() { psql -h "${HOST}" -U "${ADMIN_USER}" -d postgres -v ON_ERROR_STOP=1 "$@"; }

# El rol. Si ya esta, se le sincroniza la clave con la del .env: asi cambiarla
# en un solo sitio basta y no queda un Hue que no puede autenticarse.
if [ "$(psql_admin -tAc "select 1 from pg_roles where rolname = '${USUARIO}'")" = "1" ]; then
  psql_admin -c "ALTER ROLE \"${USUARIO}\" WITH LOGIN PASSWORD '${HUE_DB_PASSWORD}'" >/dev/null
  echo "rol ${USUARIO}: ya existia, clave sincronizada con el .env"
else
  psql_admin -c "CREATE ROLE \"${USUARIO}\" WITH LOGIN PASSWORD '${HUE_DB_PASSWORD}'" >/dev/null
  echo "rol ${USUARIO}: creado"
fi

# La base. Propia de Hue: el Hive Metastore vive en 'metastore' con otro rol y
# no se comparte nada entre las dos.
if [ "$(psql_admin -tAc "select 1 from pg_database where datname = '${NOMBRE}'")" = "1" ]; then
  echo "base ${NOMBRE}: ya existia"
else
  psql_admin -c "CREATE DATABASE \"${NOMBRE}\" WITH OWNER \"${USUARIO}\" ENCODING 'UTF8'" >/dev/null
  echo "base ${NOMBRE}: creada"
fi

echo "base interna de Hue lista en ${HOST}/${NOMBRE}"
