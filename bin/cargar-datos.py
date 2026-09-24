#!/usr/bin/env python3
"""
Deja en el ambiente los datos compartidos que usan los laboratorios.

    bin/40-cargar-datos-curso.py            # carga lo que falte
    bin/40-cargar-datos-curso.py --listar   # que hay hoy en 'curso'
    bin/40-cargar-datos-curso.py --rehacer  # borra y vuelve a cargar

Las tablas quedan en la database compartida 'curso'. Los alumnos LEEN de ahi y
escriben en su propia database: nadie le pisa el dato a nadie.

QUE CARGA, Y POR QUE ASI

El laboratorio 03 necesita dos lotes de documentos tributarios donde el segundo
traiga reenvios del primero: el mismo folio que llega dos veces. Eso NO se busca
por muestreo al azar, porque entonces el laboratorio dependeria de la suerte y
podria no traer ningun duplicado.

Se construye desde el manifiesto. `datos/manifiesto.json` declara la trampa T-2
con los identificadores EXACTOS de los mil folios duplicados que el generador
sembro. Este script toma los primeros pares completos que encuentra, en orden
determinista, y los reparte:

    curso.recepcion_lote1   la PRIMERA recepcion de cada folio duplicado,
                            mas documentos que no se repiten
    curso.recepcion_lote2   la SEGUNDA recepcion de esos mismos folios
                            —el reenvio—, mas documentos nuevos

Asi el duplicado esta garantizado por construccion, y ademas es el mismo para
todos los alumnos: los folios salen del dataset, no del azar.

Las dos recepciones de un folio difieren en `fecha_recepcion` y en nada mas. Es
lo que dice la trampa: un reenvio del mismo documento, no una correccion.

Para el laboratorio 04 (particionamiento):

    curso.dte_2024          un año de documentos, 12 meses, ESCRITO A PROPOSITO
                            en archivos que mezclan todos los meses
    curso.dte_2025_enero    un mes mas, para cargar despues de cambiar el
                            criterio de particion

Para el laboratorio 05 (evolucion de esquema):

    curso.dte_2026_reciente   documentos del formato NUEVO, con dos columnas
                              que el historico no tiene: canal_emision y
                              codigo_sucursal

Ese cambio de formato no esta inventado para el curso: el generador produce
los dos lotes con esquemas distintos porque es lo que pasa de verdad cuando
una administracion tributaria agrega campos a un documento.

Lo de "mezclan todos los meses" no es un detalle: es la situacion real de una
ingesta que escribe por orden de llegada y no por fecha de emision. Si los
archivos vinieran ordenados por fecha, el motor podria descartarlos por sus
minimos y maximos y la tabla sin particionar no se veria lenta. Escribirlos
mezclados es lo honesto y ademas es lo que pasa en el feed de la DGT.
"""

from __future__ import annotations

import argparse
import collections
import glob
import os
import json
import pathlib
from decimal import Decimal
import subprocess
import sys

RAIZ = pathlib.Path("/opt")   # dentro del contenedor: /opt/datos, /opt/datagen
CONTENEDOR = "iceberg-jupyter"   # contrato publico, ver README.md
DATABASE = "curso"

PARES_DUPLICADOS = 12    # folios que llegaran dos veces
UNICOS_LOTE1 = 18        # documentos del primer lote que no se repiten
UNICOS_LOTE2 = 8         # documentos que solo trae el segundo lote

MES_RECIENTE = "2026-01"     # lote con el esquema nuevo, dos columnas mas
FILAS_MALAS = 20             # documentos descuadrados del lote sospechoso
FILAS_BUENAS_SOSPECHOSO = 480
FILAS_LIMPIAS = 1000
MESES_2024 = [f"2024-{m:02d}" for m in range(1, 13)]
POR_MES = 2500           # documentos que se toman de cada mes
ARCHIVOS_MEZCLADOS = 12  # en cuantos archivos queda dte_2024, todos con todos
                         # los meses adentro

COLUMNAS = ["rut_emisor", "razon_social_emisor", "tipo_dte", "folio",
            "fecha_emision", "fecha_recepcion", "monto_total", "estado_sii"]


