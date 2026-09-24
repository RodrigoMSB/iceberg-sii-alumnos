"""
Las trampas pedagogicas.

Cada anomalia de los datos esta sembrada a proposito para que un laboratorio
tenga un problema real que resolver. No son ruido: son el enunciado.

Las tasas de aqui son objetivos de diseno. El generador las aplica como conteos
EXACTOS (calculados sobre el plan de generacion, no por sorteo independiente
fila a fila), de modo que el manifiesto pueda afirmar numeros redondos y los
tests puedan validarlos sin margen estadistico.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Trampa:
    identificador: str
    nombre: str
    descripcion: str
    tasa_objetivo: float
    sobre: str
    alimenta: str


TRAMPAS: tuple[Trampa, ...] = (
    Trampa(
        "T-1",
        "DTEs tardios",
        "fecha_recepcion hasta 45 dias despues de fecha_emision: sucursales "
        "rurales sin conectividad y contingencia en papel",
        0.04,
        "dte (los tres lotes)",
        "M5: particionar por emision o por recepcion duele distinto",
    ),
    Trampa(
        "T-2",
        "Folios duplicados",
        "mismo (rut_emisor, tipo_dte, folio) enviado dos veces con diferencias "
        "menores, como pasa con los reenvios de un cliente que no recibio acuse",
        0.005,
        "recepcion_diaria",
        "M4: el INSERT ingenuo duplica; de ahi nace el MERGE",
    ),
    Trampa(
        "T-3",
        "Rectificatorias F29",
        "cadenas de 2 a 4 versiones del mismo (rut, periodo); vigente es la de "
        "mayor correlativo",
        0.08,
        "f29",
        "M4: upsert por llave natural",
    ),
    Trampa(
        "T-4",
        "Notas de credito sobre periodos cerrados",
        "NC 61 que anula total o parcialmente una factura de un periodo ya "
        "cerrado: cambia el pasado sin que nadie lo note",
        0.02,
        "facturas (tipos 33 y 34)",
        "M6: la pregunta de auditoria solo se responde con time travel",
    ),
    Trampa(
        "T-5",
        "Montos corruptos",
        "filas donde el IVA no cuadra con el neto, el total no cuadra con la "
        "suma, o hay montos negativos en documentos que no son nota de credito",
        0.003,
        "recepcion_diaria",
        "M6: el WAP tiene que atrapar algo; un audit que siempre pasa no ensena",
    ),
    Trampa(
        "T-6",
        "Evolucion de esquema",
        "el lote historico trae el esquema v1; el lote reciente agrega "
        "canal_emision y codigo_sucursal",
        0.0,
        "estructura de los lotes",
        "M5: schema evolution con datos reales de ambas epocas",
    ),
    Trampa(
        "T-7",
        "Archivos chicos",
        "recepcion_diaria se escribe fragmentada en cientos de Parquet chicos, "
        "como una ingesta por goteo",
        0.0,
        "estructura fisica de recepcion_diaria",
        "M8: compactacion con mejora medible antes y despues",
    ),
)

TRAMPAS_POR_ID: dict[str, Trampa] = {t.identificador: t for t in TRAMPAS}

# Tolerancia de redondeo, en pesos: una diferencia menor o igual a este valor
# NO se considera corrupcion (T-5). El generador produce las filas sanas con
# diferencia exacta 0, y las corruptas muy por encima de este umbral.
TOLERANCIA_REDONDEO = 2

# T-6: columnas que aparecen solo en el esquema v2.
COLUMNAS_V2 = ("canal_emision", "codigo_sucursal")
