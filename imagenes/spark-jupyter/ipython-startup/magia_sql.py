"""
Magia %%sql del laboratorio: SQL puro en una celda, sin envolver en Python.

El publico del curso son operadores, administradores y analistas. Escriben SQL,
no Python alrededor de SQL. Una celda se ve asi y funciona tal cual:

    %%sql
    SELECT rut, razon_social FROM contribuyentes

Este modulo se instala en /opt/lab/python/ dentro de la imagen y lo importa
el archivo de arranque de IPython (00-magia-sql.py), que se copia a
/root/.ipython/profile_default/startup/. IPython lo ejecuta al arrancar CADA
kernel, asi que el alumno nunca escribe %load_ext.

Va en la imagen y no en /home/<alumno>, que es un volumen: por eso sobrevive a
que se reinicie el volumen de trabajo de un alumno. Y va en un modulo aparte,
no dentro del propio archivo de arranque, para no dejar sus nombres internos
sueltos en el espacio de variables del alumno.

Contrato (SPEC-005 §3):

  %%sql                       una sentencia por celda, limite 50 filas
  %%sql --limit 200           cambia el limite de filas mostradas
  %%sql df <<                 ademas deja el resultado en la variable 'df'

No agrega ninguna dependencia: usa la sesion de Spark que ya tiene el notebook
y pandas, que ya estaba en la imagen.
"""

from __future__ import annotations

import os
import re

from IPython.core.magic import register_cell_magic
from IPython.display import HTML, display

# Filas que se muestran cuando la celda no pide otra cosa. El contenedor del
# alumno tiene 3 GB: un SELECT * sin limite sobre los 2 millones de DTEs se
# lleva por delante el kernel.
LIMITE_POR_DEFECTO = 50

# Tope de guarda para --limit. Muy por encima de cualquier uso didactico, pero
# impide que un dedo pesado escriba --limit 5000000.
LIMITE_MAXIMO = 10_000


# --------------------------------------------------------------------------
# Sesion de Spark
# --------------------------------------------------------------------------

def _sesion_spark(shell):
    """La sesion que ya tiene el notebook. Nunca abre una segunda."""
    from pyspark.sql import SparkSession

    activa = SparkSession.getActiveSession()
    if activa is not None:
        return activa

    # Si el alumno ya ejecuto la celda que crea 'spark', esa es la buena.
    del_usuario = shell.user_ns.get("spark") if shell is not None else None
    if del_usuario is not None and isinstance(del_usuario, SparkSession):
        return del_usuario

    # Nadie creo sesion todavia: la celda %%sql es la primera del notebook.
    # getOrCreate() con appName solo nombra la sesion si efectivamente la crea;
    # si ya existiera una, Spark devuelve esa e ignora el appName.
    espacio = os.environ.get("LAB_USER", "mi_espacio")
    sesion = (
        SparkSession.builder
        .appName(f"lab-{espacio}")
        .enableHiveSupport()
        .getOrCreate()
    )
    sesion.sparkContext.setLogLevel("ERROR")
    if shell is not None:
        # Se publica como 'spark' para que las celdas de Python posteriores la
        # encuentren con el mismo nombre que usan las guias.
        shell.user_ns.setdefault("spark", sesion)
    return sesion


# --------------------------------------------------------------------------
# Analisis de la celda
# --------------------------------------------------------------------------

def _posiciones_de_punto_y_coma(sql: str) -> list[int]:
    """
    Indices de los ';' que separan sentencias de verdad.

    Recorre el texto ignorando los ';' que estan dentro de literales entre
    comillas simples, de identificadores entre comillas dobles o acentos
    graves, de comentarios de linea (--) y de comentarios de bloque. Un split
    ingenuo por ';' marcaria como dos sentencias algo tan corriente como
        SELECT * FROM dte WHERE glosa = 'pago; parcial'
    """
    posiciones: list[int] = []
    i = 0
    n = len(sql)
    while i < n:
        c = sql[i]

        if c == "-" and sql.startswith("--", i):
            salto = sql.find("\n", i)
            i = n if salto == -1 else salto + 1
            continue

        if c == "/" and sql.startswith("/*", i):
            cierre = sql.find("*/", i + 2)
            i = n if cierre == -1 else cierre + 2
            continue

        if c in ("'", '"', "`"):
            comilla = c
            i += 1
            while i < n:
                if sql[i] == comilla:
                    # '' dentro de un literal es una comilla escapada.
                    if i + 1 < n and sql[i + 1] == comilla:
                        i += 2
                        continue
                    i += 1
                    break
                if sql[i] == "\\" and comilla == "'":
                    i += 2
                    continue
                i += 1
            continue

        if c == ";":
            posiciones.append(i)

        i += 1

    return posiciones


