"""
Abstraccion de perfil de pais.

El generador no sabe nada de Chile: le pide al perfil los identificadores
tributarios, los tipos de documento, la tasa de impuesto y el nombre de la
declaracion mensual. Agregar un pais es escribir un perfil nuevo y registrarlo,
sin tocar la logica de generacion ni las trampas pedagogicas.

Para agregar el perfil 'peru' (fuera del alcance de esta entrega) haria falta:
  - identificador: RUC de 11 digitos con digito verificador modulo 11 y factores
    propios de SUNAT (no sirve el algoritmo chileno).
  - tipos de documento: comprobantes SUNAT (01 factura, 03 boleta, 07 nota de
    credito, 08 nota de debito) en vez de los codigos del SII.
  - tasa: IGV 18% en vez de IVA 19%.
  - declaracion mensual: PDT 621 en vez de F29, con su propia llave natural.
  - division territorial: distritos peruanos en vez de comunas chilenas.
Las trampas T-1..T-7 son independientes del pais y se reutilizan tal cual.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from decimal import Decimal
from random import Random


@dataclass(frozen=True)
class TipoDocumento:
    """Un tipo de documento tributario electronico del pais."""

    codigo: int
    nombre: str
    afecto: bool
    # Una nota (credito/debito) siempre referencia un documento previo.
    es_nota: bool = False
    # La nota de credito resta en la contabilidad.
    signo: int = 1


class PerfilPais(ABC):
    """Contrato que debe cumplir todo perfil de pais."""

    nombre: str
    moneda: str
    tasa_impuesto: Decimal
    nombre_impuesto: str
    nombre_declaracion: str
    # Codigo del documento que hace de "factura" para las trampas T-4 y T-5.
    codigos_factura: tuple[int, ...]
    codigo_nota_credito: int
    codigo_nota_debito: int

    @property
    @abstractmethod
    def tipos_documento(self) -> dict[int, TipoDocumento]:
        """Tipos de documento soportados, indexados por codigo."""

    @abstractmethod
    def generar_identificador(self, azar: Random) -> str:
        """Identificador tributario valido (RUT en Chile, RUC en Peru)."""

    @abstractmethod
    def validar_identificador(self, identificador: str) -> bool:
        """True si el identificador cumple su algoritmo de verificacion."""

    @abstractmethod
    def divisiones_territoriales(self) -> tuple[str, ...]:
        """Comunas, distritos o equivalente."""

    @abstractmethod
    def generar_razon_social(self, azar: Random) -> str:
        """Razon social sintetica y pronunciable. Nunca una empresa real."""
