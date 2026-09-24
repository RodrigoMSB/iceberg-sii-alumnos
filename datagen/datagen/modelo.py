"""
Esquemas Parquet de los datasets.

Decisiones de tipos que los laboratorios dan por sentadas:

  - Los montos son decimal(18,2), NO float. Los labs comparan igualdad exacta de
    sumas (un cierre mensual que "casi" cuadra no cuadra), y en punto flotante
    esa comparacion es una loteria.
  - Las fechas son date/timestamp, NO strings. fecha_emision es una fecha
    (date32) y fecha_recepcion un instante (timestamp), porque la distancia
    entre ambas es justamente lo que estudia el M5.
  - anio_mes NO viaja dentro del archivo: es columna de PARTICION, con
    directorios 'anio_mes=2024-01' al estilo Hive. Asi el lote historico se ve
    igual que la tabla Hive particionada de la que el M7 lo migra, y un
    spark.read.parquet(ruta) descubre la particion sin trucos. Esto no
    condiciona al M5: como se particiona la tabla Iceberg de destino sigue
    siendo decision del alumno.
"""

from __future__ import annotations

import pyarrow as pa

# Montos: 18 digitos, 2 decimales.
DECIMAL_MONTO = pa.decimal128(18, 2)

ESQUEMA_CONTRIBUYENTES = pa.schema(
    [
        pa.field("rut", pa.string(), nullable=False),
        pa.field("razon_social", pa.string(), nullable=False),
        pa.field("segmento", pa.string(), nullable=False),
        pa.field("comuna", pa.string(), nullable=False),
        pa.field("giro", pa.string(), nullable=False),
        pa.field("fecha_inicio_actividades", pa.date32(), nullable=False),
        pa.field("activo", pa.bool_(), nullable=False),
    ]
)

# --- DTE ---------------------------------------------------------------------
# Esquema v1: el del lote historico.
_CAMPOS_DTE_V1 = [
    pa.field("rut_emisor", pa.string(), nullable=False),
    pa.field("razon_social_emisor", pa.string(), nullable=False),
    pa.field("rut_receptor", pa.string(), nullable=False),
    pa.field("razon_social_receptor", pa.string(), nullable=False),
    pa.field("comuna_receptor", pa.string(), nullable=False),
    pa.field("tipo_dte", pa.int32(), nullable=False),
    pa.field("folio", pa.int64(), nullable=False),
    pa.field("fecha_emision", pa.date32(), nullable=False),
    pa.field("fecha_recepcion", pa.timestamp("us"), nullable=False),
    pa.field("comuna_emisor", pa.string(), nullable=False),
    pa.field("glosa", pa.string(), nullable=False),
    # Campos que trae de verdad un feed de recepcion de DTE y que el curso usa
    # para que las consultas se parezcan a las del cliente (y para que el
    # volumen en disco sea representativo: una tabla de 6 columnas comprime
    # tanto que la compactacion del M8 no se notaria).
    pa.field("forma_pago", pa.string(), nullable=False),
    pa.field("codigo_vendedor", pa.string(), nullable=False),
    pa.field("numero_orden_compra", pa.string(), nullable=False),
    pa.field("observaciones", pa.string(), nullable=False),
    # Detalle de lineas del documento, en el formato compacto en que lo entrega
    # el feed de la DGT: "codigo|descripcion|cantidad|precio" por linea,
    # separadas por ';'. Un DTE real es sobre todo esto: sin las lineas, el
    # dataset no se parece en peso ni en forma al del cliente.
    pa.field("detalle", pa.string(), nullable=False),
    pa.field("monto_neto", DECIMAL_MONTO, nullable=False),
    pa.field("monto_exento", DECIMAL_MONTO, nullable=False),
    pa.field("monto_iva", DECIMAL_MONTO, nullable=False),
    pa.field("monto_total", DECIMAL_MONTO, nullable=False),
    # Solo las notas (56/61) referencian; en el resto van nulos.
    pa.field("referencia_tipo", pa.int32(), nullable=True),
    pa.field("referencia_folio", pa.int64(), nullable=True),
    pa.field("referencia_rut", pa.string(), nullable=True),
    pa.field("estado_sii", pa.string(), nullable=False),
]

# T-6: el esquema v2 agrega exactamente dos columnas al final.
_CAMPOS_DTE_V2 = _CAMPOS_DTE_V1 + [
    pa.field("canal_emision", pa.string(), nullable=True),
    pa.field("codigo_sucursal", pa.string(), nullable=True),
]

ESQUEMA_DTE_V1 = pa.schema(_CAMPOS_DTE_V1)
ESQUEMA_DTE_V2 = pa.schema(_CAMPOS_DTE_V2)

COLUMNAS_DTE_V1 = tuple(campo.name for campo in _CAMPOS_DTE_V1)
COLUMNAS_DTE_V2 = tuple(campo.name for campo in _CAMPOS_DTE_V2)

ESQUEMA_F29 = pa.schema(
    [
        pa.field("rut", pa.string(), nullable=False),
        pa.field("periodo", pa.string(), nullable=False),
        # T-3: la cadena de rectificatorias. Vigente = mayor correlativo.
        pa.field("correlativo", pa.int32(), nullable=False),
        pa.field("fecha_presentacion", pa.date32(), nullable=False),
        pa.field("ventas_netas", DECIMAL_MONTO, nullable=False),
        pa.field("ventas_exentas", DECIMAL_MONTO, nullable=False),
        pa.field("compras_netas", DECIMAL_MONTO, nullable=False),
        pa.field("iva_debito", DECIMAL_MONTO, nullable=False),
        pa.field("iva_credito", DECIMAL_MONTO, nullable=False),
        pa.field("impuesto_determinado", DECIMAL_MONTO, nullable=False),
        pa.field("origen", pa.string(), nullable=False),
    ]
)

SEGMENTOS = ("MICRO", "PEQUENA", "MEDIANA", "GRANDE")

GIROS = (
    "Venta al por menor de articulos de ferreteria",
    "Servicios de ingenieria y consultoria tecnica",
    "Transporte de carga por carretera",
    "Cultivo de frutas y hortalizas",
    "Elaboracion de productos alimenticios",
    "Construccion de edificios residenciales",
    "Venta al por mayor de maquinaria",
    "Fabricacion de productos textiles",
    "Reparacion de vehiculos automotores",
    "Servicios de informatica y programacion",
    "Comercio al por mayor de alimentos",
    "Actividades de asesoria empresarial",
)

CANALES_EMISION = ("PORTAL_MIPYME", "SOFTWARE_MERCADO", "API_DGT", "CONTINGENCIA")

FORMAS_PAGO = ("CONTADO", "CREDITO_30", "CREDITO_60", "CREDITO_90", "TRANSFERENCIA")

CONTACTOS = (
    "M. Rojas", "P. Fuentes", "C. Munoz", "J. Salazar", "A. Vergara",
    "R. Tapia", "L. Cifuentes", "N. Herrera", "S. Molina", "D. Aguilera",
)

ESTADOS_SII = ("ACEPTADO", "ACEPTADO_CON_REPAROS", "EN_PROCESO")


# Indice de cada columna dentro de la fila-tupla que arma el generador.
# Se deriva del esquema para que agregar una columna no obligue a recontar
# posiciones a mano (v1 es prefijo de v2, asi que los indices compartidos
# coinciden en ambos esquemas).
INDICE_DTE = {nombre: posicion for posicion, nombre in enumerate(COLUMNAS_DTE_V2)}
