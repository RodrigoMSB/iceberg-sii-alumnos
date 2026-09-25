#!/usr/bin/env python3
"""
Verifica las guias del alumno contra la solucion ejecutada de cada laboratorio.

    bin/verificar-guias.sh          todas las guias que tengan fuente
    bin/verificar-guias.sh 10       solo la del laboratorio 10

Revisa cuatro cosas, y sale con error si alguna falla:

1. Cada bloque de salida del PDF es, caracter a caracter, lo que dejo la celda
   en solucion/lab-XX.ipynb. Se compara sin los saltos de linea que agrega el
   ancho de la pagina.
2. Cada bloque de codigo del PDF es la sentencia de la celda en la solucion.
3. El texto del PDF no dice 'indice', 'alumno1' a 'alumno6' ni 'relator', y no
   nombra otro laboratorio que el propio, salvo el 15, que repasa a proposito.
4. Cada diagrama tiene debajo la explicacion de cada caja, por su color.
5. Cada identificador de pagina, cada hora y cada numero de filas o bytes que
   cita la prosa aparece en algun bloque de salida de la misma guia. Las horas
   que se dan en hora de Chile no se revisan, porque son una conversion.

Ademas avisa, sin fallar, de los dos puntos y las rayas que aparezcan en la prosa.
"""

from __future__ import annotations

import re
import subprocess
import sys
import unicodedata
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import generar  # noqa: E402

PROHIBIDAS = [
    (re.compile(r"[íi]ndice", re.I), "índice"),
    (re.compile(r"\balumno[1-6]\b", re.I), "alumno1 a alumno6"),
    (re.compile(r"relator", re.I), "relator"),
]


def sin_espacios(t: str) -> str:
    return re.sub(r"\s+", "", unicodedata.normalize("NFC", t))


def texto_pdf(pdf: Path) -> str:
    """El texto del PDF, sin los pies de pagina, que pdftotext mete en medio de un
    bloque cuando el bloque cruza de una pagina a otra."""
    r = subprocess.run(["pdftotext", "-raw", str(pdf), "-"], capture_output=True, text=True, check=True)
    sin_pie = re.sub(r"Laboratorio \d\d · [^·\n]* · \d+/\d+", " ", r.stdout)
    return sin_pie.replace("\f", "\n")


def referencias_a_otros(texto: str, propio: int) -> list[str]:
    """'laboratorio 04', 'lab 04', 'lab-04', 'Laboratorio 01 —'. No cuenta nombres de tabla."""
    hallazgos = []
    for m in re.finditer(r"(?<![_\w])(laboratorios?|labs?)[\s\-]+(\d{1,2})\b", texto, re.I):
        if int(m.group(2)) != propio:
            ini = max(0, m.start() - 40)
            hallazgos.append(texto[ini:m.end() + 20].replace("\n", " "))
    return hallazgos


UNIDADES = r"(?:filas?|bytes|documentos|archivos|p[aá]ginas?|papelitos|contribuyentes|registros)"


def citas_sin_respaldo(documento: str, salidas: str) -> list[str]:
    """Numeros de la prosa que no aparecen en ninguna salida de la guia."""
    import html as _h
    prosa = re.sub(r"<pre>.*?</pre>|<svg.*?</svg>|<style>.*?</style>|<title>.*?</title>", " ",
                   documento, flags=re.S)
    prosa = _h.unescape(re.sub(r"<[^>]+>", " ", prosa))
    prosa = re.sub(r"\s+", " ", prosa)
    fallas = []
    for m in re.finditer(r"(?<![\d.])\d{15,20}(?![\d.])", prosa):
        if m.group(0) not in salidas:
            fallas.append(f"identificador {m.group(0)}")
    for m in re.finditer(r"(?<![\d:/])\d{1,2}:\d{2}(?::\d{2}(?:\.\d{1,3})?)?(?![\d:])", prosa):
        despues = prosa[m.end():m.end() + 30]
        if re.match(r"\s*(?:hrs\.? )?(?:en|de) (?:hora de )?Chile", despues):
            continue
        if m.group(0) not in salidas:
            fallas.append(f"hora {m.group(0)}")
    for m in re.finditer(r"(?<![\d.,])(\d{1,3}(?:\.\d{3})+|\d+)(?:,\d+)? " + UNIDADES + r"\b", prosa):
        crudo = m.group(1).replace(".", "")
        if not (re.search(rf"(?<![\d.]){crudo}(?![\d])", salidas)
                or re.search(rf"(?<![\d.]){re.escape(m.group(1))}(?![\d])", salidas)):
            fallas.append(f"'{m.group(0)}'")
    return fallas