def construir_subconjunto():
    """Los dos lotes, derivados del manifiesto. Determinista."""
    import pyarrow as pa
    import pyarrow.parquet as pq

    manifiesto = RAIZ / "datos" / "manifiesto.json"
    if not manifiesto.exists():
        sys.exit(f"falta {manifiesto}. Genera los datos primero:\n"
                 f"  .venv/bin/python -m datagen --escala curso --salida datos/")

    trampa = json.loads(manifiesto.read_text())["trampas"]["T-2"]
    declarados = {(r, int(t), int(f)) for r, t, f in trampa["folios"]}
    print(f"  T-2 «{trampa['nombre']}»: {trampa['conteo']} folios duplicados declarados")

    archivos = sorted(glob.glob(str(RAIZ / "datos/recepcion_diaria/**/*.parquet"),
                                recursive=True))
    if not archivos:
        sys.exit("falta datos/recepcion_diaria/. Genera los datos primero.")

    repetidos = collections.defaultdict(list)
    sueltos = []
    for ruta in archivos:
        tabla = pq.read_table(ruta, columns=COLUMNAS).to_pylist()
        for fila in tabla:
            clave = (fila["rut_emisor"], fila["tipo_dte"], fila["folio"])
            if clave in declarados:
                repetidos[clave].append(fila)
            elif len(sueltos) < (UNICOS_LOTE1 + UNICOS_LOTE2) * 3:
                sueltos.append((clave, fila))
        completos = sum(1 for v in repetidos.values() if len(v) >= 2)
        if completos >= PARES_DUPLICADOS and len(sueltos) >= UNICOS_LOTE1 + UNICOS_LOTE2:
            break

    pares = sorted((k, v) for k, v in repetidos.items() if len(v) >= 2)[:PARES_DUPLICADOS]
    if len(pares) < PARES_DUPLICADOS:
        sys.exit(f"solo encontre {len(pares)} pares completos; esperaba {PARES_DUPLICADOS}")
    sueltos = sorted(sueltos, key=lambda x: x[0])

    lote1, lote2 = [], []
    for _, filas in pares:
        # La primera recepcion va al lote 1; el reenvio, al lote 2.
        primera, segunda = sorted(filas[:2], key=lambda f: f["fecha_recepcion"])
        lote1.append(primera)
        lote2.append(segunda)
    for _, fila in sueltos[:UNICOS_LOTE1]:
        lote1.append(fila)
    for _, fila in sueltos[UNICOS_LOTE1:UNICOS_LOTE1 + UNICOS_LOTE2]:
        lote2.append(fila)

    orden = lambda f: (f["rut_emisor"], f["tipo_dte"], f["folio"])
    lote1.sort(key=orden)
    lote2.sort(key=orden)

    print(f"  lote 1: {len(lote1)} documentos  ({PARES_DUPLICADOS} que se van a repetir "
          f"+ {UNICOS_LOTE1} que no)")
    print(f"  lote 2: {len(lote2)} documentos  ({PARES_DUPLICADOS} reenvios "
          f"+ {UNICOS_LOTE2} nuevos)")

    esquema = pq.read_table(archivos[0], columns=COLUMNAS).schema
    marcado = ([dict(f, lote=1) for f in lote1] + [dict(f, lote=2) for f in lote2])
    esquema = esquema.append(pa.field("lote", pa.int32()))
    return pa.Table.from_pylist(marcado, schema=esquema)


COLUMNAS_DTE = ["rut_emisor", "razon_social_emisor", "tipo_dte", "folio",
                "fecha_emision", "fecha_recepcion", "monto_neto", "monto_iva",
                "monto_total", "estado_sii"]

# El formato nuevo agrega estas dos al final. El orden importa: es el que va a
# tener la tabla del alumno despues del ALTER TABLE ... ADD COLUMNS.
COLUMNAS_NUEVAS = ["canal_emision", "codigo_sucursal"]

# El laboratorio 06 audita montos, asi que necesita monto_exento: el control de
# "el total es la suma" no se puede escribir sin el.
COLUMNAS_MONTOS = ["rut_emisor", "razon_social_emisor", "tipo_dte", "folio",
                   "fecha_emision", "monto_neto", "monto_exento", "monto_iva",
                   "monto_total", "estado_sii"]


def construir_dte(meses, por_mes, lote="lote_historico", columnas=None):
    """Un subconjunto de un lote: los primeros `por_mes` documentos de cada mes."""
    import pyarrow as pa
    import pyarrow.parquet as pq

    filas = []
    for mes in meses:
        rutas = sorted(glob.glob(str(RAIZ / f"datos/dte/{lote}/anio_mes={mes}/*.parquet")))
        if not rutas:
            sys.exit(f"falta datos/dte/{lote}/anio_mes={mes}/")
        # Deterministas: los primeros del archivo, siempre los mismos.
        tabla = pq.read_table(rutas[0], columns=columnas or COLUMNAS_DTE).slice(0, por_mes)
        filas.append(tabla)
    junto = pa.concat_tables(filas)
    print(f"  {len(meses)} meses x {por_mes} documentos = {junto.num_rows} filas")
    return junto


