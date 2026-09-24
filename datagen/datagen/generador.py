"""
Generador de datos tributarios sinteticos del universo DGT.

Estrategia general
------------------
1. Se arma un PLAN completo antes de generar una sola fila: cuantos DTEs por
   periodo, cuantos de cada tipo, y cuantas trampas van en cada periodo. Con el
   plan cerrado, los conteos de trampas son EXACTOS y el manifiesto puede
   afirmar numeros redondos en vez de "aproximadamente".
2. Cada periodo se genera en dos pasadas: primero los documentos base
   (facturas, boletas, guias) y despues las notas, que necesitan referenciar un
   documento que ya exista. Asi ninguna nota queda apuntando al vacio (CA-6).
3. Las filas se barajan dentro del periodo antes de escribir, para que el
   archivo no quede ordenado por tipo de documento.

Determinismo: todo el azar sale de generadores sembrados desde --semilla. No se
consulta el reloj en ningun punto.
"""

from __future__ import annotations

import datetime as dt
from collections import defaultdict
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path
from random import Random

from . import modelo
from .modelo import INDICE_DTE as IDX
from .escalas import (
    PERIODO_RECEPCION,
    ANIOS_BODEGA,
    FILAS_POR_ANIO_BODEGA,
    PERIODOS_HISTORICO,
    PERIODOS_RECIENTE,
    Escala,
)
from .escritura import construir_tabla, escribir_tabla, limpiar_directorio
from .perfiles import PerfilPais
from .trampas import TRAMPAS_POR_ID

CENTAVOS = Decimal("0.01")

# Mezcla de tipos de documento. Suma 1.0.
MEZCLA_TIPOS: dict[int, float] = {
    33: 0.42,  # factura afecta
    39: 0.38,  # boleta
    34: 0.07,  # factura exenta
    52: 0.06,  # guia de despacho
    61: 0.05,  # nota de credito
    56: 0.02,  # nota de debito
}

# Peso de emision por segmento: una GRANDE emite ordenes de magnitud mas que una
# MICRO. Determina que contribuyente aparece como emisor.
PESO_EMISION = {"MICRO": 1.0, "PEQUENA": 4.0, "MEDIANA": 15.0, "GRANDE": 60.0}

# Reparto de la poblacion de contribuyentes.
REPARTO_SEGMENTOS = {"MICRO": 0.60, "PEQUENA": 0.25, "MEDIANA": 0.12, "GRANDE": 0.03}

# Rango de monto neto (en pesos) por segmento.
RANGO_MONTO = {
    "MICRO": (5_000, 500_000),
    "PEQUENA": (20_000, 2_000_000),
    "MEDIANA": (100_000, 10_000_000),
    "GRANDE": (500_000, 80_000_000),
}

_CALIDADES = (
    "linea estandar", "linea premium", "formato industrial", "uso general",
    "grado tecnico", "presentacion mayorista", "serie economica", "alta rotacion",
)

_ARTICULOS = (
    "materiales de construccion", "insumos de oficina", "repuestos automotrices",
    "productos alimenticios", "equipos de computacion", "articulos de ferreteria",
    "servicios de mantencion", "fletes y acarreos", "asesoria profesional",
    "arriendo de maquinaria", "insumos agricolas", "productos textiles",
)


def _reparto_entero(total: int, proporciones: dict) -> dict:
    """
    Reparte 'total' unidades segun proporciones, con restos mayores.

    Se usa para que los conteos por tipo de documento sumen EXACTAMENTE el total
    del periodo, sin perder ni inventar filas por redondeo.
    """
    crudo = {clave: total * peso for clave, peso in proporciones.items()}
    asignado = {clave: int(valor) for clave, valor in crudo.items()}
    faltan = total - sum(asignado.values())
    if faltan:
        restos = sorted(
            crudo, key=lambda c: (crudo[c] - asignado[c], c), reverse=True
        )
        for clave in restos[:faltan]:
            asignado[clave] += 1
    return asignado


def _reparto_lista(total: int, pesos: list[int]) -> list[int]:
    """Reparte 'total' entre posiciones proporcionalmente a 'pesos'."""
    suma = sum(pesos)
    if suma == 0:
        return [0] * len(pesos)
    crudo = [total * peso / suma for peso in pesos]
    asignado = [int(valor) for valor in crudo]
    faltan = total - sum(asignado)
    orden = sorted(
        range(len(pesos)), key=lambda i: (crudo[i] - asignado[i], i), reverse=True
    )
    for i in orden[:faltan]:
        asignado[i] += 1
    return asignado


def _dias_del_periodo(periodo: str) -> int:
    anio, mes = (int(p) for p in periodo.split("-"))
    if mes == 12:
        siguiente = dt.date(anio + 1, 1, 1)
    else:
        siguiente = dt.date(anio, mes + 1, 1)
    return (siguiente - dt.date(anio, mes, 1)).days


def _monto(pesos: int) -> Decimal:
    return Decimal(pesos).quantize(CENTAVOS)