def verificar(carpeta: Path) -> tuple[list[str], list[str]]:
    g = generar.Guia(carpeta)
    documento = g.html()
    fallas = [f"diagrama: {p}" for p in g.problemas]
    pdf = carpeta / "GUIA.pdf"
    if not pdf.exists():
        return fallas + ["no existe GUIA.pdf"], []
    texto = texto_pdf(pdf)
    plano = sin_espacios(texto)

    # 1 y 2. Codigo y salidas, contra la solucion.
    for tipo, lista in (("codigo", g.usadas_codigo), ("salida", g.usadas_salida)):
        for et in lista:
            celda = g.celdas[et]
            esperado = (generar._texto(celda["source"]).rstrip("\n") if tipo == "codigo"
                        else generar.salida_de_celda(celda))
            if sin_espacios(esperado) not in plano:
                fallas.append(f"{tipo} de la celda {et}: el PDF no lo trae igual a la solucion")
    # Lo mismo al reves: cada bloque del HTML sale de una celda de la solucion. Un
    # bloque largo va partido en dos divisiones con la misma celda: se juntan.
    import html as _h
    bloques: list[list] = []
    for clase, et, cuerpo in re.findall(
            r'<div class="(codigo[^"]*)" data-celda="([\d.]+)">(?:<div class="etiqueta">[^<]*</div>)?<pre>(.*?)</pre>',
            documento, re.S):
        cuerpo = _h.unescape(cuerpo)
        if "continua" in clase and bloques and bloques[-1][1] == et:
            bloques[-1][2] += "\n" + cuerpo
        else:
            bloques.append([clase, et, cuerpo])
    for clase, et, cuerpo in bloques:
        celda = g.celdas[et]
        esperado = (generar.salida_de_celda(celda) if "salida" in clase
                    else generar._texto(celda["source"]).rstrip("\n"))
        if cuerpo != esperado:
            fallas.append(f"bloque de la celda {et} distinto de la solucion")

    # 5. Lo que cita la prosa tiene que estar en alguna salida de la guia.
    salidas = "\n".join(generar.salida_de_celda(g.celdas[et]) for et in g.usadas_salida)
    for f in citas_sin_respaldo(documento, salidas):
        fallas.append(f"la prosa cita {f} y no esta en ninguna salida de la guia")

    # 3. Palabras y referencias.
    for patron, nombre in PROHIBIDAS:
        for m in patron.finditer(texto):
            ini = max(0, m.start() - 40)
            fallas.append(f"aparece '{nombre}': ...{texto[ini:m.end() + 30]!r}")
    propio = int(g.numero)
    if propio != 15:
        for h in referencias_a_otros(texto, propio):
            fallas.append(f"referencia a otro laboratorio: ...{h!r}")

    # Avisos de estilo: dos puntos y rayas en la prosa, fuera del codigo.
    prosa = re.sub(r"<pre>.*?</pre>", "", documento, flags=re.S)
    prosa = re.sub(r"<code>.*?</code>|<svg.*?</svg>|<style>.*?</style>|<table.*?</table>", "", prosa, flags=re.S)
    prosa = re.sub(r"<[^>]+>", " ", prosa)
    avisos = []
    for m in re.finditer(r"[^\s]*\s?[:—–]\s?[^\s]*", prosa):
        frag = m.group(0)
        if re.search(r"https?:|\d:\d", frag):
            continue
        avisos.append(frag.strip())
    return fallas, avisos


def main(args: list[str]) -> None:
    if args and args[0] != "todos":
        carpetas = [generar.carpeta_del_lab(a) for a in args]
    else:
        carpetas = [c for c in sorted(generar.LABS.glob("lab-*")) if (c / "guia" / "fuente.md").exists()]
    total = 0
    for c in carpetas:
        fallas, avisos = verificar(c)
        paginas = subprocess.run(["pdfinfo", str(c / "GUIA.pdf")], capture_output=True, text=True).stdout
        n = re.search(r"Pages:\s+(\d+)", paginas)
        estado = "OK   " if not fallas else "FALLA"
        print(f"  {estado} {c.name}/GUIA.pdf  {n.group(1) if n else '?'} paginas")
        for f in fallas:
            print(f"        {f}")
        for a in avisos:
            print(f"        aviso de estilo: {a!r}")
        total += len(fallas)
    sys.exit(1 if total else 0)


if __name__ == "__main__":
    main(sys.argv[1:])
