"""
CA-5: cada trampa existe, es medible y coincide con el manifiesto.

Una trampa que el test no sabe encontrar es folclore: la guia afirmaria un
problema que nadie puede verificar. Por eso cada test aqui localiza la anomalia
en los datos reales, no se conforma con leer el conteo del manifiesto.
"""

from __future__ import annotations

from collections import Counter
from decimal import Decimal

import pyarrow.dataset as ds
import pytest

from datagen.trampas import COLUMNAS_V2, TOLERANCIA_REDONDEO

TASA = Decimal("0.19")
# En escala dev el umbral de archivos chicos baja; en curso el objetivo es 500.
MINIMO_ARCHIVOS_DEV = 50


def _tabla(datos, ruta, columnas=None):
    return ds.dataset(datos / ruta, format="parquet").to_table(columns=columnas)


# --- T-1 ---------------------------------------------------------------------
def test_t1_existen_dtes_tardios(datos, manifiesto):
    """Recepcion hasta 45 dias despues de la emision."""
    tardios = 0
    maximo = 0
    for ruta in ("dte/lote_historico", "dte/lote_reciente", "recepcion_diaria"):
        tabla = _tabla(datos, ruta, ["fecha_emision", "fecha_recepcion"])
        for emision, recepcion in zip(
            tabla.column("fecha_emision").to_pylist(),
            tabla.column("fecha_recepcion").to_pylist(),
        ):
            atraso = (recepcion.date() - emision).days
            if atraso >= 5:
                tardios += 1
            maximo = max(maximo, atraso)
    declarado = manifiesto["trampas"]["T-1"]["conteo"]
    assert tardios == declarado, f"tardios reales {tardios} != declarados {declarado}"
    assert maximo <= 45, f"un DTE llego {maximo} dias tarde; el tope de T-1 es 45"


# --- T-2 ---------------------------------------------------------------------
def test_t2_folios_duplicados_son_localizables(datos, manifiesto):
    tabla = _tabla(datos, "recepcion_diaria", ["rut_emisor", "tipo_dte", "folio"])
    claves = Counter(
        zip(
            tabla.column("rut_emisor").to_pylist(),
            tabla.column("tipo_dte").to_pylist(),
            tabla.column("folio").to_pylist(),
        )
    )
    repetidas = {clave for clave, veces in claves.items() if veces > 1}
    declaradas = {
        (rut, tipo, folio)
        for rut, tipo, folio in manifiesto["trampas"]["T-2"]["folios"]
    }
    assert repetidas == declaradas, (
        "los duplicados encontrados no son los que declara el manifiesto"
    )
    assert len(declaradas) == manifiesto["trampas"]["T-2"]["conteo"]


def test_t2_el_insert_ingenuo_duplicaria(datos, manifiesto):
    """El sentido pedagogico: contar distinto por llave natural da menos filas."""
    total = ds.dataset(datos / "recepcion_diaria", format="parquet").count_rows()
    tabla = _tabla(datos, "recepcion_diaria", ["rut_emisor", "tipo_dte", "folio"])
    distintas = len(
        set(
            zip(
                tabla.column("rut_emisor").to_pylist(),
                tabla.column("tipo_dte").to_pylist(),
                tabla.column("folio").to_pylist(),
            )
        )
    )
    assert total - distintas == manifiesto["trampas"]["T-2"]["conteo"]


# --- T-3 ---------------------------------------------------------------------
def test_t3_cadenas_de_rectificatorias(datos, manifiesto):
    tabla = _tabla(datos, "f29", ["rut", "periodo", "correlativo"])
    versiones: dict[tuple[str, str], list[int]] = {}
    for rut, periodo, correlativo in zip(
        tabla.column("rut").to_pylist(),
        tabla.column("periodo").to_pylist(),
        tabla.column("correlativo").to_pylist(),
    ):
        versiones.setdefault((rut, periodo), []).append(correlativo)

    cadenas = {clave: v for clave, v in versiones.items() if len(v) > 1}
    assert len(cadenas) == manifiesto["trampas"]["T-3"]["conteo"]

    declaradas = {
        (rut, periodo): total
        for rut, periodo, total in manifiesto["trampas"]["T-3"]["cadenas"]
    }
    assert set(cadenas) == set(declaradas)
    for clave, correlativos in cadenas.items():
        assert len(correlativos) == declaradas[clave]
        assert 2 <= len(correlativos) <= 4, "las cadenas van de 2 a 4 versiones"