def construir_auditoria():
    """Dos lotes de recepcion: uno limpio y otro con filas descuadradas.

    Las malas salen de la trampa T-5 del manifiesto, que declara cuales son.
    Las buenas se comprueban una por una contra los tres controles, para que el
    lote limpio pase de verdad y no por casualidad.
    """
    import pyarrow as pa
    import pyarrow.parquet as pq

    trampa = json.loads((RAIZ / "datos/manifiesto.json").read_text())["trampas"]["T-5"]
    declaradas = {(r, int(t), int(f)): motivo for r, t, f, motivo in trampa["filas"]}
    print(f"  T-5 «{trampa['nombre']}»: {trampa['conteo']} filas descuadradas declaradas, "
          f"tolerancia {trampa['tolerancia_pesos']} pesos")

    def cuadra(fila):
        neto, exento = fila["monto_neto"], fila["monto_exento"]
        iva, total = fila["monto_iva"], fila["monto_total"]
        iva_ok = abs(iva - round(neto * Decimal("0.19"))) <= 2
        suma_ok = abs(total - (neto + exento + iva)) <= 2
        signo_ok = total >= 0 or fila["tipo_dte"] == 61
        return iva_ok and suma_ok and signo_ok

    malas, buenas = {}, []
    for ruta in sorted(glob.glob(str(RAIZ / "datos/recepcion_diaria/**/*.parquet"),
                                 recursive=True)):
        for fila in pq.read_table(ruta, columns=COLUMNAS_MONTOS).to_pylist():
            clave = (fila["rut_emisor"], fila["tipo_dte"], fila["folio"])
            if clave in declaradas and clave not in malas:
                malas[clave] = fila
            elif clave not in declaradas and cuadra(fila):
                if len(buenas) < FILAS_LIMPIAS + FILAS_BUENAS_SOSPECHOSO:
                    buenas.append((clave, fila))
        if len(malas) >= FILAS_MALAS and len(buenas) >= FILAS_LIMPIAS + FILAS_BUENAS_SOSPECHOSO:
            break

    orden = lambda x: x[0]
    escogidas = [f for _, f in sorted(malas.items())[:FILAS_MALAS]]
    buenas = [f for _, f in sorted(buenas, key=orden)]
    if len(escogidas) < FILAS_MALAS:
        sys.exit(f"solo encontre {len(escogidas)} filas descuadradas de {FILAS_MALAS}")

    limpio = buenas[:FILAS_LIMPIAS]
    sospechoso = escogidas + buenas[FILAS_LIMPIAS:FILAS_LIMPIAS + FILAS_BUENAS_SOSPECHOSO]
    clave = lambda f: (f["rut_emisor"], f["tipo_dte"], f["folio"])
    limpio.sort(key=clave)
    sospechoso.sort(key=clave)

    print(f"  lote limpio:     {len(limpio)} documentos, todos cuadran")
    print(f"  lote sospechoso: {len(sospechoso)} documentos, de los cuales "
          f"{len(escogidas)} NO cuadran")

    esquema = pq.read_table(
        sorted(glob.glob(str(RAIZ / "datos/recepcion_diaria/**/*.parquet"),
                         recursive=True))[0], columns=COLUMNAS_MONTOS).schema
    return (pa.Table.from_pylist(limpio, schema=esquema),
            pa.Table.from_pylist(sospechoso, schema=esquema))


