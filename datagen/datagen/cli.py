"""Interfaz de linea de comandos del generador."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .escalas import ESCALAS, obtener_escala
from .generador import Generador
from .perfiles import obtener_perfil, perfiles_disponibles

SEMILLA_POR_DEFECTO = 20260813


def construir_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m datagen",
        description=(
            "Genera los datos tributarios sinteticos del universo DGT para el "
            "curso de Apache Iceberg."
        ),
    )
    parser.add_argument(
        "--escala",
        default="dev",
        choices=sorted(ESCALAS),
        help="dev (~100 mil DTEs, para tests) o curso (~2 millones)",
    )
    parser.add_argument(
        "--salida",
        default=None,
        help="directorio de salida (por defecto datos/, o datos-bodega/ con --bodega)",
    )
    parser.add_argument(
        "--semilla",
        type=int,
        default=SEMILLA_POR_DEFECTO,
        help=f"semilla del generador (por defecto {SEMILLA_POR_DEFECTO})",
    )
    parser.add_argument(
        "--pais",
        default="chile",
        choices=list(perfiles_disponibles()),
        help="perfil de pais",
    )
    parser.add_argument(
        "--silencioso",
        action="store_true",
        help="no imprime el resumen al terminar",
    )
    parser.add_argument(
        "--bodega",
        action="store_true",
        help=(
            "genera SOLO la bodega de diez anios del laboratorio 17 "
            "(2015 a 2024, un millon de filas por anio) en su propia carpeta. "
            "No escribe manifiesto.json ni toca los datos del curso"
        ),
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = construir_parser().parse_args(argv)

    perfil = obtener_perfil(args.pais)
    escala = obtener_escala(args.escala)
    salida = Path(args.salida or ("datos-bodega/" if args.bodega else "datos/"))

    generador = Generador(
        perfil=perfil, escala=escala, semilla=args.semilla, salida=salida
    )

    if args.bodega:
        try:
            resumen = generador.ejecutar_bodega()
        except ValueError as error:
            print(error, file=sys.stderr)
            return 2
        ruta = salida / "bodega.json"
        ruta.write_text(
            json.dumps(resumen, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        if not args.silencioso:
            _imprimir_bodega(resumen, ruta)
        return 0

    manifiesto = generador.ejecutar()

    ruta_manifiesto = salida / "manifiesto.json"
    # sort_keys + separadores fijos: el manifiesto tambien tiene que ser
    # byte-identico entre corridas con la misma semilla (CA-2).
    ruta_manifiesto.write_text(
        json.dumps(manifiesto, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    if not args.silencioso:
        _imprimir_resumen(manifiesto, ruta_manifiesto)
    return 0


def _imprimir_bodega(resumen: dict, ruta: Path) -> None:
    print(
        f"Bodega de diez anios  |  semilla={resumen['semilla']}  "
        f"{resumen['filas']:,} filas en {resumen['archivos']} archivos"
    )
    print("\nPor anio:")
    for anio in resumen["anios"]:
        print(f"  {anio['anio']}  {anio['filas']:>10,} filas  "
              f"{anio['archivos']:>3} archivos")
    print(f"\nsuma de monto_total: {resumen['suma_monto_total']}")
    print(f"Resumen: {ruta}")
    print("\nEsto NO es el universo del curso: no lleva manifiesto.json.")


def _imprimir_resumen(manifiesto: dict, ruta_manifiesto: Path) -> None:
    print(
        f"Universo DGT generado  |  escala={manifiesto['escala']}  "
        f"semilla={manifiesto['semilla']}  pais={manifiesto['pais']}"
    )
    print("\nDatasets:")
    for nombre, datos in manifiesto["datasets"].items():
        print(f"  {nombre:<22} {datos['filas']:>10,} filas  "
              f"{datos['archivos']:>5} archivo(s)")
    print("\nTrampas pedagogicas:")
    for identificador in sorted(manifiesto["trampas"]):
        trampa = manifiesto["trampas"][identificador]
        conteo = trampa.get("conteo")
        if conteo is None:
            detalle = f"{trampa.get('archivos', '-')} archivos" if identificador == "T-7" else "estructural"
        else:
            detalle = f"{conteo:,} casos ({trampa.get('tasa_real', 0):.4f})"
        print(f"  {identificador}  {trampa['nombre']:<38} {detalle}")
    print(f"\nManifiesto: {ruta_manifiesto}")


if __name__ == "__main__":
    sys.exit(main())