def test_t3_la_vigente_es_la_de_mayor_correlativo(datos):
    tabla = _tabla(datos, "f29", ["rut", "periodo", "correlativo", "origen"])
    por_clave: dict[tuple[str, str], list[tuple[int, str]]] = {}
    for rut, periodo, correlativo, origen in zip(
        tabla.column("rut").to_pylist(),
        tabla.column("periodo").to_pylist(),
        tabla.column("correlativo").to_pylist(),
        tabla.column("origen").to_pylist(),
    ):
        por_clave.setdefault((rut, periodo), []).append((correlativo, origen))

    for versiones in por_clave.values():
        versiones.sort()
        assert versiones[0][1] == "ORIGINAL"
        for correlativo, origen in versiones[1:]:
            assert origen == "RECTIFICATORIA", (
                f"el correlativo {correlativo} deberia ser RECTIFICATORIA"
            )


# --- T-4 ---------------------------------------------------------------------
def test_t4_las_nc_anulan_periodos_cerrados(datos, manifiesto):
    """
    Cada par declarado debe existir y la factura anulada tiene que ser de un
    periodo ESTRICTAMENTE anterior: si fuera del mismo mes, no habria nada que
    descubrir con time travel.
    """
    pares = manifiesto["trampas"]["T-4"]["pares"]
    assert pares, "no se generaron notas de credito sobre periodos cerrados"
    assert len(pares) == manifiesto["trampas"]["T-4"]["conteo"]

    for _rut_nc, tipo_nc, _folio_nc, _rut_ref, tipo_ref, _folio_ref, periodo_ref, periodo_nc, alcance in pares:
        assert tipo_nc == 61, "T-4 es siempre nota de credito"
        assert tipo_ref in (33, 34), "una NC de T-4 anula una factura"
        assert periodo_ref < periodo_nc, (
            f"la factura anulada ({periodo_ref}) no es de un periodo anterior "
            f"a la NC ({periodo_nc})"
        )
        assert alcance in ("total", "parcial")


def test_t4_las_nc_declaradas_existen_en_los_datos(datos, manifiesto):
    presentes = set()
    for ruta in ("dte/lote_historico", "dte/lote_reciente", "recepcion_diaria"):
        tabla = _tabla(datos, ruta, ["rut_emisor", "tipo_dte", "folio"])
        presentes.update(
            zip(
                tabla.column("rut_emisor").to_pylist(),
                tabla.column("tipo_dte").to_pylist(),
                tabla.column("folio").to_pylist(),
            )
        )
    faltantes = [
        (p[0], p[1], p[2])
        for p in manifiesto["trampas"]["T-4"]["pares"]
        if (p[0], p[1], p[2]) not in presentes
    ]
    assert faltantes == [], f"NC declaradas en T-4 que no existen: {faltantes[:5]}"


# --- T-5 ---------------------------------------------------------------------
def test_t5_las_filas_corruptas_violan_la_aritmetica(datos, manifiesto):
    tabla = _tabla(datos, "recepcion_diaria")
    indice = {
        (fila["rut_emisor"], fila["tipo_dte"], fila["folio"]): fila
        for fila in tabla.to_pylist()
    }
    declaradas = manifiesto["trampas"]["T-5"]["filas"]
    assert len(declaradas) == manifiesto["trampas"]["T-5"]["conteo"]

    for rut, tipo, folio, motivo in declaradas:
        fila = indice[(rut, tipo, folio)]
        iva_esperado = (fila["monto_neto"] * TASA).quantize(Decimal("0.01"))
        suma = fila["monto_neto"] + fila["monto_exento"] + fila["monto_iva"]
        rompe = (
            abs(fila["monto_iva"] - iva_esperado) > TOLERANCIA_REDONDEO
            or abs(fila["monto_total"] - suma) > TOLERANCIA_REDONDEO
            or (fila["monto_total"] < 0 and fila["tipo_dte"] != 61)
        )
        assert rompe, f"la fila {rut}/{tipo}/{folio} ({motivo}) no viola nada"


