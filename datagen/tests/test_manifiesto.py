"""
CA-4: el manifiesto coincide EXACTO con los datos.

El manifiesto es el ground truth del curso. Cada test aqui vuelve a contar por
su cuenta, leyendo los Parquet, y compara contra lo declarado: si el manifiesto
dijera cualquier otra cosa, las guias mentirian.
"""

from __future__ import annotations

from decimal import Decimal

import pyarrow.compute as pc
import pyarrow.dataset as ds
import pytest

RUTAS = {
    "contribuyentes": "contribuyentes",
    "dte_lote_historico": "dte/lote_historico",
    "dte_lote_reciente": "dte/lote_reciente",
    "f29": "f29",
    "recepcion_diaria": "recepcion_diaria",
}


@pytest.mark.parametrize("dataset", sorted(RUTAS))
def test_conteo_de_filas_coincide(datos, manifiesto, dataset):
    real = ds.dataset(datos / RUTAS[dataset], format="parquet").count_rows()
    declarado = manifiesto["datasets"][dataset]["filas"]
    assert real == declarado, (
        f"{dataset}: el manifiesto declara {declarado} filas y hay {real}"
    )


@pytest.mark.parametrize("dataset", sorted(RUTAS))
def test_conteo_de_archivos_coincide(datos, manifiesto, dataset):
    archivos = list((datos / RUTAS[dataset]).rglob("*.parquet"))
    declarado = manifiesto["datasets"][dataset]["archivos"]
    assert len(archivos) == declarado


def test_suma_de_montos_coincide(datos, manifiesto):
    """
    La suma de monto_total sobre los tres lotes de DTE.

    Es el mismo numero que el CA-7 pide comprobar desde Spark, asi que si este
    test pasa y aquel falla, el problema esta en la lectura, no en los datos.
    """
    total = Decimal(0)
    for ruta in ("dte/lote_historico", "dte/lote_reciente", "recepcion_diaria"):
        tabla = ds.dataset(datos / ruta, format="parquet").to_table(
            columns=["monto_total"]
        )
        total += sum(tabla.column("monto_total").to_pylist(), Decimal(0))
    assert str(total) == manifiesto["totales"]["suma_monto_total_dte"]


def test_total_de_dtes_coincide(datos, manifiesto):
    real = sum(
        ds.dataset(datos / ruta, format="parquet").count_rows()
        for ruta in ("dte/lote_historico", "dte/lote_reciente", "recepcion_diaria")
    )
    assert real == manifiesto["totales"]["dtes"]


def test_las_tasas_reales_estan_dentro_del_cinco_por_ciento(manifiesto):
    """Las tasas de la spec son objetivos de diseno; el margen tolerado es 5%."""
    for identificador in ("T-1", "T-2", "T-3", "T-4", "T-5"):
        trampa = manifiesto["trampas"][identificador]
        objetivo = trampa["tasa_objetivo"]
        real = trampa["tasa_real"]
        assert objetivo > 0
        desvio = abs(real - objetivo) / objetivo
        assert desvio <= 0.05, (
            f"{identificador}: tasa real {real} se aparta {desvio:.1%} "
            f"del objetivo {objetivo}"
        )


def test_declara_semilla_escala_y_pais(manifiesto):
    assert manifiesto["semilla"] == 20260813
    assert manifiesto["escala"] == "dev"
    assert manifiesto["pais"] == "chile"
    assert manifiesto["tasa_impuesto"] == "0.19"


def test_todas_las_trampas_estan_documentadas(manifiesto):
    esperadas = {f"T-{n}" for n in range(1, 8)}
    assert set(manifiesto["trampas"]) == esperadas
    for identificador, trampa in manifiesto["trampas"].items():
        assert trampa["nombre"], f"{identificador} sin nombre"
        assert trampa["descripcion"], f"{identificador} sin descripcion"
        assert trampa["alimenta"], f"{identificador} no declara que lab alimenta"


def test_los_montos_no_son_de_punto_flotante(datos):
    """decimal(18,2): los labs comparan igualdad exacta de sumas."""
    esquema = ds.dataset(datos / "dte/lote_historico", format="parquet").schema
    for columna in ("monto_neto", "monto_exento", "monto_iva", "monto_total"):
        tipo = str(esquema.field(columna).type)
        assert tipo == "decimal128(18, 2)", f"{columna} es {tipo}"


def test_las_fechas_no_son_texto(datos):
    esquema = ds.dataset(datos / "dte/lote_reciente", format="parquet").schema
    assert str(esquema.field("fecha_emision").type) == "date32[day]"
    assert str(esquema.field("fecha_recepcion").type).startswith("timestamp")


def test_no_hay_montos_nulos(datos):
    tabla = ds.dataset(datos / "dte/lote_historico", format="parquet").to_table(
        columns=["monto_total"]
    )
    assert pc.sum(pc.is_null(tabla.column("monto_total"))).as_py() == 0
