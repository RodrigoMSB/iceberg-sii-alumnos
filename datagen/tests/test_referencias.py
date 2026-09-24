"""
CA-6: integridad referencial.

Dos invariantes que los laboratorios dan por ciertas:
  - toda nota (56/61) apunta a un documento que existe de verdad;
  - toda cadena de rectificatorias tiene correlativos consecutivos desde 1.

Si alguna se rompiera, el alumno culparia a su consulta antes que a los datos.
"""

from __future__ import annotations

import pyarrow.dataset as ds

RUTAS_DTE = ("dte/lote_historico", "dte/lote_reciente", "recepcion_diaria")


def _todas_las_claves(datos) -> set[tuple[str, int, int]]:
    claves: set[tuple[str, int, int]] = set()
    for ruta in RUTAS_DTE:
        tabla = ds.dataset(datos / ruta, format="parquet").to_table(
            columns=["rut_emisor", "tipo_dte", "folio"]
        )
        claves.update(
            zip(
                tabla.column("rut_emisor").to_pylist(),
                tabla.column("tipo_dte").to_pylist(),
                tabla.column("folio").to_pylist(),
            )
        )
    return claves


def test_toda_nota_referencia_un_documento_existente(datos):
    universo = _todas_las_claves(datos)
    huerfanas = []
    for ruta in RUTAS_DTE:
        tabla = ds.dataset(datos / ruta, format="parquet").to_table(
            columns=["tipo_dte", "referencia_rut", "referencia_tipo", "referencia_folio"]
        ).to_pylist()
        for fila in tabla:
            if fila["tipo_dte"] not in (56, 61):
                continue
            clave = (
                fila["referencia_rut"],
                fila["referencia_tipo"],
                fila["referencia_folio"],
            )
            if None in clave or clave not in universo:
                huerfanas.append((ruta, clave))
    assert huerfanas == [], f"notas apuntando al vacio: {huerfanas[:5]}"


def test_solo_las_notas_traen_referencia(datos):
    for ruta in RUTAS_DTE:
        tabla = ds.dataset(datos / ruta, format="parquet").to_table(
            columns=["tipo_dte", "referencia_folio"]
        )
        for tipo, referencia in zip(
            tabla.column("tipo_dte").to_pylist(),
            tabla.column("referencia_folio").to_pylist(),
        ):
            if tipo in (56, 61):
                assert referencia is not None, f"{ruta}: nota {tipo} sin referencia"
            else:
                assert referencia is None, (
                    f"{ruta}: el documento {tipo} no deberia referenciar nada"
                )


def test_las_notas_de_credito_restan(datos, manifiesto):
    """
    La NC lleva montos negativos: resta en la contabilidad.

    Se excluyen las filas corruptas de T-5: una corrupcion de tipo
    'total_inconsistente' puede empujar el total de una NC hasta volverlo
    positivo, y eso es precisamente la anomalia que el M6 debe detectar, no un
    defecto del generador.
    """
    corruptas = {
        (rut, tipo, folio)
        for rut, tipo, folio, _ in manifiesto["trampas"]["T-5"]["filas"]
    }
    for ruta in RUTAS_DTE:
        tabla = ds.dataset(datos / ruta, format="parquet").to_table(
            columns=["rut_emisor", "tipo_dte", "folio", "monto_total"]
        )
        positivas = [
            (rut, folio)
            for rut, tipo, folio, monto in zip(
                tabla.column("rut_emisor").to_pylist(),
                tabla.column("tipo_dte").to_pylist(),
                tabla.column("folio").to_pylist(),
                tabla.column("monto_total").to_pylist(),
            )
            if tipo == 61
            and monto > 0
            and (rut, tipo, folio) not in corruptas
        ]
        assert positivas == [], (
            f"{ruta}: notas de credito sanas con monto positivo: {positivas[:5]}"
        )


def test_correlativos_consecutivos_desde_uno(datos):
    tabla = ds.dataset(datos / "f29", format="parquet").to_table(
        columns=["rut", "periodo", "correlativo"]
    )
    cadenas: dict[tuple[str, str], list[int]] = {}
    for rut, periodo, correlativo in zip(
        tabla.column("rut").to_pylist(),
        tabla.column("periodo").to_pylist(),
        tabla.column("correlativo").to_pylist(),
    ):
        cadenas.setdefault((rut, periodo), []).append(correlativo)

    rotas = []
    for clave, correlativos in cadenas.items():
        esperado = list(range(1, len(correlativos) + 1))
        if sorted(correlativos) != esperado:
            rotas.append((clave, sorted(correlativos)))
    assert rotas == [], f"cadenas con correlativos no consecutivos: {rotas[:5]}"


def test_el_folio_es_unico_por_emisor_y_tipo_en_los_lotes_limpios(datos):
    """
    Los lotes historico y reciente NO tienen duplicados: el unico lugar donde se
    repite un folio es recepcion_diaria, que es donde vive la trampa T-2.
    """
    for ruta in ("dte/lote_historico", "dte/lote_reciente"):
        tabla = ds.dataset(datos / ruta, format="parquet").to_table(
            columns=["rut_emisor", "tipo_dte", "folio"]
        )
        claves = list(
            zip(
                tabla.column("rut_emisor").to_pylist(),
                tabla.column("tipo_dte").to_pylist(),
                tabla.column("folio").to_pylist(),
            )
        )
        assert len(claves) == len(set(claves)), f"{ruta} trae folios repetidos"


def test_los_receptores_existen_en_el_padron(datos):
    padron = set(
        ds.dataset(datos / "contribuyentes", format="parquet")
        .to_table(columns=["rut"])
        .column("rut")
        .to_pylist()
    )
    tabla = ds.dataset(datos / "dte/lote_reciente", format="parquet").to_table(
        columns=["rut_emisor", "rut_receptor"]
    )
    for columna in ("rut_emisor", "rut_receptor"):
        desconocidos = [
            r for r in tabla.column(columna).to_pylist() if r not in padron
        ]
        assert desconocidos == [], f"{columna} fuera del padron: {desconocidos[:5]}"
