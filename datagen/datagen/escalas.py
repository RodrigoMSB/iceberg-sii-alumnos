"""
Escalas de generacion.

  dev   -> ~100 mil DTEs. Corre en segundos. Es la escala de los tests.
  curso -> ~2 millones de DTEs. Es la que se usa para dictar el curso.

Los periodos son identicos en ambas escalas: lo que cambia es el volumen por
periodo. Asi las trampas se comportan igual en tests y en clase.
"""

from __future__ import annotations

from dataclasses import dataclass

# Rango temporal del universo DGT (SPEC-002 §4.2).
PERIODOS_HISTORICO = tuple(
    f"{anio}-{mes:02d}" for anio in (2024, 2025) for mes in range(1, 13)
)
PERIODOS_RECIENTE = tuple(f"2026-{mes:02d}" for mes in range(1, 6))
PERIODO_RECEPCION = "2026-06"

# --- La bodega de diez anios (laboratorio 17) -------------------------------
#
# NO forma parte del universo que declara datos/manifiesto.json. Es un dataset
# aparte, opcional, que se pide con --bodega y se escribe en otra carpeta: el
# laboratorio 17 necesita volumen y diez anios de historia para que se note la
# diferencia entre un diseno y otro, y eso no cabe en el universo del curso.
#
# Va aqui, al lado de los otros periodos, y NO tocando PERIODOS_HISTORICO:
# ampliar esa tupla correria el flujo de azar de los DTE y cambiaria byte a byte
# los datos de 2024 y 2025 de los que dependen los diecisiete laboratorios.
ANIOS_BODEGA = tuple(range(2015, 2025))
PERIODOS_BODEGA = tuple(
    f"{anio}-{mes:02d}" for anio in ANIOS_BODEGA for mes in range(1, 13)
)
FILAS_POR_ANIO_BODEGA = 1_000_000


@dataclass(frozen=True)
class Escala:
    nombre: str
    contribuyentes: int
    dtes_historico: int
    dtes_reciente: int
    dtes_recepcion: int
    # T-7: en cuantos archivos Parquet se fragmenta recepcion_diaria.
    archivos_recepcion: int
    # Fraccion de contribuyentes que declara F29 en cada periodo.
    cobertura_f29: float
    # Tope del reservorio de facturas referenciables (acota memoria en escala
    # curso sin romper la integridad referencial de CA-6).
    tope_reservorio: int


ESCALAS: dict[str, Escala] = {
    "dev": Escala(
        nombre="dev",
        contribuyentes=1_000,
        dtes_historico=60_000,
        dtes_reciente=25_000,
        dtes_recepcion=15_000,
        archivos_recepcion=50,
        cobertura_f29=0.70,
        tope_reservorio=60_000,
    ),
    "curso": Escala(
        nombre="curso",
        contribuyentes=10_000,
        dtes_historico=1_400_000,
        dtes_reciente=400_000,
        dtes_recepcion=200_000,
        archivos_recepcion=500,
        cobertura_f29=0.70,
        tope_reservorio=300_000,
    ),
}


def obtener_escala(nombre: str) -> Escala:
    clave = nombre.strip().lower()
    if clave not in ESCALAS:
        raise ValueError(
            f"escala desconocida: '{nombre}'. Disponibles: {', '.join(sorted(ESCALAS))}"
        )
    return ESCALAS[clave]