def _miles(numero: int) -> str:
    """12345 -> '12.345'. Separador de miles como se escribe en Chile."""
    return f"{numero:,}".replace(",", ".")


def _mensaje_de_spark(error: Exception) -> str:
    """
    El mensaje de Spark sin el volcado del plan logico.

    AnalysisException adjunta el arbol del plan ("'Project [*]", "+- ...").
    Para quien esta aprendiendo SQL eso es ruido: la linea util es la primera.
    Si el recorte dejara el mensaje vacio, se devuelve entero.
    """
    completo = str(error).strip()
    utiles = []
    for linea in completo.splitlines():
        if linea[:1] in ("'", "+") or linea.startswith(":-") or linea.startswith(":+"):
            break
        utiles.append(linea)
    recortado = "\n".join(utiles).strip()
    return recortado or completo


class ErrorDeCelda(Exception):
    """Problema de la celda misma, no de Spark. Se muestra sin traza."""


def _sentencia_unica(sql: str) -> str:
    """
    Devuelve la sentencia lista para ejecutar, o explica por que no se puede.

    Regla del curso: una sentencia por celda. Un ';' final suelto se tolera.
    """
    cuerpo = sql.strip()
    if not cuerpo:
        raise ErrorDeCelda(
            "La celda está vacía: escribe una sentencia SQL debajo de %%sql."
        )

    posiciones = _posiciones_de_punto_y_coma(cuerpo)

    # Un ';' final, con espacios o comentarios detras, no separa nada.
    if posiciones and not cuerpo[posiciones[-1] + 1:].strip():
        posiciones = posiciones[:-1]
        cuerpo = cuerpo[: cuerpo.rfind(";")].rstrip()

    if posiciones:
        primera = cuerpo[: posiciones[0]].strip()
        resto = cuerpo[posiciones[0] + 1:].strip()
        raise ErrorDeCelda(
            "Esta celda tiene más de una sentencia SQL, y en este curso va "
            "una sentencia por celda.\n\n"
            "Por qué: se ejecuta una idea, se mira el resultado, y recién "
            "entonces sigue la siguiente.\n\n"
            "Separa la celda en dos. En esta deja:\n"
            f"    {primera}\n"
            "y en una celda nueva, con su propio %%sql:\n"
            f"    {resto.splitlines()[0] if resto else ''}"
        )

    return cuerpo


_LINEA = re.compile(
    r"""^\s*
        (?:(?P<variable>[A-Za-z_]\w*)\s*<<)?      # 'df <<'
        \s*
        (?P<opciones>.*)$
    """,
    re.VERBOSE,
)


def _leer_linea(linea: str) -> tuple[str | None, int]:
    """Interpreta la linea del %%sql: variable de captura y --limit."""
    coincidencia = _LINEA.match(linea or "")
    variable = coincidencia.group("variable")
    opciones = (coincidencia.group("opciones") or "").split()

    limite = LIMITE_POR_DEFECTO
    i = 0
    while i < len(opciones):
        opcion = opciones[i]
        if opcion in ("--limit", "-n"):
            if i + 1 >= len(opciones):
                raise ErrorDeCelda("A --limit le falta el número: %%sql --limit 200")
            crudo = opciones[i + 1]
            i += 2
        elif opcion.startswith("--limit="):
            crudo = opcion.split("=", 1)[1]
            i += 1
        else:
            raise ErrorDeCelda(
                f"No entiendo la opción '{opcion}'.\n\n"
                "Las formas válidas son:\n"
                "    %%sql\n"
                "    %%sql --limit 200\n"
                "    %%sql df <<\n"
                "    %%sql df << --limit 200"
            )
        if not crudo.lstrip("+").isdigit() or int(crudo) <= 0:
            raise ErrorDeCelda(f"--limit tiene que ser un entero positivo, no '{crudo}'.")
        limite = int(crudo)
        if limite > LIMITE_MAXIMO:
            raise ErrorDeCelda(
                f"--limit {_miles(limite)} es demasiado para la memoria del "
                f"contenedor (el tope es {_miles(LIMITE_MAXIMO)}). "
                "Filtra la consulta con WHERE."
            )

    return variable, limite


