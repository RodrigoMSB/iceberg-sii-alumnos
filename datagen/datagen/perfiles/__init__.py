"""Registro de perfiles de pais."""

from __future__ import annotations

from .base import PerfilPais, TipoDocumento
from .chile import PerfilChile

# Perfiles disponibles. 'peru' queda deliberadamente fuera de esta entrega: la
# abstraccion esta lista (ver perfiles/base.py) pero el perfil no se implementa.
_PERFILES: dict[str, type[PerfilPais]] = {
    "chile": PerfilChile,
}


def perfiles_disponibles() -> tuple[str, ...]:
    return tuple(sorted(_PERFILES))


def obtener_perfil(nombre: str) -> PerfilPais:
    clave = nombre.strip().lower()
    if clave not in _PERFILES:
        disponibles = ", ".join(perfiles_disponibles())
        raise ValueError(
            f"perfil de pais desconocido: '{nombre}'. Disponibles: {disponibles}"
        )
    return _PERFILES[clave]()


__all__ = [
    "PerfilPais",
    "TipoDocumento",
    "PerfilChile",
    "obtener_perfil",
    "perfiles_disponibles",
]
