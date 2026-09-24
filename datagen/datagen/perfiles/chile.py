"""
Perfil Chile: RUT modulo 11, tipos de DTE del SII, IVA 19%, F29.

Advertencia de dominio: la DGT es una administracion tributaria ficticia. Los
RUT que emite este modulo son sinteticos y se generan en un rango alto reservado
(ver RANGO_RUT) que no corresponde a contribuyentes reales.
"""

from __future__ import annotations

from decimal import Decimal
from random import Random

from .base import PerfilPais, TipoDocumento

# Rango de cuerpo de RUT usado por el generador. Se elige alto y acotado para no
# colisionar con RUT de personas naturales reales (que viven muy por debajo).
RANGO_RUT = (76_000_000, 79_999_999)

# Codigos oficiales de DTE del SII.
TIPOS_DTE: dict[int, TipoDocumento] = {
    33: TipoDocumento(33, "factura electronica afecta", afecto=True),
    34: TipoDocumento(34, "factura electronica exenta", afecto=False),
    39: TipoDocumento(39, "boleta electronica", afecto=True),
    52: TipoDocumento(52, "guia de despacho electronica", afecto=False),
    56: TipoDocumento(56, "nota de debito electronica", afecto=True, es_nota=True, signo=1),
    61: TipoDocumento(61, "nota de credito electronica", afecto=True, es_nota=True, signo=-1),
}

COMUNAS = (
    "Santiago", "Providencia", "Las Condes", "Nunoa", "Maipu", "La Florida",
    "Puente Alto", "Valparaiso", "Vina del Mar", "Quilpue", "Concepcion",
    "Talcahuano", "Chillan", "Temuco", "Valdivia", "Osorno", "Puerto Montt",
    "Castro", "Coyhaique", "Punta Arenas", "La Serena", "Coquimbo", "Ovalle",
    "Copiapo", "Antofagasta", "Calama", "Iquique", "Arica", "Rancagua",
    "San Fernando", "Curico", "Talca", "Linares", "Los Angeles", "Angol",
)

# Piezas para razones sociales sinteticas pronunciables. Ninguna combinacion
# apunta a una empresa real.
_PREFIJOS = (
    "Andes", "Araucaria", "Boldo", "Calafate", "Copihue", "Cordillera",
    "Huemul", "Lenga", "Litre", "Maiten", "Nalca", "Pehuen", "Quillay",
    "Rauli", "Tepa", "Ulmo", "Coihue", "Canelo", "Peumo", "Manio",
)
_SUFIJOS = (
    "Comercial", "Distribuidora", "Servicios", "Ingenieria", "Logistica",
    "Importadora", "Agricola", "Constructora", "Transportes", "Consultores",
    "Alimentos", "Maquinarias", "Textil", "Ferreteria", "Automotriz",
)
_FORMAS = ("SpA", "Ltda.", "S.A.", "EIRL")


def digito_verificador(cuerpo: int) -> str:
    """
    Digito verificador de un RUT chileno (modulo 11).

    Se recorre el cuerpo de derecha a izquierda multiplicando por la serie
    ciclica 2,3,4,5,6,7. resto 11 -> '0', resto 10 -> 'K'.
    """
    suma = 0
    factor = 2
    for caracter in reversed(str(cuerpo)):
        suma += int(caracter) * factor
        factor = 2 if factor == 7 else factor + 1
    resto = 11 - (suma % 11)
    if resto == 11:
        return "0"
    if resto == 10:
        return "K"
    return str(resto)


def formatear_rut(cuerpo: int) -> str:
    """RUT en formato 'CUERPO-DV', sin puntos (formato de intercambio del SII)."""
    return f"{cuerpo}-{digito_verificador(cuerpo)}"


def validar_rut(rut: str) -> bool:
    """True si el RUT tiene forma 'cuerpo-dv' y el dv corresponde al cuerpo."""
    if not isinstance(rut, str) or "-" not in rut:
        return False
    cuerpo, _, dv = rut.partition("-")
    if not cuerpo.isdigit() or not dv:
        return False
    return digito_verificador(int(cuerpo)) == dv.upper()


class PerfilChile(PerfilPais):
    nombre = "chile"
    moneda = "CLP"
    tasa_impuesto = Decimal("0.19")
    nombre_impuesto = "IVA"
    nombre_declaracion = "F29"
    codigos_factura = (33, 34)
    codigo_nota_credito = 61
    codigo_nota_debito = 56

    @property
    def tipos_documento(self) -> dict[int, TipoDocumento]:
        return TIPOS_DTE

    def generar_identificador(self, azar: Random) -> str:
        return formatear_rut(azar.randint(*RANGO_RUT))

    def validar_identificador(self, identificador: str) -> bool:
        return validar_rut(identificador)

    def divisiones_territoriales(self) -> tuple[str, ...]:
        return COMUNAS

    def generar_razon_social(self, azar: Random) -> str:
        return (
            f"{azar.choice(_PREFIJOS)} {azar.choice(_SUFIJOS)} "
            f"{azar.choice(_FORMAS)}"
        )
