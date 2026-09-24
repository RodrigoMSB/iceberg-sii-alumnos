"""
CA-2: misma semilla, mismos bytes.

Si esto se rompe, todo el curso se rompe: las guias afirman numeros exactos
("hay 75 folios duplicados") y los tests de cada laboratorio los validan contra
el manifiesto. Un generador que varia entre corridas convierte cada afirmacion
del material en una mentira intermitente.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

from conftest import generar_en


def _huella_del_arbol(raiz: Path) -> list[tuple[str, str]]:
    """(ruta relativa, sha256) de cada archivo, ordenado por ruta."""
    huellas = []
    for archivo in sorted(p for p in raiz.rglob("*") if p.is_file()):
        digest = hashlib.sha256(archivo.read_bytes()).hexdigest()
        huellas.append((str(archivo.relative_to(raiz)), digest))
    return huellas


def test_misma_semilla_produce_bytes_identicos(tmp_path):
    primera = tmp_path / "corrida-1"
    segunda = tmp_path / "corrida-2"
    generar_en(primera)
    generar_en(segunda)

    huella_1 = _huella_del_arbol(primera)
    huella_2 = _huella_del_arbol(segunda)

    assert [r for r, _ in huella_1] == [r for r, _ in huella_2], (
        "las dos corridas produjeron arboles de archivos distintos"
    )
    distintos = [
        ruta
        for (ruta, a), (_, b) in zip(huella_1, huella_2)
        if a != b
    ]
    assert distintos == [], f"archivos con contenido distinto entre corridas: {distintos}"


def test_semilla_distinta_produce_datos_distintos(tmp_path):
    """El control negativo: si la semilla no influye, el determinismo es falso."""
    primera = tmp_path / "semilla-a"
    segunda = tmp_path / "semilla-b"
    generar_en(primera)
    generar_en(segunda, semilla=987654)

    assert _huella_del_arbol(primera) != _huella_del_arbol(segunda)


def test_el_manifiesto_no_lleva_marca_de_tiempo(manifiesto):
    """
    Una fecha de generacion rompiria el determinismo del arbol completo.
    """
    texto = str(manifiesto).lower()
    for prohibido in ("generado_en", "timestamp_generacion", "fecha_generacion"):
        assert prohibido not in texto