DENTRO = r'''
import os
from pyspark.sql import SparkSession

spark = (SparkSession.builder.appName("cargar-datos-curso")
         .config("spark.ui.showConsoleProgress", "false")
         .enableHiveSupport().getOrCreate())
spark.sparkContext.setLogLevel("ERROR")

DB = os.environ["DB"]
spark.sql(f"CREATE DATABASE IF NOT EXISTS {DB}")
# La base de trabajo del alumno. El ambiente del curso la traia creada; aqui
# no hay quien la cree, asi que se crea al cargar los datos.
spark.sql("CREATE DATABASE IF NOT EXISTS mi_espacio")
print("  creada la base de trabajo mi_espacio")
# file:// explicito: el defaultFS del lab es HDFS, asi que una ruta pelada
# se buscaria alli y no en el disco del contenedor.
marco = spark.read.parquet("file:///tmp/datos-curso/subconjunto.parquet")
marco.createOrReplaceTempView("origen")

for numero in (1, 2):
    tabla = f"{DB}.recepcion_lote{numero}"
    spark.sql(f"DROP TABLE IF EXISTS {tabla}")
    spark.sql(f"""
        CREATE TABLE {tabla} USING iceberg AS
        SELECT rut_emisor, razon_social_emisor, tipo_dte, folio,
               fecha_emision, fecha_recepcion, monto_total, estado_sii
        FROM origen WHERE lote = {numero}
    """)
    n = spark.sql(f"SELECT count(*) c FROM {tabla}").collect()[0]["c"]
    print(f"  cargada {tabla}: {n} documentos")

# --- laboratorio 04 ---------------------------------------------------------
# dte_2024 se escribe MEZCLADO: repartition() reparte las filas por turnos entre
# los archivos, asi que cada archivo termina con documentos de los doce meses.
# Es lo que hace una ingesta que escribe por orden de llegada, y es lo que hace
# que la tabla sin particionar no pueda descartar ningun archivo.
mezclados = int(os.environ["ARCHIVOS_MEZCLADOS"])
anual = spark.read.parquet("file:///tmp/datos-curso/dte_2024.parquet")
anual.repartition(mezclados).createOrReplaceTempView("anual")
spark.sql(f"DROP TABLE IF EXISTS {DB}.dte_2024")
spark.sql(f"CREATE TABLE {DB}.dte_2024 USING iceberg AS SELECT * FROM anual")
n = spark.sql(f"SELECT count(*) c FROM {DB}.dte_2024").collect()[0]["c"]
archivos = spark.sql(f"SELECT count(*) c FROM {DB}.dte_2024.files").collect()[0]["c"]
abarcan = spark.sql(f"""
    SELECT count(*) c FROM {DB}.dte_2024.files
    WHERE readable_metrics.fecha_emision.lower_bound <  DATE '2024-02-01'
      AND readable_metrics.fecha_emision.upper_bound >= DATE '2024-12-01'
""").collect()[0]["c"]
print(f"  cargada {DB}.dte_2024: {n} documentos en {archivos} archivos "
      f"({abarcan} de ellos abarcan casi todo el ano)")

enero = spark.read.parquet("file:///tmp/datos-curso/dte_2025_enero.parquet")
enero.createOrReplaceTempView("enero")
spark.sql(f"DROP TABLE IF EXISTS {DB}.dte_2025_enero")
spark.sql(f"CREATE TABLE {DB}.dte_2025_enero USING iceberg AS SELECT * FROM enero")
n = spark.sql(f"SELECT count(*) c FROM {DB}.dte_2025_enero").collect()[0]["c"]
print(f"  cargada {DB}.dte_2025_enero: {n} documentos")

# --- laboratorio 05 ---------------------------------------------------------
reciente = spark.read.parquet("file:///tmp/datos-curso/dte_2026_reciente.parquet")
reciente.createOrReplaceTempView("reciente")
spark.sql(f"DROP TABLE IF EXISTS {DB}.dte_2026_reciente")
spark.sql(f"CREATE TABLE {DB}.dte_2026_reciente USING iceberg AS SELECT * FROM reciente")
n = spark.sql(f"SELECT count(*) c FROM {DB}.dte_2026_reciente").collect()[0]["c"]
cols = len(spark.table(f"{DB}.dte_2026_reciente").columns)
print(f"  cargada {DB}.dte_2026_reciente: {n} documentos, {cols} columnas "
      f"(el historico tiene {len(os.environ['COLUMNAS_DTE'].split(','))})")

# --- laboratorio 06 ---------------------------------------------------------
for nombre in ("recepcion_limpia", "recepcion_sospechosa"):
    marco = spark.read.parquet(f"file:///tmp/datos-curso/{nombre}.parquet")
    marco.createOrReplaceTempView("aud")
    spark.sql(f"DROP TABLE IF EXISTS {DB}.{nombre}")
    spark.sql(f"CREATE TABLE {DB}.{nombre} USING iceberg AS SELECT * FROM aud")
    n = spark.sql(f"SELECT count(*) c FROM {DB}.{nombre}").collect()[0]["c"]
    malas = spark.sql(f"""
        SELECT count(*) c FROM {DB}.{nombre}
        WHERE abs(monto_iva - round(monto_neto * 0.19)) > 2
           OR abs(monto_total - (monto_neto + monto_exento + monto_iva)) > 2
           OR (monto_total < 0 AND tipo_dte <> 61)
    """).collect()[0]["c"]
    print(f"  cargada {DB}.{nombre}: {n} documentos, {malas} no cuadran")

repetidos = spark.sql(f"""
    SELECT count(*) c FROM (
      SELECT rut_emisor, tipo_dte, folio FROM {DB}.recepcion_lote1
      INTERSECT
      SELECT rut_emisor, tipo_dte, folio FROM {DB}.recepcion_lote2)
""").collect()[0]["c"]
print(f"  folios presentes en LOS DOS lotes: {repetidos}")
if repetidos == 0:
    raise SystemExit("el subconjunto no quedo con duplicados: revisa el manifiesto")
spark.stop()
'''

