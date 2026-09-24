"""
Escritura de Parquet determinista.

Dos corridas con la misma semilla deben producir bytes identicos (CA-2), asi que
aqui se fijan todas las opciones que podrian variar entre corridas: compresion,
tamano de row group y version del formato. No se escribe ninguna marca de
tiempo: el manifiesto tampoco lleva fecha de generacion, justamente para que los
checksums sean comparables.
"""

from __future__ import annotations

import shutil
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq

COMPRESION = "snappy"
VERSION_PARQUET = "2.6"
FILAS_POR_GRUPO = 50_000


def limpiar_directorio(ruta: Path) -> None:
    """Deja el directorio vacio: regenerar no debe mezclar con corridas previas."""
    if ruta.exists():
        shutil.rmtree(ruta)
    ruta.mkdir(parents=True, exist_ok=True)


def escribir_tabla(tabla: pa.Table, destino: Path) -> int:
    """Escribe una tabla como un unico Parquet. Devuelve el numero de filas."""
    destino.parent.mkdir(parents=True, exist_ok=True)
    pq.write_table(
        tabla,
        destino,
        compression=COMPRESION,
        version=VERSION_PARQUET,
        row_group_size=FILAS_POR_GRUPO,
        # Sin estadisticas de pagina: no aportan al lab y agregan variabilidad.
        write_statistics=True,
        store_schema=True,
    )
    return tabla.num_rows


def construir_tabla(columnas: dict[str, list], esquema: pa.Schema) -> pa.Table:
    """
    Arma una tabla respetando el orden de columnas del esquema.

    Se construye por columnas (no fila a fila) porque en escala curso son
    millones de filas y armar dicts por fila multiplica el tiempo por diez.
    """
    arreglos = [
        pa.array(columnas[campo.name], type=campo.type) for campo in esquema
    ]
    return pa.Table.from_arrays(arreglos, schema=esquema)
