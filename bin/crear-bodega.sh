#!/usr/bin/env bash
#
# Crea la bodega de diez años que usa el laboratorio 17.
#
#   bin/crear-bodega.sh            crea las dos tablas si faltan
#   bin/crear-bodega.sh --estado   solo mira, no toca nada
#   bin/crear-bodega.sh --rehacer  las bota y las vuelve a crear
#
# DEMORA Y OCUPA. Genera diez millones de documentos de diez años, y eso toma
# entre veinte y cuarenta minutos según tu máquina. Deja cerca de 3 GB de
# archivos intermedios y unos 500 MB en las dos tablas.
#
# Si no piensas hacer el laboratorio 17, no lo corras.
#
# QUE DEJA
#
#   curso.dte_10_anios          diez millones de filas, sin partición
#   curso.dte_10_anios_por_mes  las mismas diez millones, un cajón por mes
#
# Las dos tienen exactamente los mismos documentos y pesan casi lo mismo. La
# única diferencia es cómo están agrupadas las filas adentro, y eso es lo que el
# laboratorio 17 mide con el reloj.

set -euo pipefail
cd "$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

if [ -t 1 ]; then VERDE=$'\033[32m'; ROJO=$'\033[31m'; AMARILLO=$'\033[33m'; NEGRITA=$'\033[1m'; FIN=$'\033[0m'
else VERDE=""; ROJO=""; AMARILLO=""; NEGRITA=""; FIN=""; fi
ok()    { printf '%s  OK  %s %s\n' "${VERDE}" "${FIN}" "$*"; }
aviso() { printf '%s AVISO%s %s\n' "${AMARILLO}" "${FIN}" "$*"; }
paso()  { printf '\n%s==> %s%s\n' "${NEGRITA}" "$*" "${FIN}"; }
morir() { printf '%s FALLA%s %s\n' "${ROJO}" "${FIN}" "$1"; shift; for l in "$@"; do printf '        %s\n' "$l"; done; exit 1; }

docker inspect iceberg-jupyter >/dev/null 2>&1 || morir \
  "el ambiente no esta arriba." "Levantalo con:  bin/ambiente.sh arriba"

ESTADO="no"; REHACER="no"
for a in "$@"; do
  case "$a" in
    --estado)  ESTADO="si" ;;
    --rehacer) REHACER="si" ;;
    *) morir "opcion desconocida: $a" "Uso: $0 [--estado|--rehacer]" ;;
  esac
done

# --- Que hay hoy -----------------------------------------------------------
LEIDO="$(docker exec -i iceberg-jupyter python3 - <<'PY' 2>/dev/null
from pyspark.sql import SparkSession
spark = SparkSession.builder.appName("estado-bodega").enableHiveSupport().getOrCreate()
spark.sparkContext.setLogLevel("ERROR")
for tabla in ("curso.dte_10_anios", "curso.dte_10_anios_por_mes"):
    try:
        filas = spark.sql(f"SELECT count(*) c FROM {tabla}").collect()[0]["c"]
        archivos = spark.sql(f"SELECT count(*) c FROM {tabla}.files").collect()[0]["c"]
        print(f"RESULTADO {tabla} {filas} {archivos}")
    except Exception:
        print(f"RESULTADO {tabla} 0 0")
PY
)"
echo "${LEIDO}" | { grep '^RESULTADO' || true; } | while read -r _ tabla filas archivos; do
  if [ "${filas}" = "0" ]; then aviso "${tabla}: no existe"
  else ok "${tabla}: ${filas} filas en ${archivos} archivos"; fi
done
COMPLETAS="si"
while read -r _ _ filas _; do
  [ "${filas}" = "10000000" ] || COMPLETAS="no"
done <<< "$(echo "${LEIDO}" | { grep '^RESULTADO' || true; })"

if [ "${ESTADO}" = "si" ]; then
  [ "${COMPLETAS}" = "si" ] && ok "las dos tablas estan completas." || aviso "falta crearlas."
  exit 0
