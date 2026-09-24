#!/usr/bin/env bash
#
# Repone la tabla fragmentada que el mi_espacio proyecta en el paso 4 del
# laboratorio 17.
#
#   bin/43-reponer-fragmentada-lab17.sh           # la deja recien creada
#   bin/43-reponer-fragmentada-lab17.sh --estado  # solo mira, no toca nada
#
# ANTES DE CADA DICTADO DEL LABORATORIO 17, igual que 96-reiniciar-lab10.sh y
# 97-cambiar-origen-lab16.sh --reset antes de los suyos.
#
# QUE DEJA
#
#   mi_espacio.dte_un_anio_fragmentado   un millon de documentos de 2024, cargados
#                                     en una escritura por dia
#
# Son 365 commits, uno por dia, como los hace una ingesta diaria de verdad: cada
# dia llega su lote y se anota una pagina nueva en la libreta. El resultado son
# cientos de papelitos chicos, que es justo lo que el paso 4 compacta con
# rewrite_data_files para mostrar la diferencia.
#
# POR QUE SE REPONE CADA VEZ
#
# El paso 4 COMPACTA la tabla. Despues de un dictado queda con sus archivos ya
# juntos, y el siguiente mi_espacio proyectaria una compactacion que no tiene nada
# que compactar. Este script la devuelve a su estado fragmentado.
#
# SOLO TOCA EL ESPACIO 'mi_espacio'
#
# Ninguna otra database. Los alumnos no escriben en esta tabla: en su cuaderno
# el paso 4 va como texto con la salida esperada, sin celdas ejecutables, y es
# el mi_espacio quien lo proyecta.

source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/_comun.sh"

CONTENEDOR="iceberg-jupyter"   # contrato publico, ver README.md
DATABASE="mi_espacio"
TABLA="dte_un_anio_fragmentado"
ORIGEN="curso.dte_10_anios"
ANIO=2024
ESCRITURAS_MINIMAS=300

ESTADO="no"
for argumento in "$@"; do
  case "${argumento}" in
    --estado) ESTADO="si" ;;
    *)        morir "opcion desconocida: ${argumento}" "Uso: $0 [--estado]" ;;
  esac
done

exigir_docker
contenedor_vivo "${CONTENEDOR}" || morir \
  "el contenedor ${CONTENEDOR} no esta corriendo." \
  "cd bin/ambiente.sh arriba"

titulo "Tabla fragmentada del laboratorio 17"

if [ "${ESTADO}" = "si" ]; then
  docker exec -i -e DB="${DATABASE}" -e TABLA="${TABLA}" "${CONTENEDOR}" python3 - <<'PY'
import os
from pyspark.sql import SparkSession
spark = SparkSession.builder.appName("estado-fragmentada").enableHiveSupport().getOrCreate()
spark.sparkContext.setLogLevel("ERROR")
tabla = f"{os.environ['DB']}.{os.environ['TABLA']}"
try:
    filas = spark.sql(f"SELECT count(*) c FROM {tabla}").collect()[0]["c"]
    archivos = spark.sql(f"SELECT count(*) c FROM {tabla}.files").collect()[0]["c"]
    paginas = spark.sql(f"SELECT count(*) c FROM {tabla}.snapshots").collect()[0]["c"]
    print(f"  {tabla}: {filas} filas, {archivos} archivos, {paginas} paginas")
    print("  fragmentada" if archivos >= 300 else "  YA COMPACTADA: hay que reponerla")
except Exception:
    print(f"  {tabla}: no existe")
PY
  exit 0
fi

info "reponiendo ${DATABASE}.${TABLA} desde ${ORIGEN}, una escritura por dia"
INICIO=$(date +%s)
docker exec -i \
  -e DB="${DATABASE}" -e TABLA="${TABLA}" -e ORIGEN="${ORIGEN}" -e ANIO="${ANIO}" \
  "${CONTENEDOR}" python3 - <<'PY'
import os, time
from pyspark.sql import SparkSession

DB = os.environ["DB"]
TABLA = os.environ["TABLA"]
ORIGEN = os.environ["ORIGEN"]
ANIO = int(os.environ["ANIO"])
destino = f"{DB}.{TABLA}"

spark = (SparkSession.builder.appName("reponer-fragmentada-lab17")
         .enableHiveSupport().getOrCreate())
spark.sparkContext.setLogLevel("ERROR")

try:
    spark.sql(f"SELECT 1 FROM {ORIGEN} LIMIT 1").collect()
except Exception:
    raise SystemExit(
        f"no existe {ORIGEN}. Corre antes bin/42-crear-bodega-10-anios.sh"
    )

spark.sql(f"CREATE DATABASE IF NOT EXISTS {DB}")
spark.sql(f"DROP TABLE IF EXISTS {destino}")

columnas = spark.table(ORIGEN).dtypes
columnas_sql = ",\n  ".join(f"{c} {t}" for c, t in columnas)
spark.sql(f"CREATE TABLE {destino} (\n  {columnas_sql}\n) USING iceberg")

# Un dia, una escritura. Se materializa el anio una sola vez y se recorre por
# dia: leer la tabla de origen 365 veces seria 365 escaneos de diez millones.
anio = spark.sql(f"""
    SELECT * FROM {ORIGEN}
    WHERE fecha_emision >= DATE '{ANIO}-01-01'
      AND fecha_emision <= DATE '{ANIO}-12-31'
""")
anio.createOrReplaceTempView("anio")
spark.catalog.cacheTable("anio")
total = spark.sql("SELECT count(*) c FROM anio").collect()[0]["c"]
print(f"  {total} documentos de {ANIO} para repartir en dias")

dias = [f["fecha_emision"] for f in spark.sql(
    "SELECT DISTINCT fecha_emision FROM anio ORDER BY fecha_emision").collect()]
print(f"  {len(dias)} dias distintos")

inicio = time.monotonic()
for numero, dia in enumerate(dias, start=1):
    spark.sql(f"""
        INSERT INTO {destino}
        SELECT * FROM anio WHERE fecha_emision = DATE '{dia}'
    """)
    if numero % 50 == 0 or numero == len(dias):
        print(f"  {numero} de {len(dias)} dias escritos")
demoro = time.monotonic() - inicio

filas = spark.sql(f"SELECT count(*) c FROM {destino}").collect()[0]["c"]
fila = spark.sql(f"""
    SELECT count(*) AS archivos, sum(file_size_in_bytes) AS bytes
    FROM {destino}.files
""").collect()[0]
paginas = spark.sql(f"SELECT count(*) c FROM {destino}.snapshots").collect()[0]["c"]
print(f"  {destino}: {filas} filas, {fila['archivos']} archivos, "
      f"{fila['bytes']} bytes, {paginas} paginas, en {demoro:.1f} s")
PY
CODIGO=$?
FIN=$(date +%s)

[ "${CODIGO}" = "0" ] || morir "la reposicion fallo con codigo ${CODIGO}."
ok "repuesta en $((FIN - INICIO)) s. El paso 4 del laboratorio 17 ya tiene que compactar."