def calcular_montos(
    neto_pesos: int, afecto: bool, tasa: Decimal, signo: int
) -> tuple[Decimal, Decimal, Decimal, Decimal]:
    """
    Devuelve (neto, exento, iva, total) ya con signo aplicado.

    En documentos afectos el IVA es round(neto * tasa) y el total es la suma.
    La nota de credito lleva los montos en negativo: resta en la contabilidad,
    y por eso un monto negativo en una NC NO es una corrupcion (ver T-5).
    """
    if afecto:
        neto = _monto(neto_pesos)
        exento = _monto(0)
        iva = (neto * tasa).quantize(CENTAVOS, rounding=ROUND_HALF_UP)
        total = neto + iva
    else:
        neto = _monto(0)
        exento = _monto(neto_pesos)
        iva = _monto(0)
        total = exento
    if signo < 0:
        return -neto, -exento, -iva, -total
    return neto, exento, iva, total


class Generador:
    def __init__(
        self,
        perfil: PerfilPais,
        escala: Escala,
        semilla: int,
        salida: Path,
    ) -> None:
        self.perfil = perfil
        self.escala = escala
        self.semilla = semilla
        self.salida = salida
        self.tasa = perfil.tasa_impuesto

        # Un generador de azar por dominio: agregar un dataset nuevo no corre
        # la secuencia de los demas y por lo tanto no cambia sus bytes.
        self.azar_contribuyentes = Random(semilla + 101)
        self.azar_dte = Random(semilla + 202)
        self.azar_f29 = Random(semilla + 303)
        self.azar_recepcion = Random(semilla + 404)
        # La bodega del laboratorio 17 es un dataset opcional y aparte. Tiene su
        # propio flujo por la misma razon que los de arriba: pedirla no corre la
        # secuencia de ninguno de los otros, asi que no cambia ni un byte de lo
        # que ya genera el curso.
        self.azar_bodega = Random(semilla + 505)

        self.contribuyentes: list[dict] = []
        self.folios: dict[tuple[str, int], int] = defaultdict(int)
        # Facturas ya emitidas, disponibles como blanco de una nota de credito.
        self.reservorio: list[tuple] = []

        self.evidencia: dict[str, dict] = {}
        self.conteos: dict[str, dict] = {}

    # --- contribuyentes ----------------------------------------------------
    def generar_contribuyentes(self) -> None:
        azar = self.azar_contribuyentes
        total = self.escala.contribuyentes
        por_segmento = _reparto_entero(total, REPARTO_SEGMENTOS)

        comunas = self.perfil.divisiones_territoriales()
        ruts_vistos: set[str] = set()
        registros: list[dict] = []

        for segmento in modelo.SEGMENTOS:
            for _ in range(por_segmento[segmento]):
                rut = self.perfil.generar_identificador(azar)
                while rut in ruts_vistos:
                    rut = self.perfil.generar_identificador(azar)
                ruts_vistos.add(rut)
                registros.append(
                    {
                        "rut": rut,
                        "razon_social": self.perfil.generar_razon_social(azar),
                        "segmento": segmento,
                        "comuna": azar.choice(comunas),
                        "giro": azar.choice(modelo.GIROS),
                        "fecha_inicio_actividades": dt.date(2024, 1, 1)
                        - dt.timedelta(days=azar.randint(200, 7000)),
                        "activo": azar.random() > 0.03,
                    }
                )

        azar.shuffle(registros)
        self.contribuyentes = registros

        # Distribucion acumulada para elegir emisor segun peso de segmento.
        self._pesos_emision = [PESO_EMISION[c["segmento"]] for c in registros]
        self._indices = list(range(len(registros)))
        acumulado, suma = [], 0.0
        for peso in self._pesos_emision:
            suma += peso
            acumulado.append(suma)
        self._acumulado_emision = acumulado

        columnas = {
            campo: [reg[campo] for reg in registros]
            for campo in modelo.ESQUEMA_CONTRIBUYENTES.names
        }
        tabla = construir_tabla(columnas, modelo.ESQUEMA_CONTRIBUYENTES)
        destino = self.salida / "contribuyentes" / "contribuyentes.parquet"
        escribir_tabla(tabla, destino)
        self.conteos["contribuyentes"] = {"filas": len(registros), "archivos": 1}

    # --- utilidades de fila -------------------------------------------------
    def _elegir_emisores(self, azar: Random, cantidad: int) -> list[int]:
        return azar.choices(
            self._indices, cum_weights=self._acumulado_emision, k=cantidad
        )

    def _glosa(self, azar: Random, folio: int) -> str:
        return (
            f"{azar.choice(_ARTICULOS)} - {azar.randint(1, 400)} unidades - "
            f"OC {azar.randint(100000, 999999)} - despacho {folio}"
        )

    def _observaciones(self, azar: Random) -> str:
        return (
            f"Recepcion conforme en anden {azar.randint(1, 24)}. "
            f"Guia interna {azar.randint(100000, 999999)}. "
            f"Bulto {azar.randint(1, 40)} de {azar.randint(40, 90)}. "
            f"Contacto {azar.choice(modelo.CONTACTOS)} anexo {azar.randint(200, 899)}."
        )

    def _detalle(self, azar: Random) -> str:
        lineas = []
        for _ in range(azar.randint(3, 18)):
            lineas.append(
                f"{azar.randint(100000, 999999)}|"
                f"{azar.choice(_ARTICULOS)} {azar.choice(_CALIDADES)}|"
                f"{azar.randint(1, 250)}|"
                f"{azar.randint(500, 900000)}"
            )
        return ";".join(lineas)

    def _fechas(
        self, azar: Random, periodo: str, dias: int, tardio: bool
    ) -> tuple[dt.date, dt.datetime]:
        anio, mes = (int(p) for p in periodo.split("-"))
        emision = dt.date(anio, mes, azar.randint(1, dias))
        if tardio:
            # T-1: la recepcion llega hasta 45 dias despues de la emision.
            atraso = azar.randint(5, 45)
        else:
            atraso = azar.randint(0, 2)
        recepcion = dt.datetime.combine(
            emision + dt.timedelta(days=atraso),
            dt.time(azar.randint(0, 23), azar.randint(0, 59), azar.randint(0, 59)),
        )
        return emision, recepcion

    def _fila_base(
        self,
        azar: Random,
        periodo: str,
        dias: int,
        tipo: int,
        tardio: bool,
        con_v2: bool,
    ) -> tuple:
        indice = self._elegir_emisores(azar, 1)[0]
        emisor = self.contribuyentes[indice]
        receptor = self.contribuyentes[azar.randrange(len(self.contribuyentes))]
        if receptor["rut"] == emisor["rut"]:
            receptor = self.contribuyentes[
                (indice + 1) % len(self.contribuyentes)
            ]

        documento = self.perfil.tipos_documento[tipo]
        clave = (emisor["rut"], tipo)
        self.folios[clave] += 1
        folio = self.folios[clave]

        minimo, maximo = RANGO_MONTO[emisor["segmento"]]
        if tipo == 39:  # las boletas son chicas por naturaleza
            minimo, maximo = 1_000, 120_000
        neto = azar.randint(minimo, maximo)
        montos = calcular_montos(neto, documento.afecto, self.tasa, 1)
        emision, recepcion = self._fechas(azar, periodo, dias, tardio)

        fila = [
            emisor["rut"],
            emisor["razon_social"],
            receptor["rut"],
            receptor["razon_social"],
            receptor["comuna"],
            tipo,
            folio,
            emision,
            recepcion,
            emisor["comuna"],
            self._glosa(azar, folio),
            azar.choice(modelo.FORMAS_PAGO),
            f"VEN-{azar.randint(1, 9999):04d}",
            f"OC-{azar.randint(10_000_000, 99_999_999)}",
            self._observaciones(azar),
            self._detalle(azar),
            montos[0],
            montos[1],
            montos[2],
            montos[3],
            None,
            None,
            None,
            azar.choices(modelo.ESTADOS_SII, cum_weights=[0.94, 0.99, 1.0], k=1)[0],
        ]
        if con_v2:
            fila.extend(self._campos_v2(azar))
        return tuple(fila)

    def _campos_v2(self, azar: Random) -> list:
        return [
            azar.choice(modelo.CANALES_EMISION),
            f"SUC-{azar.randint(1, 60):03d}",
        ]

    def _fila_nota(
        self,
        azar: Random,
        periodo: str,
        dias: int,
        tipo: int,
        referencia: tuple,
        tardio: bool,
        con_v2: bool,
        anular_total: bool,
    ) -> tuple:
        """Nota (56/61) que referencia un documento ya emitido."""
        ref_rut, ref_tipo, ref_folio, _ref_fecha, ref_total = referencia
        emisor = self._por_rut[ref_rut]

        clave = (emisor["rut"], tipo)
        self.folios[clave] += 1
        folio = self.folios[clave]

        documento = self.perfil.tipos_documento[tipo]
        # La NC anula el total de la factura o una parte de ella.
        base = abs(int(ref_total))
        if not anular_total:
            base = max(1_000, int(base * azar.uniform(0.15, 0.75)))
        neto = max(1_000, int(base / (1 + float(self.tasa))))
        montos = calcular_montos(neto, documento.afecto, self.tasa, documento.signo)
        emision, recepcion = self._fechas(azar, periodo, dias, tardio)

        fila = [
            emisor["rut"],
            emisor["razon_social"],
            emisor["rut"],
            emisor["razon_social"],
            emisor["comuna"],
            tipo,
            folio,
            emision,
            recepcion,
            emisor["comuna"],
            f"anula documento {ref_tipo} folio {ref_folio}",
            azar.choice(modelo.FORMAS_PAGO),
            f"VEN-{azar.randint(1, 9999):04d}",
            f"OC-{azar.randint(10_000_000, 99_999_999)}",
            self._observaciones(azar),
            self._detalle(azar),
            montos[0],
            montos[1],
            montos[2],
            montos[3],
            ref_tipo,
            ref_folio,
            ref_rut,
            "ACEPTADO",
        ]
        if con_v2:
            fila.extend(self._campos_v2(azar))
        return tuple(fila)

    # --- DTE ----------------------------------------------------------------
    def _plan_dte(self, periodos: tuple[str, ...], total: int) -> list[dict]:
        """
        Reparte el total de DTEs entre periodos y tipos, y decide de antemano
        cuantas trampas T-1 y T-4 lleva cada periodo.
        """
        # Peso creciente: la DGT recibe mas documentos con el paso del tiempo.
        pesos = [100 + i * 3 for i in range(len(periodos))]
        por_periodo = _reparto_lista(total, pesos)

        plan = []
        for periodo, cantidad in zip(periodos, por_periodo):
            tipos = _reparto_entero(cantidad, MEZCLA_TIPOS)
            plan.append(
                {
                    "periodo": periodo,
                    "total": cantidad,
                    "tipos": tipos,
                    "tardios": round(cantidad * TRAMPAS_POR_ID["T-1"].tasa_objetivo),
                    "t4": 0,
                }
            )
        return plan

    def _asignar_t4(self, plan: list[dict], facturas_totales: int) -> int:
        """
        Reparte las notas de credito sobre periodos cerrados (T-4).

        Solo pueden ir en periodos que tengan al menos un periodo anterior: no se
        puede anular el pasado en el primer mes del universo.
        """
        objetivo = round(facturas_totales * TRAMPAS_POR_ID["T-4"].tasa_objetivo)
        elegibles = plan[1:]
        disponibles = [p["tipos"][self.perfil.codigo_nota_credito] for p in elegibles]
        objetivo = min(objetivo, sum(disponibles))
        reparto = _reparto_lista(objetivo, disponibles)
        for periodo_plan, cantidad in zip(elegibles, reparto):
            periodo_plan["t4"] = min(cantidad, periodo_plan["tipos"][self.perfil.codigo_nota_credito])
        return sum(p["t4"] for p in plan)

    def _generar_lote(
        self,
        nombre_lote: str,
        periodos: tuple[str, ...],
        total: int,
        con_v2: bool,
        azar: Random,
    ) -> dict:
        plan = self._plan_dte(periodos, total)
        facturas_totales = sum(
            sum(p["tipos"][codigo] for codigo in self.perfil.codigos_factura)
            for p in plan
        )
        t4_planificadas = self._asignar_t4(plan, facturas_totales)

        esquema = modelo.ESQUEMA_DTE_V2 if con_v2 else modelo.ESQUEMA_DTE_V1
        columnas_nombre = list(esquema.names)
        raiz = self.salida / "dte" / nombre_lote

        filas_escritas = 0
        archivos = 0
        tardios_reales = 0
        t4_reales = 0
        pares_t4: list[list] = []
        suma_total = Decimal(0)

        for periodo_plan in plan:
            periodo = periodo_plan["periodo"]
            dias = _dias_del_periodo(periodo)
            tipos = periodo_plan["tipos"]
            codigo_nc = self.perfil.codigo_nota_credito
            codigo_nd = self.perfil.codigo_nota_debito

            # Que filas del periodo llegan tarde (T-1).
            cantidad = periodo_plan["total"]
            indices_tardios = set(
                azar.sample(range(cantidad), periodo_plan["tardios"])
            ) if periodo_plan["tardios"] else set()
            contador = 0

            filas: list[tuple] = []
            facturas_periodo: list[tuple] = []

            # Pasada 1: documentos base (todo lo que no es nota).
            for tipo in (33, 34, 39, 52):
                for _ in range(tipos[tipo]):
                    tardio = contador in indices_tardios
                    contador += 1
                    fila = self._fila_base(azar, periodo, dias, tipo, tardio, con_v2)
                    filas.append(fila)
                    if tardio:
                        tardios_reales += 1
                    if tipo in self.perfil.codigos_factura:
                        # (rut, tipo, folio, fecha, total) para referenciar luego
                        facturas_periodo.append(
                            (fila[IDX["rut_emisor"]], fila[IDX["tipo_dte"]], fila[IDX["folio"]], fila[IDX["fecha_emision"]], fila[IDX["monto_total"]])
                        )

            # Pasada 2: notas. Necesitan un documento previo que exista.
            pendientes_t4 = periodo_plan["t4"]
            for tipo in (codigo_nc, codigo_nd):
                for _ in range(tipos[tipo]):
                    tardio = contador in indices_tardios
                    contador += 1
                    usar_t4 = (
                        tipo == codigo_nc and pendientes_t4 > 0 and bool(self.reservorio)
                    )
                    if usar_t4:
                        referencia = self.reservorio[
                            azar.randrange(len(self.reservorio))
                        ]
                        pendientes_t4 -= 1
                    elif facturas_periodo:
                        referencia = facturas_periodo[
                            azar.randrange(len(facturas_periodo))
                        ]
                    elif self.reservorio:
                        referencia = self.reservorio[
                            azar.randrange(len(self.reservorio))
                        ]
                    else:
                        continue  # sin documentos previos no se emite la nota

                    anular_total = azar.random() < 0.55
                    fila = self._fila_nota(
                        azar, periodo, dias, tipo, referencia, tardio, con_v2,
                        anular_total,
                    )
                    filas.append(fila)
                    if tardio:
                        tardios_reales += 1
                    if usar_t4:
                        t4_reales += 1
                        pares_t4.append(
                            [
                                fila[IDX["rut_emisor"]], int(fila[IDX["tipo_dte"]]), int(fila[IDX["folio"]]),  # NC
                                referencia[0], int(referencia[1]), int(referencia[2]),
                                referencia[3].strftime("%Y-%m"), periodo,
                                "total" if anular_total else "parcial",
                            ]
                        )

            # El archivo no debe quedar ordenado por tipo de documento.
            azar.shuffle(filas)

            columnas = {nombre: lista for nombre, lista in zip(columnas_nombre, zip(*filas))}
            columnas = {k: list(v) for k, v in columnas.items()}
            tabla = construir_tabla(columnas, esquema)
            escribir_tabla(tabla, raiz / f"anio_mes={periodo}" / "parte-00000.parquet")
            filas_escritas += tabla.num_rows
            archivos += 1
            suma_total += sum(columnas["monto_total"], Decimal(0))

            # Alimenta el reservorio para las NC de periodos siguientes.
            self.reservorio.extend(facturas_periodo)
            if len(self.reservorio) > self.escala.tope_reservorio:
                self.reservorio = azar.sample(
                    self.reservorio, self.escala.tope_reservorio
                )

        return {
            "filas": filas_escritas,
            "archivos": archivos,
            "tardios": tardios_reales,
            "t4": t4_reales,
            "pares_t4": pares_t4,
            "facturas": facturas_totales,
            "t4_planificadas": t4_planificadas,
            "suma_monto_total": str(suma_total),
        }

    def generar_dtes(self) -> None:
        self._por_rut = {c["rut"]: c for c in self.contribuyentes}
        limpiar_directorio(self.salida / "dte")

        historico = self._generar_lote(
            "lote_historico", PERIODOS_HISTORICO, self.escala.dtes_historico,
            con_v2=False, azar=self.azar_dte,
        )
        reciente = self._generar_lote(
            "lote_reciente", PERIODOS_RECIENTE, self.escala.dtes_reciente,
            con_v2=True, azar=self.azar_dte,
        )
        self.conteos["dte_lote_historico"] = historico
        self.conteos["dte_lote_reciente"] = reciente

    # --- F29 ----------------------------------------------------------------
    def generar_f29(self) -> None:
        """
        Declaraciones mensuales con cadenas de rectificatorias (T-3).

        La llave natural es (rut, periodo); el correlativo ordena las versiones y
        la vigente es la de mayor correlativo. Los correlativos de una cadena son
        consecutivos desde 1 (CA-6): una cadena con huecos seria un dato
        imposible en la vida real y arruinaria el ejercicio de upsert del M4.
        """
        azar = self.azar_f29
        periodos = PERIODOS_HISTORICO + PERIODOS_RECIENTE
        declarantes = max(1, int(len(self.contribuyentes) * self.escala.cobertura_f29))

        filas: list[tuple] = []
        cadenas: list[list] = []
        total_llaves = 0

        for periodo in periodos:
            muestra = azar.sample(self.contribuyentes, declarantes)
            objetivo_rect = round(declarantes * TRAMPAS_POR_ID["T-3"].tasa_objetivo)
            indices_rect = set(azar.sample(range(declarantes), objetivo_rect))

            anio, mes = (int(p) for p in periodo.split("-"))
            # El F29 se presenta al mes siguiente del periodo declarado.
            base_pago = dt.date(anio + (1 if mes == 12 else 0), 1 if mes == 12 else mes + 1, 1)

            for posicion, contribuyente in enumerate(muestra):
                total_llaves += 1
                versiones = azar.randint(2, 4) if posicion in indices_rect else 1
                minimo, maximo = RANGO_MONTO[contribuyente["segmento"]]
                ventas = azar.randint(minimo, maximo)
                compras = int(ventas * azar.uniform(0.35, 0.92))

                for correlativo in range(1, versiones + 1):
                    # Cada rectificatoria corrige los montos de la anterior.
                    factor = 1.0 if correlativo == 1 else azar.uniform(0.85, 1.18)
                    ventas_v = int(ventas * factor)
                    compras_v = int(compras * factor)
                    exentas_v = int(ventas_v * azar.uniform(0.0, 0.12))
                    afecto_v = max(0, ventas_v - exentas_v)
                    debito = (Decimal(afecto_v) * self.tasa).quantize(
                        CENTAVOS, rounding=ROUND_HALF_UP
                    )
                    credito = (Decimal(compras_v) * self.tasa).quantize(
                        CENTAVOS, rounding=ROUND_HALF_UP
                    )
                    filas.append(
                        (
                            contribuyente["rut"],
                            periodo,
                            correlativo,
                            base_pago + dt.timedelta(days=azar.randint(0, 45) + (correlativo - 1) * azar.randint(20, 120)),
                            _monto(afecto_v),
                            _monto(exentas_v),
                            _monto(compras_v),
                            debito,
                            credito,
                            debito - credito,
                            "ORIGINAL" if correlativo == 1 else "RECTIFICATORIA",
                        )
                    )

                if versiones > 1:
                    cadenas.append([contribuyente["rut"], periodo, versiones])

        azar.shuffle(filas)
        columnas = {
            nombre: list(valores)
            for nombre, valores in zip(modelo.ESQUEMA_F29.names, zip(*filas))
        }
        tabla = construir_tabla(columnas, modelo.ESQUEMA_F29)
        destino = self.salida / "f29" / "f29.parquet"
        limpiar_directorio(self.salida / "f29")
        escribir_tabla(tabla, destino)

        self.conteos["f29"] = {
            "filas": len(filas),
            "archivos": 1,
            "llaves_naturales": total_llaves,
            "cadenas_rectificatorias": len(cadenas),
            "suma_impuesto_determinado": str(
                sum(columnas["impuesto_determinado"], Decimal(0))
            ),
        }
        self.evidencia["T-3"] = {
            "conteo": len(cadenas),
            "sobre_total": total_llaves,
            "tasa_real": round(len(cadenas) / total_llaves, 6) if total_llaves else 0.0,
            "cadenas": cadenas,
        }

    # --- recepcion diaria ---------------------------------------------------
    def generar_recepcion(self) -> None:
        """
        El lote que ingieren los labs M4 y M6.

        Aqui viven las tres trampas mas duras juntas: folios duplicados (T-2),
        montos corruptos (T-5) y cientos de archivos chicos (T-7).
        """
        azar = self.azar_recepcion
        periodo = PERIODO_RECEPCION
        dias = _dias_del_periodo(periodo)
        total = self.escala.dtes_recepcion
        tipos = _reparto_entero(total, MEZCLA_TIPOS)
        esquema = modelo.ESQUEMA_DTE_V2
        codigo_nc = self.perfil.codigo_nota_credito
        codigo_nd = self.perfil.codigo_nota_debito

        tardios = round(total * TRAMPAS_POR_ID["T-1"].tasa_objetivo)
        indices_tardios = set(azar.sample(range(total), tardios)) if tardios else set()
        contador = 0

        filas: list[list] = []
        facturas_periodo: list[tuple] = []
        facturas_lote = sum(tipos[c] for c in self.perfil.codigos_factura)
        # T-4 tambien vive aqui: 2% de las facturas del lote, todas anulando
        # documentos de periodos ya cerrados (todo lo anterior a 2026-06).
        pendientes_t4 = round(facturas_lote * TRAMPAS_POR_ID["T-4"].tasa_objetivo)
        pares_t4: list[list] = []
        tardios_reales = 0

        for tipo in (33, 34, 39, 52):
            for _ in range(tipos[tipo]):
                tardio = contador in indices_tardios
                contador += 1
                fila = list(self._fila_base(azar, periodo, dias, tipo, tardio, True))
                filas.append(fila)
                if tardio:
                    tardios_reales += 1
                if tipo in self.perfil.codigos_factura:
                    facturas_periodo.append((fila[IDX["rut_emisor"]], fila[IDX["tipo_dte"]], fila[IDX["folio"]], fila[IDX["fecha_emision"]], fila[IDX["monto_total"]]))

        for tipo in (codigo_nc, codigo_nd):
            for _ in range(tipos[tipo]):
                tardio = contador in indices_tardios
                contador += 1
                usar_t4 = tipo == codigo_nc and pendientes_t4 > 0 and bool(self.reservorio)
                if usar_t4:
                    referencia = self.reservorio[azar.randrange(len(self.reservorio))]
                    pendientes_t4 -= 1
                elif facturas_periodo:
                    referencia = facturas_periodo[azar.randrange(len(facturas_periodo))]
                elif self.reservorio:
                    referencia = self.reservorio[azar.randrange(len(self.reservorio))]
                else:
                    continue
                anular_total = azar.random() < 0.55
                fila = list(
                    self._fila_nota(
                        azar, periodo, dias, tipo, referencia, tardio, True, anular_total
                    )
                )
                filas.append(fila)
                if tardio:
                    tardios_reales += 1
                if usar_t4:
                    pares_t4.append(
                        [
                            fila[IDX["rut_emisor"]], int(fila[IDX["tipo_dte"]]), int(fila[IDX["folio"]]),
                            referencia[0], int(referencia[1]), int(referencia[2]),
                            referencia[3].strftime("%Y-%m"), periodo,
                            "total" if anular_total else "parcial",
                        ]
                    )

        azar.shuffle(filas)
        base = len(filas)

        # --- T-5: montos corruptos ---
        objetivo_corruptos = round(base * TRAMPAS_POR_ID["T-5"].tasa_objetivo)
        indices_corruptos = azar.sample(range(base), objetivo_corruptos)
        corruptos: list[list] = []
        for indice in sorted(indices_corruptos):
            fila = filas[indice]
            motivo = azar.choice(
                ["iva_inconsistente", "total_inconsistente", "monto_negativo"]
            )
            if motivo == "monto_negativo" and int(fila[IDX["tipo_dte"]]) == codigo_nc:
                # Un monto negativo en una NC es legitimo: no serviria de trampa.
                motivo = "iva_inconsistente"
            desvio = Decimal(azar.randint(1_000, 900_000))
            if motivo == "iva_inconsistente":
                fila[IDX["monto_iva"]] = fila[IDX["monto_iva"]] + desvio
            elif motivo == "total_inconsistente":
                fila[IDX["monto_total"]] = fila[IDX["monto_total"]] + desvio
            else:
                fila[IDX["monto_neto"]] = -abs(fila[IDX["monto_neto"]])
                fila[IDX["monto_total"]] = -abs(fila[IDX["monto_total"]])
            corruptos.append([fila[IDX["rut_emisor"]], int(fila[IDX["tipo_dte"]]), int(fila[IDX["folio"]]), motivo])

        # --- T-2: folios duplicados ---
        objetivo_duplicados = round(base * TRAMPAS_POR_ID["T-2"].tasa_objetivo)
        candidatos = [i for i in range(base) if i not in set(indices_corruptos)]
        indices_duplicados = azar.sample(candidatos, min(objetivo_duplicados, len(candidatos)))
        duplicados: list[list] = []
        for indice in indices_duplicados:
            copia = list(filas[indice])
            # El reenvio llega mas tarde y a veces con la glosa retocada.
            copia[IDX["fecha_recepcion"]] = copia[IDX["fecha_recepcion"]] + dt.timedelta(minutes=azar.randint(5, 2880))
            if azar.random() < 0.5:
                copia[IDX["glosa"]] = copia[IDX["glosa"]] + " (reenvio)"
            copia[IDX["estado_sii"]] = "ACEPTADO"
            filas.append(copia)
            duplicados.append([copia[IDX["rut_emisor"]], int(copia[IDX["tipo_dte"]]), int(copia[IDX["folio"]])])

        azar.shuffle(filas)

        # Recuento de tardios SOBRE LAS FILAS FINALES, no sobre las planificadas.
        # Interaccion real entre trampas: T-2 duplica filas, y si la fila copiada
        # era tardia (T-1) su copia tambien lo es. El manifiesto tiene que
        # describir los datos que quedaron escritos, no la intencion original.
        tardios_reales = sum(
            1 for fila in filas if (fila[IDX["fecha_recepcion"]].date() - fila[IDX["fecha_emision"]]).days >= 5
        )

        # --- T-7: fragmentar en muchos archivos chicos ---
        raiz = self.salida / "recepcion_diaria"
        limpiar_directorio(raiz)
        cantidad_archivos = self.escala.archivos_recepcion
        tamano = max(1, -(-len(filas) // cantidad_archivos))  # techo
        archivos = 0
        suma_total = Decimal(0)
        for numero, inicio in enumerate(range(0, len(filas), tamano)):
            trozo = filas[inicio : inicio + tamano]
            columnas = {
                nombre: list(valores)
                for nombre, valores in zip(esquema.names, zip(*trozo))
            }
            tabla = construir_tabla(columnas, esquema)
            escribir_tabla(tabla, raiz / f"anio_mes={periodo}" / f"parte-{numero:05d}.parquet")
            suma_total += sum(columnas["monto_total"], Decimal(0))
            archivos += 1

        self.conteos["recepcion_diaria"] = {
            "filas": len(filas),
            "filas_base": base,
            "archivos": archivos,
            "suma_monto_total": str(suma_total),
        }
        self.evidencia["T-2"] = {
            "conteo": len(duplicados),
            "sobre_total": base,
            "tasa_real": round(len(duplicados) / base, 6) if base else 0.0,
            "folios": duplicados,
        }
        self.evidencia["T-5"] = {
            "conteo": len(corruptos),
            "sobre_total": base,
            "tasa_real": round(len(corruptos) / base, 6) if base else 0.0,
            "tolerancia_pesos": 2,
            "filas": corruptos,
        }
        self._t4_recepcion = pares_t4
        self._tardios_recepcion = tardios_reales
        self._facturas_recepcion = facturas_lote

    # --- orquestacion -------------------------------------------------------
    def ejecutar(self) -> dict:
        self.salida.mkdir(parents=True, exist_ok=True)
        limpiar_directorio(self.salida / "contribuyentes")
        self.generar_contribuyentes()
        self.generar_dtes()
        self.generar_f29()
        self.generar_recepcion()
        return self.armar_manifiesto()

    def ejecutar_bodega(self) -> dict:
        """
        Genera SOLO la bodega de diez anios del laboratorio 17.

        No es el universo del curso y no pretende serlo: no escribe
        manifiesto.json, no genera F29 ni recepcion diaria, y no toca el lote
        historico. Se escribe en la carpeta que reciba por --salida, que tiene
        que ser distinta de la del curso.

        Un millon de filas por anio, de 2015 a 2024, con el mismo esquema v1 de
        siempre. Se llama a _generar_lote una vez por anio, y no una sola vez
        con los ciento veinte periodos, porque _plan_dte reparte el total con
        peso creciente: en una sola llamada 2024 se llevaria varias veces mas
        filas que 2015, y el laboratorio compara anios entre si.

        El padron sale del flujo de siempre, con la misma semilla, asi que los
        RUT de la bodega son los mismos contribuyentes del universo DGT. Las
        filas de DTE salen de azar_bodega, que no existe para ninguna otra
        corrida.
        """
        if (self.salida / "manifiesto.json").exists():
            raise ValueError(
                f"{self.salida} tiene un manifiesto.json: es la carpeta del "
                "universo del curso. La bodega se escribe aparte, con "
                "--salida datos-bodega/, para no tocar esos datos."
            )

        self.salida.mkdir(parents=True, exist_ok=True)
        limpiar_directorio(self.salida / "contribuyentes")
        self.generar_contribuyentes()
        self._por_rut = {c["rut"]: c for c in self.contribuyentes}

        # Solo el lote de la bodega, nunca self.salida / "dte" entero.
        limpiar_directorio(self.salida / "dte" / "bodega")

        anios = []
        filas = archivos = 0
        suma = Decimal(0)
        for anio in ANIOS_BODEGA:
            periodos = tuple(f"{anio}-{mes:02d}" for mes in range(1, 13))
            conteo = self._generar_lote(
                "bodega", periodos, FILAS_POR_ANIO_BODEGA,
                con_v2=False, azar=self.azar_bodega,
            )
            filas += conteo["filas"]
            archivos += conteo["archivos"]
            suma += Decimal(conteo["suma_monto_total"])
            anios.append({"anio": anio, "filas": conteo["filas"],
                          "archivos": conteo["archivos"],
                          "suma_monto_total": conteo["suma_monto_total"]})

        return {
            "semilla": self.semilla,
            "escala": self.escala.nombre,
            "anios": anios,
            "filas": filas,
            "archivos": archivos,
            "suma_monto_total": str(suma),
            "columnas": list(modelo.ESQUEMA_DTE_V1.names),
        }

    def armar_manifiesto(self) -> dict:
        historico = self.conteos["dte_lote_historico"]
        reciente = self.conteos["dte_lote_reciente"]
        recepcion = self.conteos["recepcion_diaria"]

        dtes_totales = historico["filas"] + reciente["filas"] + recepcion["filas"]
        facturas_totales = (
            historico["facturas"] + reciente["facturas"] + self._facturas_recepcion
        )
        tardios = historico["tardios"] + reciente["tardios"] + self._tardios_recepcion
        pares_t4 = historico["pares_t4"] + reciente["pares_t4"] + self._t4_recepcion

        self.evidencia["T-1"] = {
            "conteo": tardios,
            "sobre_total": dtes_totales,
            "tasa_real": round(tardios / dtes_totales, 6) if dtes_totales else 0.0,
            "dias_maximos": 45,
        }
        self.evidencia["T-4"] = {
            "conteo": len(pares_t4),
            "sobre_total": facturas_totales,
            "tasa_real": round(len(pares_t4) / facturas_totales, 6) if facturas_totales else 0.0,
            # [rut_nc, tipo_nc, folio_nc, rut_ref, tipo_ref, folio_ref,
            #  periodo_ref, periodo_nc, alcance]
            "pares": pares_t4,
        }
        self.evidencia["T-6"] = {
            "columnas_v1": list(modelo.COLUMNAS_DTE_V1),
            "columnas_v2": list(modelo.COLUMNAS_DTE_V2),
            "columnas_agregadas": [
                c for c in modelo.COLUMNAS_DTE_V2 if c not in modelo.COLUMNAS_DTE_V1
            ],
            "lote_v1": "dte/lote_historico",
            "lotes_v2": ["dte/lote_reciente", "recepcion_diaria"],
        }
        self.evidencia["T-7"] = {
            "archivos": recepcion["archivos"],
            "filas": recepcion["filas"],
            "filas_por_archivo_promedio": round(
                recepcion["filas"] / recepcion["archivos"], 2
            )
            if recepcion["archivos"]
            else 0,
            "ruta": "recepcion_diaria",
        }

        suma_dte = (
            Decimal(historico["suma_monto_total"])
            + Decimal(reciente["suma_monto_total"])
            + Decimal(recepcion["suma_monto_total"])
        )

        trampas = {}
        for identificador, trampa in TRAMPAS_POR_ID.items():
            registro = dict(self.evidencia.get(identificador, {}))
            registro["nombre"] = trampa.nombre
            registro["descripcion"] = trampa.descripcion
            registro["tasa_objetivo"] = trampa.tasa_objetivo
            registro["sobre"] = trampa.sobre
            registro["alimenta"] = trampa.alimenta
            trampas[identificador] = registro

        return {
            "semilla": self.semilla,
            "escala": self.escala.nombre,
            "pais": self.perfil.nombre,
            "moneda": self.perfil.moneda,
            "tasa_impuesto": str(self.perfil.tasa_impuesto),
            "periodos": {
                "lote_historico": list(PERIODOS_HISTORICO),
                "lote_reciente": list(PERIODOS_RECIENTE),
                "recepcion_diaria": [PERIODO_RECEPCION],
            },
            "datasets": {
                "contribuyentes": self.conteos["contribuyentes"],
                "dte_lote_historico": {
                    k: v for k, v in historico.items() if k != "pares_t4"
                },
                "dte_lote_reciente": {
                    k: v for k, v in reciente.items() if k != "pares_t4"
                },
                "f29": self.conteos["f29"],
                "recepcion_diaria": recepcion,
            },
            "totales": {
                "dtes": dtes_totales,
                "facturas": facturas_totales,
                "suma_monto_total_dte": str(suma_dte),
            },
            "trampas": trampas,
        }
