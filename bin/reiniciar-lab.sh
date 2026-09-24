#!/usr/bin/env bash
#
# Deja un laboratorio como recien empezado, para poder repetirlo.
#
#   bin/reiniciar-lab.sh 03     borra las tablas que crea el laboratorio 03
#   bin/reiniciar-lab.sh todos  borra todas las tablas de mi_espacio
#
# Solo toca TU base de trabajo, mi_espacio. La base 'curso', que es de solo
# lectura para los laboratorios, no se toca nunca: si la borraras habria que
# volver a cargarla con bin/cargar-datos.sh.
#
# Casi todos los laboratorios empiezan con un DROP TABLE IF EXISTS, asi que se
# pueden repetir sin reiniciar nada. Esto es para cuando quieres partir limpio,
# o para el 10 y el 16, que necesitan ademas otra cosa:
#
#   laboratorio 10  la tabla compartida se repone sola aqui
#   laboratorio 16  el origen se repone con bin/origen-lab16.sh --reset
#   laboratorio 17  la tabla fragmentada se repone con bin/reponer-fragmentada.sh

set -euo pipefail
cd "$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

[ $# -ge 1 ] || { echo "uso: $0 <numero de laboratorio|todos>"; exit 2; }
docker inspect iceberg-jupyter >/dev/null 2>&1 || {
  echo "el ambiente no esta arriba. Levantalo con: bin/ambiente.sh arriba"; exit 1; }

LAB="$1"

docker exec -i -e LAB="${LAB}" iceberg-jupyter python3 - <<'PY'
import os
from pyspark.sql import SparkSession

LAB = os.environ["LAB"]
DB = "mi_espacio"

spark = SparkSession.builder.appName("reiniciar-lab").enableHiveSupport().getOrCreate()
spark.sparkContext.setLogLevel("ERROR")

existentes = [f["tableName"] for f in spark.sql(f"SHOW TABLES IN {DB}").collect()]
if LAB == "todos":
    objetivo = existentes
else:
    n = LAB.zfill(2)
    objetivo = [t for t in existentes if t.endswith(f"lab{n}") or f"lab{n}_" in t
                or (n == "17" and t == "dte_un_anio_fragmentado")
                or (n == "04" and t in ("documentos_sin_particion", "documentos_por_mes"))
                or (n == "07" and t.startswith("documentos_hive"))
                or (n == "13" and t == "documentos_lab13")]

if not objetivo:
    print(f"  no hay tablas que borrar para '{LAB}'")
else:
    for tabla in objetivo:
        spark.sql(f"DROP TABLE IF EXISTS {DB}.{tabla}")
        print(f"  borrada {DB}.{tabla}")
    print(f"  {len(objetivo)} tabla(s) borradas de {DB}")
PY

if [ "${LAB}" = "10" ] || [ "${LAB}" = "todos" ]; then
  echo "  reponiendo la tabla compartida del laboratorio 10"
  docker exec -i iceberg-jupyter python3 - <<'PY'
from pyspark.sql import SparkSession
spark = SparkSession.builder.appName("reponer-lab10").enableHiveSupport().getOrCreate()
spark.sparkContext.setLogLevel("ERROR")
spark.sql("DROP TABLE IF EXISTS curso.escritores_lab10")
spark.sql("""
    CREATE TABLE curso.escritores_lab10 (
        rut STRING, razon_social STRING, segmento STRING
    ) USING iceberg
""")
spark.sql("""
    INSERT INTO curso.escritores_lab10 VALUES
        ('77746521-K', 'Pehuen Logistica EIRL',    'MICRO'),
        ('77884562-8', 'Araucaria Ferreteria SpA', 'PEQUENA'),
        ('78800840-6', 'Copihue Maquinarias EIRL', 'MEDIANA'),
        ('76171162-8', 'Huemul Alimentos EIRL',    'GRANDE')
""")
print("  curso.escritores_lab10 repuesta con sus cuatro contribuyentes")
PY
fi

echo "  listo: el laboratorio ${LAB} se puede repetir desde el principio"