fi
if [ "${COMPLETAS}" = "si" ] && [ "${REHACER}" = "no" ]; then
  ok "las dos tablas ya estan con sus diez millones. No hay nada que hacer."
  exit 0
fi

# --- 1. Generar los diez años ----------------------------------------------
if [ "${REHACER}" = "si" ] || ! docker exec iceberg-jupyter test -f /opt/datos-bodega/bodega.json 2>/dev/null; then
  paso "generando diez millones de documentos. Demora entre veinte y cuarenta minutos."
  echo "    Va imprimiendo su avance; puedes dejarlo corriendo y volver."
  docker exec -w /opt iceberg-jupyter env PYTHONPATH=/opt/datagen \
    python3 -m datagen --bodega --salida /opt/datos-bodega/
  ok "datos de la bodega generados"
else
  ok "los datos de la bodega ya estaban generados"
fi

# --- 2. Crear las dos tablas -----------------------------------------------
paso "creando las dos tablas. Son diez millones de filas, dos veces."
docker exec -i iceberg-jupyter python3 - <<'PY'
import time
from pyspark.sql import SparkSession

COLUMNAS = ["rut_emisor", "razon_social_emisor", "tipo_dte", "folio", "fecha_emision",
            "fecha_recepcion", "monto_neto", "monto_iva", "monto_total", "estado_sii"]
ARCHIVOS = 120

spark = (SparkSession.builder.appName("crear-bodega")
         .enableHiveSupport().getOrCreate())
spark.sparkContext.setLogLevel("ERROR")

crudo = spark.read.parquet("file:///opt/datos-bodega/dte/bodega")
origen = crudo.select(*COLUMNAS)

# La tabla sin particion va MEZCLADA a proposito: repartition reparte por
# turnos, asi que cada archivo termina con filas de los diez anios y ningun
# rotulo permite descartarlo. Es lo que hace que el laboratorio muestre algo.
origen.repartition(ARCHIVOS).createOrReplaceTempView("mezclado")
spark.sql("DROP TABLE IF EXISTS curso.dte_10_anios")
t = time.monotonic()
spark.sql("CREATE TABLE curso.dte_10_anios USING iceberg AS SELECT * FROM mezclado")
print(f"  curso.dte_10_anios creada en {time.monotonic() - t:.0f} s")

origen.createOrReplaceTempView("ordenado")
columnas_sql = ",\n  ".join(f"{c} {t2}" for c, t2 in origen.dtypes)
spark.sql("DROP TABLE IF EXISTS curso.dte_10_anios_por_mes")
spark.sql(f"""
    CREATE TABLE curso.dte_10_anios_por_mes (
      {columnas_sql}
    ) USING iceberg
    PARTITIONED BY (months(fecha_emision))
    TBLPROPERTIES ('write.distribution-mode' = 'hash')
""")
t = time.monotonic()
spark.sql("INSERT INTO curso.dte_10_anios_por_mes SELECT * FROM ordenado")
print(f"  curso.dte_10_anios_por_mes creada en {time.monotonic() - t:.0f} s")

for tabla in ("curso.dte_10_anios", "curso.dte_10_anios_por_mes"):
    f = spark.sql(f"""
        SELECT count(*) AS archivos, sum(record_count) AS filas,
               sum(file_size_in_bytes) AS bytes
        FROM {tabla}.files
    """).collect()[0]
    suma = spark.sql(f"SELECT sum(monto_total) AS s FROM {tabla}").collect()[0]["s"]
    print(f"  {tabla}: {f['filas']} filas, {f['archivos']} archivos, "
          f"{f['bytes']} bytes, suma {suma}")
PY

ok "bodega lista. Ahora puedes hacer el laboratorio 17."
echo "    Para el paso 4 hace falta ademas:  bin/reponer-fragmentada.sh"