LISTAR = r'''
import os
from pyspark.sql import SparkSession
spark = (SparkSession.builder.appName("listar-datos-curso")
         .config("spark.ui.showConsoleProgress", "false")
         .enableHiveSupport().getOrCreate())
spark.sparkContext.setLogLevel("ERROR")
DB = os.environ["DB"]
tablas = [f["tableName"] for f in spark.sql(f"SHOW TABLES IN {DB}").collect()]
if not tablas:
    print("  (la database 'curso' esta vacia)")
for t in sorted(tablas):
    n = spark.sql(f"SELECT count(*) c FROM {DB}.{t}").collect()[0]["c"]
    print(f"  {DB}.{t}: {n} filas")
spark.stop()
'''


def en_contenedor(programa: str, entorno: dict) -> int:
    """Ejecuta el programa aqui mismo: este script ya corre donde esta Spark."""
    for clave, valor in entorno.items():
        os.environ[clave] = valor
    try:
        exec(compile(programa, "<carga>", "exec"), {"__name__": "__main__"})
    except SystemExit as salida:
        return int(salida.code or 0)
    except Exception as error:
        print(f"  Error: {error}")
        return 1
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(description="Carga los datos compartidos del curso")
    parser.add_argument("--listar", action="store_true")
    parser.add_argument("--dentro", action="store_true",
                        help="se corre dentro del contenedor (es lo normal)")
    parser.add_argument("--rehacer", action="store_true")
    args = parser.parse_args()

    if args.listar:
        sys.exit(en_contenedor(LISTAR, {"DB": DATABASE}))

    print("construyendo el subconjunto desde el manifiesto")
    tabla = construir_subconjunto()

    print("construyendo el subconjunto anual (laboratorio 04)")
    anual = construir_dte(MESES_2024, POR_MES)
    enero = construir_dte(["2025-01"], POR_MES)

    print("construyendo los lotes de auditoria (laboratorio 06)")
    limpio, sospechoso = construir_auditoria()

    print("construyendo el lote del formato nuevo (laboratorio 05)")
    reciente = construir_dte([MES_RECIENTE], POR_MES, lote="lote_reciente",
                             columnas=COLUMNAS_DTE + COLUMNAS_NUEVAS)
    print(f"  {reciente.num_rows} documentos con {len(reciente.column_names)} columnas "
          f"({', '.join(COLUMNAS_NUEVAS)} son las nuevas)")

    import pyarrow.parquet as pq
    pathlib.Path("/tmp/datos-curso").mkdir(parents=True, exist_ok=True)
    for nombre, contenido in (("subconjunto", tabla), ("dte_2024", anual),
                              ("dte_2025_enero", enero),
                              ("dte_2026_reciente", reciente),
                              ("recepcion_limpia", limpio),
                              ("recepcion_sospechosa", sospechoso)):
        pq.write_table(contenido, f"/tmp/datos-curso/{nombre}.parquet")

    print("cargando en el ambiente")
    codigo = en_contenedor(DENTRO, {"DB": DATABASE,
                                    "ARCHIVOS_MEZCLADOS": str(ARCHIVOS_MEZCLADOS),
                                    "COLUMNAS_DTE": ",".join(COLUMNAS_DTE)})
    if codigo:
        sys.exit(codigo)
    print("\nlisto. Los laboratorios leen de 'curso' y escriben en la database del alumno.")


if __name__ == "__main__":
    main()
