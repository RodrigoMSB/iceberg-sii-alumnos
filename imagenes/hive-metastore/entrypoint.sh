#!/usr/bin/env bash
# Inicializa el esquema del metastore en Postgres (idempotente) y arranca el
# servicio pedido: metastore | hiveserver2.
set -euo pipefail

ROLE="${1:-metastore}"

DB_HOST="${METASTORE_DB_HOST:-postgres}"
DB_PORT="${METASTORE_DB_PORT:-5432}"

echo "==> esperando PostgreSQL en ${DB_HOST}:${DB_PORT}"
for i in $(seq 1 60); do
  if nc -z "${DB_HOST}" "${DB_PORT}" 2>/dev/null; then
    echo "==> PostgreSQL disponible"
    break
  fi
  if [ "$i" -eq 60 ]; then
    echo "ERROR: PostgreSQL no respondio tras 120s" >&2
    exit 1
  fi
  sleep 2
done

echo "==> esperando NameNode en namenode:8020"
for i in $(seq 1 60); do
  if nc -z namenode 8020 2>/dev/null; then
    echo "==> NameNode disponible"
    break
  fi
  if [ "$i" -eq 60 ]; then
    echo "ERROR: NameNode no respondio tras 120s" >&2
    exit 1
  fi
  sleep 2
done

init_schema_if_needed() {
  # schematool -info devuelve != 0 si el esquema no existe todavia.
  if "${HIVE_HOME}/bin/schematool" -dbType postgres -info >/dev/null 2>&1; then
    echo "==> esquema del metastore ya inicializado"
  else
    echo "==> inicializando esquema del metastore (schematool -initSchema)"
    "${HIVE_HOME}/bin/schematool" -dbType postgres -initSchema
  fi
}

# Espera a que HDFS acepte escrituras. En un reinicio con datos, el NameNode
# arranca en safemode (solo lectura) hasta que el DataNode reporta sus bloques;
# escribir antes de eso falla con SafeModeException.
wait_for_safemode_off() {
  echo "==> esperando a que HDFS salga de safemode"
  for _ in $(seq 1 60); do
    if "${HADOOP_HOME}/bin/hdfs" dfsadmin -safemode get 2>/dev/null | grep -q 'Safe mode is OFF'; then
      echo "==> HDFS escribible (safemode OFF)"
      return 0
    fi
    sleep 5
  done
  echo "AVISO: HDFS sigue en safemode tras 300s; se intenta continuar igual" >&2
}

# Crea el directorio del warehouse en HDFS si aun no existe.
prepare_warehouse() {
  local wh="${ICEBERG_WAREHOUSE:-/warehouse/iceberg}"
  wait_for_safemode_off
  echo "==> preparando warehouse HDFS ${wh}"
  "${HADOOP_HOME}/bin/hdfs" dfs -mkdir -p "${wh}" || true
  "${HADOOP_HOME}/bin/hdfs" dfs -chmod -R 777 "${wh}" || true
}

case "${ROLE}" in
  metastore)
    init_schema_if_needed
    prepare_warehouse
    echo "==> arrancando Hive Metastore ${HIVE_VERSION} en :9083"
    exec "${HIVE_HOME}/bin/hive" --service metastore
    ;;
  hiveserver2)
    echo "==> arrancando HiveServer2 ${HIVE_VERSION} en :10000 (plan A)"
    exec "${HIVE_HOME}/bin/hive" --service hiveserver2
    ;;
  *)
    exec "$@"
    ;;
esac