def test_t5_las_filas_sanas_cuadran(datos, manifiesto):
    """
    El otro lado de la moneda: si las filas sanas tambien fallaran, el audit del
    WAP marcaria todo y la trampa perderia sentido.
    """
    declaradas = {
        (rut, tipo, folio) for rut, tipo, folio, _ in manifiesto["trampas"]["T-5"]["filas"]
    }
    infractoras = []
    for fila in _tabla(datos, "recepcion_diaria").to_pylist():
        clave = (fila["rut_emisor"], fila["tipo_dte"], fila["folio"])
        if clave in declaradas:
            continue
        iva_esperado = (fila["monto_neto"] * TASA).quantize(Decimal("0.01"))
        suma = fila["monto_neto"] + fila["monto_exento"] + fila["monto_iva"]
        if abs(fila["monto_iva"] - iva_esperado) > TOLERANCIA_REDONDEO:
            infractoras.append(clave)
        elif abs(fila["monto_total"] - suma) > TOLERANCIA_REDONDEO:
            infractoras.append(clave)
    assert infractoras == [], (
        f"{len(infractoras)} filas no declaradas violan la aritmetica: {infractoras[:5]}"
    )


def test_t5_los_motivos_declarados_son_los_esperados(manifiesto):
    motivos = {motivo for _, _, _, motivo in manifiesto["trampas"]["T-5"]["filas"]}
    assert motivos <= {"iva_inconsistente", "total_inconsistente", "monto_negativo"}
    assert len(motivos) >= 2, "conviene mas de un tipo de corrupcion"


# --- T-6 ---------------------------------------------------------------------
def test_t6_el_lote_reciente_agrega_exactamente_dos_columnas(datos):
    v1 = ds.dataset(datos / "dte/lote_historico", format="parquet").schema
    v2 = ds.dataset(datos / "dte/lote_reciente", format="parquet").schema
    agregadas = [n for n in v2.names if n not in v1.names]
    assert agregadas == list(COLUMNAS_V2)
    assert len(v2.names) == len(v1.names) + 2
    assert [n for n in v1.names if n not in v2.names] == [], (
        "el esquema v2 no puede perder columnas de v1"
    )


def test_t6_recepcion_comparte_el_esquema_v2(datos):
    """El MERGE del M4 lee recepcion_diaria: su esquema debe ser el v2."""
    v2 = ds.dataset(datos / "dte/lote_reciente", format="parquet").schema
    recepcion = ds.dataset(datos / "recepcion_diaria", format="parquet").schema
    assert recepcion.names == v2.names


# --- T-7 ---------------------------------------------------------------------
def test_t7_recepcion_esta_fragmentada(datos, manifiesto):
    archivos = list((datos / "recepcion_diaria").rglob("*.parquet"))
    assert len(archivos) >= MINIMO_ARCHIVOS_DEV, (
        f"solo {len(archivos)} archivos; en escala dev se esperan "
        f">={MINIMO_ARCHIVOS_DEV} para que la compactacion del M8 tenga sentido"
    )
    assert len(archivos) == manifiesto["trampas"]["T-7"]["archivos"]


def test_t7_los_archivos_son_efectivamente_chicos(datos):
    archivos = sorted((datos / "recepcion_diaria").rglob("*.parquet"))
    mayor = max(a.stat().st_size for a in archivos)
    assert mayor < 5 * 1024 * 1024, (
        "los fragmentos deberian ser chicos; si ya son grandes, el laboratorio "
        "de compactacion no tendria nada que mejorar"
    )
