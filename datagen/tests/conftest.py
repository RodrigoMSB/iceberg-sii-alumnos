"""
Fixtures compartidas.

Los tests corren SIEMPRE en escala dev: son unos segundos de generacion y las
trampas se comportan igual que en escala curso (lo unico que cambia es el
volumen por periodo).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from datagen.cli import SEMILLA_POR_DEFECTO  # noqa: E402
from datagen.escalas import obtener_escala  # noqa: E402
from datagen.generador import Generador  # noqa: E402
from datagen.perfiles import obtener_perfil  # noqa: E402

RAIZ_REPO = Path(__file__).resolve().parents[2]


def generar_en(destino: Path, semilla: int = SEMILLA_POR_DEFECTO) -> dict:
    generador = Generador(
        perfil=obtener_perfil("chile"),
        escala=obtener_escala("dev"),
        semilla=semilla,
        salida=destino,
    )
    manifiesto = generador.ejecutar()
    (destino / "manifiesto.json").write_text(
        json.dumps(manifiesto, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return manifiesto


@pytest.fixture(scope="session")
def universo(tmp_path_factory) -> tuple[Path, dict]:
    """Genera el universo una sola vez para toda la sesion de tests."""
    destino = tmp_path_factory.mktemp("universo")
    manifiesto = generar_en(destino)
    return destino, manifiesto


@pytest.fixture(scope="session")
def datos(universo) -> Path:
    return universo[0]


@pytest.fixture(scope="session")
def manifiesto(universo) -> dict:
    return universo[1]
