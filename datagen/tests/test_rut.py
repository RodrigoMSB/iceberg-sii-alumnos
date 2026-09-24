"""CA-3: el 100% de los RUT generados valida modulo 11."""

from __future__ import annotations

import pyarrow.dataset as ds
import pytest

from datagen.perfiles.chile import digito_verificador, formatear_rut, validar_rut


def test_caso_canonico():
    """12.345.678-5 es el ejemplo de manual del algoritmo chileno."""
    assert digito_verificador(12345678) == "5"


def test_produce_los_once_digitos_posibles():
    encontrados = {digito_verificador(c) for c in range(1_000_000, 1_002_000)}
    assert encontrados == set("0123456789K")


@pytest.mark.parametrize(
    "rut_invalido",
    ["12345678-9", "76000000-Z", "sin-guion", "76000000", "", "-5", "abc-1"],
)
def test_rechaza_invalidos(rut_invalido):
    assert validar_rut(rut_invalido) is False


def test_acepta_dv_en_minuscula():
    cuerpo = next(c for c in range(1_000_000, 1_010_000) if digito_verificador(c) == "K")
    assert validar_rut(f"{cuerpo}-k") is True


def test_todos_los_contribuyentes_validan(datos):
    tabla = ds.dataset(datos / "contribuyentes", format="parquet").to_table()
    ruts = tabla.column("rut").to_pylist()
    assert ruts, "no se generaron contribuyentes"
    invalidos = [r for r in ruts if not validar_rut(r)]
    assert invalidos == [], f"RUT invalidos entre los contribuyentes: {invalidos[:5]}"


def test_ruts_de_contribuyentes_son_unicos(datos):
    tabla = ds.dataset(datos / "contribuyentes", format="parquet").to_table()
    ruts = tabla.column("rut").to_pylist()
    assert len(ruts) == len(set(ruts)), "hay RUT repetidos en el padron"


@pytest.mark.parametrize(
    "ruta",
    ["dte/lote_historico", "dte/lote_reciente", "recepcion_diaria"],
)
def test_ruts_de_los_dte_validan(datos, ruta):
    """Muestreo sobre los DTE: emisor y receptor deben validar igual."""
    tabla = ds.dataset(datos / ruta, format="parquet").head(4000)
    for columna in ("rut_emisor", "rut_receptor"):
        invalidos = [r for r in tabla.column(columna).to_pylist() if not validar_rut(r)]
        assert invalidos == [], f"{ruta}.{columna} trae RUT invalidos: {invalidos[:5]}"


def test_referencias_de_notas_validan(datos):
    tabla = ds.dataset(datos / "dte/lote_reciente", format="parquet").to_table()
    referencias = [r for r in tabla.column("referencia_rut").to_pylist() if r]
    assert referencias, "no hay notas con referencia en el lote reciente"
    invalidos = [r for r in referencias if not validar_rut(r)]
    assert invalidos == [], f"referencia_rut invalidos: {invalidos[:5]}"


def test_formatear_rut_es_consistente_con_validar():
    for cuerpo in range(76_000_000, 76_000_500):
        assert validar_rut(formatear_rut(cuerpo)) is True