# --------------------------------------------------------------------------
# Presentacion
# --------------------------------------------------------------------------

def _mostrar_aviso(texto: str, color: str) -> None:
    display(HTML(
        f'<div style="margin:.35em 0;padding:.5em .7em;border-left:4px solid {color};'
        f'background:rgba(127,127,127,.08);font-family:sans-serif;font-size:.9em;'
        f'white-space:pre-wrap">{_escapar(texto)}</div>'
    ))


def _escapar(texto: str) -> str:
    return (
        str(texto)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def _tabla_html(filas, columnas) -> bool:
    """Dibuja las filas como tabla HTML. False si pandas no esta disponible."""
    try:
        import pandas
    except Exception:
        return False

    try:
        marco = pandas.DataFrame(
            [list(fila) for fila in filas], columns=list(columnas)
        )
        display(HTML(marco.to_html(index=False, escape=True, na_rep="NULL")))
        return True
    except Exception:
        return False


def _texto_plano(filas, columnas) -> None:
    """Respaldo cuando pandas no esta: la tabla monoespaciada de Spark."""
    anchos = [len(str(c)) for c in columnas]
    filas_texto = [["NULL" if v is None else str(v) for v in fila] for fila in filas]
    for fila in filas_texto:
        anchos = [max(a, len(v)) for a, v in zip(anchos, fila)]

    def linea(valores):
        return "| " + " | ".join(v.ljust(a) for v, a in zip(valores, anchos)) + " |"

    borde = "+" + "+".join("-" * (a + 2) for a in anchos) + "+"
    print(borde)
    print(linea([str(c) for c in columnas]))
    print(borde)
    for fila in filas_texto:
        print(linea(fila))
    print(borde)


# --------------------------------------------------------------------------
# La magia
# --------------------------------------------------------------------------

@register_cell_magic
def sql(linea, celda):
    """Ejecuta una sentencia SQL contra la sesion de Spark del notebook."""
    from IPython import get_ipython

    shell = get_ipython()

    try:
        variable, limite = _leer_linea(linea)
        sentencia = _sentencia_unica(celda)
    except ErrorDeCelda as error:
        _mostrar_aviso(str(error), "#c0392b")
        return

    spark = _sesion_spark(shell)

    try:
        df = spark.sql(sentencia)
    except Exception as error:
        # El mensaje de Spark es lo util; la traza de Python no aporta nada a
        # quien esta aprendiendo SQL. Se muestra completo el mensaje, sin traza.
        _mostrar_aviso(
            "Spark rechazó la sentencia:\n\n" + _mensaje_de_spark(error), "#c0392b"
        )
        return

    # DDL y DML (CREATE, INSERT, MERGE, UPDATE, DELETE, USE...) no devuelven
    # columnas. Mostrar una tabla vacia confundiria: se confirma y se sale.
    if not df.columns:
        _mostrar_aviso("Listo. La sentencia se ejecutó.", "#27ae60")
        if variable and shell is not None:
            shell.user_ns[variable] = df
        return

    # take(limite + 1) trae una fila de mas: con eso se sabe si hubo corte sin
    # traer todo el resultado a memoria.
    muestra = df.take(limite + 1)
    truncado = len(muestra) > limite
    visibles = muestra[:limite]

    if not _tabla_html(visibles, df.columns):
        _texto_plano(visibles, df.columns)

    if truncado:
        # Solo cuando hubo corte se paga el count(): sobre una tabla Iceberg
        # sin filtros lo responde la metadata, sin leer los Parquet.
        try:
            total = _miles(df.count())
        except Exception:
            total = "muchas"
        _mostrar_aviso(
            f"Mostrando {limite} de {total} filas. "
            f"Para ver más: %%sql --limit {limite * 4}",
            "#e67e22",
        )
    else:
        n = len(visibles)
        _mostrar_aviso(f"{n} fila{'' if n == 1 else 's'}.", "#7f8c8d")

    if variable and shell is not None:
        shell.user_ns[variable] = df
        try:
            # Ademas queda como vista temporal, para que la siguiente celda
            # %%sql pueda consultarla sin salir de SQL.
            df.createOrReplaceTempView(variable)
            extra = f" y como vista SQL: SELECT * FROM {variable}"
        except Exception:
            extra = ""
        _mostrar_aviso(
            f"Guardado en la variable '{variable}' (DataFrame de Spark, "
            f"resultado completo, no solo las filas de arriba){extra}.",
            "#2980b9",
        )

