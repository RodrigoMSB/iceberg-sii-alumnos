#!/usr/bin/env python3
"""
Genera la guia del alumno de un laboratorio, en PDF.

    bin/generar-guia.sh 10        la guia del laboratorio 10
    bin/generar-guia.sh todos     las de todos los laboratorios que tengan fuente

La fuente vive en laboratorios/lab-XX-.../guia/fuente.md y el PDF queda en
laboratorios/lab-XX-.../GUIA.pdf.

La fuente es Markdown sencillo, mas unas pocas directivas en su propia linea:

    ::codigo 1.1      el codigo de la celda 1.1, tal cual esta en la solucion
    ::salida 1.1      lo que esa celda dejo en pantalla, tal cual
    ::diagrama        un diagrama de cajas de colores, hasta ::fin
    ::bloque bash     un bloque de texto literal con su etiqueta, hasta ::fin
    ::salto           salto de pagina

El codigo y las salidas NUNCA se escriben a mano en la fuente: se leen de
solucion/lab-XX.ipynb cada vez que se genera. Por eso lo que dice la guia es
siempre lo que salio de verdad en la ultima ejecucion de la solucion.

El PDF lo imprime Google Chrome sin ventana. No hace falta nada mas.
"""

from __future__ import annotations

import html
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
LABS = RAIZ / "laboratorios"
AQUI = Path(__file__).resolve().parent

CHROME_CANDIDATOS = [
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
    "google-chrome", "google-chrome-stable", "chromium", "chromium-browser",
]


# --------------------------------------------------------------------------
# El cuaderno de la solucion
# --------------------------------------------------------------------------

def _texto(v) -> str:
    return "".join(v) if isinstance(v, list) else (v or "")


def _tabla_html_a_texto(h: str) -> str:
    """Una tabla de pandas en HTML, como columnas alineadas."""
    filas = []
    for tr in re.findall(r"<tr[^>]*>(.*?)</tr>", h, re.S):
        celdas = re.findall(r"<t[hd][^>]*>(.*?)</t[hd]>", tr, re.S)
        filas.append([html.unescape(re.sub(r"<[^>]+>", "", c)).strip() for c in celdas])
    if not filas:
        return ""
    ancho = [0] * max(len(f) for f in filas)
    for f in filas:
        for i, c in enumerate(f):
            ancho[i] = max(ancho[i], len(c))
    lineas = []
    for f in filas:
        partes = [c.ljust(ancho[i]) for i, c in enumerate(f)]
        lineas.append("  ".join(partes).rstrip())
    return "\n".join(lineas)


def _html_a_texto(h: str) -> str:
    if "<table" in h:
        return _tabla_html_a_texto(h)
    h = re.sub(r"<br\s*/?>", "\n", h)
    return html.unescape(re.sub(r"<[^>]+>", "", h)).strip("\n")


def salida_de_celda(celda: dict) -> str:
    """Todo lo que la celda dejo en pantalla, en orden, como texto."""
    partes = []
    for o in celda.get("outputs", []):
        tipo = o.get("output_type")
        if tipo == "stream":
            partes.append(_texto(o.get("text")).rstrip("\n"))
        elif tipo in ("display_data", "execute_result"):
            datos = o.get("data", {})
            if "text/html" in datos:
                partes.append(_html_a_texto(_texto(datos["text/html"])))
            elif "text/plain" in datos:
                partes.append(_texto(datos["text/plain"]).rstrip("\n"))
        elif tipo == "error":
            tb = "\n".join(o.get("traceback", []))
            partes.append(re.sub(r"\x1b\[[0-9;]*m", "", tb).rstrip("\n"))
    return "\n".join(p for p in partes if p != "")


def lenguaje_de_celda(fuente: str) -> str:
    # La primera linea que cuenta: el comentario '# Celda N.N' no dice el lenguaje.
    utiles = [l for l in fuente.splitlines()
              if l.strip() and not re.match(r"\s*(--|#|//)\s*Celda \d+\.\d+\s*$", l)]
    primera = utiles[0].lstrip() if utiles else ""
    if primera.startswith("%%time") and len(utiles) > 1:
        primera = utiles[1].lstrip()
    if primera.startswith("%%sql"):
        return "sql"
    if primera.startswith("%%bash") or primera.startswith("!"):
        return "bash"
    if primera.startswith("%%writefile") and ".scala" in primera:
        return "scala"
    if primera.startswith("%%writefile") or primera.startswith("%%"):
        return "text"
    return "python"


def celdas_por_etiqueta(cuaderno: Path) -> dict[str, dict]:
    nb = json.loads(cuaderno.read_text(encoding="utf-8"))
    mapa: dict[str, dict] = {}
    for c in nb["cells"]:
        if c["cell_type"] != "code":
            continue
        fuente = _texto(c["source"])
        m = re.search(r"(?:--|#|//)\s*Celda (\d+\.\d+)\b", fuente)
        if m:
            if m.group(1) in mapa:
                raise SystemExit(f"{cuaderno}: la celda {m.group(1)} aparece dos veces")
            mapa[m.group(1)] = c
    return mapa


# --------------------------------------------------------------------------
# Diagramas
# --------------------------------------------------------------------------

COLORES = {
    # nombre      relleno    borde      texto
    "azul":       ("#e8f0fb", "#3b6fb6", "#1f4e8c"),
    "morado":     ("#efebfb", "#6a55b8", "#4a3690"),
    "amarillo":   ("#fbefd9", "#c98a1c", "#7a5208"),
    "gris":       ("#f1efea", "#8a857a", "#3f3c36"),
    "verde":      ("#eaf4e2", "#5d9a3a", "#35661a"),
    "verde agua": ("#e2f4f0", "#2f9884", "#17695a"),
    "rojo":       ("#fbe8e8", "#c0443f", "#8f2320"),
    "coral":      ("#fcebe4", "#d9734f", "#9a4424"),
}


def _partir_linea(t: str) -> list[str]:
    return [p.strip() for p in t.split("|")] if t else []


def diagrama_svg(texto: str) -> tuple[str, list[tuple[str, str]]]:
    """
    Formato, una instruccion por linea:

        caja ID FILA COLUMNA COLOR "Titulo" "subtitulo | segunda linea" [ancho=N]
        flecha ORIGEN DESTINO ["etiqueta"]
        columnas N

    Las filas y columnas empiezan en 0 y la columna puede ser fraccionaria.
    Devuelve el SVG y la lista (titulo, color) para revisar la explicacion.
    """
    cajas: dict[str, dict] = {}
    flechas = []
    columnas = None
    for linea in texto.splitlines():
        linea = linea.strip()
        if not linea or linea.startswith("#"):
            continue
        comillas = re.findall(r'"([^"]*)"', linea)
        resto = re.sub(r'"[^"]*"', "", linea).split()
        if resto[0] == "columnas":
            columnas = int(resto[1])
        elif resto[0] == "caja":
            _, ident, fila, col = resto[:4]
            opciones = dict(p.split("=") for p in resto[4:] if "=" in p)
            color = " ".join(p for p in resto[4:] if "=" not in p)
            if color not in COLORES:
                raise SystemExit(f"diagrama: color desconocido '{color}' en: {linea}")
            cajas[ident] = {
                "fila": float(fila), "col": float(col), "color": color,
                "titulo": comillas[0] if comillas else ident,
                "sub": _partir_linea(comillas[1]) if len(comillas) > 1 else [],
                "ancho": float(opciones.get("ancho", 1)),
            }
        elif resto[0] == "flecha":
            flechas.append((resto[1], resto[2], comillas[0] if comillas else ""))
        else:
            raise SystemExit(f"diagrama: no entiendo la linea: {linea}")

    if columnas is None:
        columnas = int(max(c["col"] + c["ancho"] for c in cajas.values()) + 0.999)
    W = 680
    colw = W / columnas
    fila_alto = {}
    for c in cajas.values():
        alto = 30 + 15 * max(1, len(c["sub"]))
        fila_alto[c["fila"]] = max(fila_alto.get(c["fila"], 0), alto)
    gap = 44
    y_fila = {}
    y = 8
    for f in sorted(fila_alto):
        y_fila[f] = y
        y += fila_alto[f] + gap
    H = y - gap + 8

    for c in cajas.values():
        c["x"] = c["col"] * colw + 8
        c["w"] = c["ancho"] * colw - 16
        c["y"] = y_fila[c["fila"]]
        c["h"] = fila_alto[c["fila"]]

    partes = [
        f'<svg class="diagrama" viewBox="0 0 {W} {H:.0f}" width="{W}" height="{H:.0f}" '
        f'xmlns="http://www.w3.org/2000/svg" font-family="Helvetica, Arial, sans-serif">',
        '<defs><marker id="punta" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" '
        'markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="#555"/>'
        "</marker></defs>",
    ]
    etiquetas = []
    for o, d, et in flechas:
        a, b = cajas[o], cajas[d]
        if b["fila"] > a["fila"]:
            x1, y1 = a["x"] + a["w"] / 2, a["y"] + a["h"]
            x2, y2 = b["x"] + b["w"] / 2, b["y"]
        elif b["fila"] < a["fila"]:
            # Hacia arriba: sube derecho desde el borde de arriba del origen y
            # entra por el costado del destino, en ángulo recto. Solo si el
            # origen queda debajo del destino sube en línea recta.
            x1, y1 = a["x"] + a["w"] / 2, a["y"]
            ym = b["y"] + b["h"] / 2
            if x1 > b["x"] + b["w"]:
                x2 = b["x"] + b["w"]
            elif x1 < b["x"]:
                x2 = b["x"]
            else:
                x2 = None
            if x2 is not None:
                partes.append(
                    f'<polyline points="{x1:.1f},{y1:.1f} {x1:.1f},{ym:.1f} {x2:.1f},{ym:.1f}" '
                    f'fill="none" stroke="#555" stroke-width="1.2" marker-end="url(#punta)"/>'
                )
                if et:
                    etiquetas.append((x1, (y1 + ym) / 2, et))
                continue
            x2, y2 = x1, b["y"] + b["h"]
        else:
            izq = b["x"] > a["x"]
            x1 = a["x"] + (a["w"] if izq else 0)
            x2 = b["x"] + (0 if izq else b["w"])
            y1 = y2 = a["y"] + a["h"] / 2
        partes.append(
            f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" '
            f'stroke="#555" stroke-width="1.2" marker-end="url(#punta)"/>'
        )
        if et:
            mx, my = (x1 + x2) / 2, (y1 + y2) / 2
            etiquetas.append((mx, my, et))
    for c in cajas.values():
        relleno, borde, tinta = COLORES[c["color"]]
        partes.append(
            f'<rect x="{c["x"]:.1f}" y="{c["y"]:.1f}" width="{c["w"]:.1f}" height="{c["h"]:.1f}" '
            f'rx="7" fill="{relleno}" stroke="{borde}" stroke-width="1.3"/>'
        )
        cx = c["x"] + c["w"] / 2
        lineas = 1 + len(c["sub"])
        y0 = c["y"] + c["h"] / 2 - (lineas - 1) * 15 / 2 + 4
        partes.append(
            f'<text x="{cx:.1f}" y="{y0:.1f}" text-anchor="middle" font-size="12.5" '
            f'font-weight="bold" fill="{tinta}">{html.escape(c["titulo"])}</text>'
        )
        for i, s in enumerate(c["sub"]):
            partes.append(
                f'<text x="{cx:.1f}" y="{y0 + 15 * (i + 1):.1f}" text-anchor="middle" '
                f'font-size="10.5" fill="{tinta}">{html.escape(s)}</text>'
            )
    for mx, my, et in etiquetas:
        ancho = 6.2 * len(et) + 10
        mx = min(max(mx, ancho / 2 + 2), W - ancho / 2 - 2)
        partes.append(
            f'<rect x="{mx - ancho / 2:.1f}" y="{my - 9:.1f}" width="{ancho:.1f}" height="16" '
            f'rx="3" fill="#ffffff"/>'
            f'<text x="{mx:.1f}" y="{my + 3:.1f}" text-anchor="middle" font-size="10.5" '
            f'fill="#333">{html.escape(et)}</text>'
        )
    partes.append("</svg>")
    return "\n".join(partes), [(c["titulo"], c["color"]) for c in cajas.values()]


# --------------------------------------------------------------------------
# Markdown sencillo
# --------------------------------------------------------------------------

def en_linea(t: str) -> str:
    t = html.escape(t, quote=False)
    t = re.sub(r"`([^`]+)`", r"<code>\1</code>", t)
    t = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", t)
    t = re.sub(r"(?<![*\w])\*([^*]+)\*(?![*\w])", r"<em>\1</em>", t)
    return t


def _es_titulo(elemento: str, siguiente: str) -> bool:
    """Lo que no puede quedar solo al pie de una página: un título, o un párrafo corto que
    presenta lo que viene abajo (una lista, un bloque, una tabla, un diagrama)."""
    if re.match(r"<h[2-4][ >]", elemento):
        return True
    if elemento.startswith("<p>") and not siguiente.startswith("<p>"):
        return len(re.sub(r"<[^>]+>", "", elemento)) <= 160
    return False


def pegar_titulos(out: list[str]) -> list[str]:
    """Junta cada título con el bloque que lo sigue, para que no se separen de página."""
    resultado: list[str] = []
    for elemento in reversed(out):
        if resultado and _es_titulo(elemento, resultado[0]):
            cabeza, resto = _partir_bloque_largo(resultado[0])
            resultado[0] = f'<div class="junto">{elemento}\n{cabeza}</div>'
            if resto:
                resultado.insert(1, resto)
        else:
            resultado.insert(0, elemento)
    return resultado


LINEAS_JUNTO = 12
LINEAS_LARGO = 40


def _partir_bloque_largo(elemento: str) -> tuple[str, str]:
    """Un bloque de más de una página no cabe entero junto a su título: se pegan al
    título sus primeras líneas y el resto sigue como continuación del mismo bloque."""
    m = re.fullmatch(r'<div class="(codigo[^"]*)"( data-celda="[^"]*")?>(<div class="etiqueta">.*?</div>)'
                     r"<pre([^>]*)>(.*)</pre></div>", elemento, re.S)
    if not m:
        return elemento, ""
    estilo, cuerpo = m.group(4), m.group(5)
    lineas = cuerpo.split("\n")
    if len(lineas) <= LINEAS_LARGO:
        return elemento, ""
    clase, celda, etiqueta = m.group(1), m.group(2) or "", m.group(3)
    cabeza = "\n".join(lineas[:LINEAS_JUNTO])
    resto = "\n".join(lineas[LINEAS_JUNTO:])
    return (f'<div class="{clase} partido"{celda}>{etiqueta}<pre{estilo}>{cabeza}</pre></div>',
            f'<div class="{clase} continua"{celda}><pre{estilo}>{resto}</pre></div>')


# Caracteres que caben en una línea de un bloque, con la letra de siempre.
LETRA_PT = 8.2
CABEN = 96
LETRA_MINIMA_PT = 4.0


def letra_de_tabla(celda: dict) -> float | None:
    """Si la celda muestra una tabla más ancha que el bloque, la letra con que cada fila
    cabe en una línea y las columnas quedan alineadas. Nunca menos de 4 puntos: una fila
    que no cabe ni así se parte, y las demás siguen alineadas."""
    ancho = 0
    for o in celda.get("outputs", []):
        h = _texto(o.get("data", {}).get("text/html", ""))
        if "<table" in h:
            ancho = max([ancho] + [len(l) for l in _tabla_html_a_texto(h).splitlines()])
    if ancho <= CABEN:
        return None
    return max(LETRA_MINIMA_PT, round(LETRA_PT * CABEN / ancho, 2))


def bloque_codigo(etiqueta: str, cuerpo: str, clase: str = "codigo", celda: str = "",
                  letra: float | None = None) -> str:
    marca = f' data-celda="{celda}"' if celda else ""
    estilo = f' style="font-size:{letra}pt"' if letra else ""
    return (
        f'<div class="{clase}"{marca}><div class="etiqueta">{html.escape(etiqueta)}</div>'
        f"<pre{estilo}>{html.escape(cuerpo)}</pre></div>"
    )


class Guia:
    def __init__(self, carpeta: Path):
        self.carpeta = carpeta
        self.fuente = carpeta / "guia" / "fuente.md"
        texto = self.fuente.read_text(encoding="utf-8")
        cabecera, _, self.cuerpo = texto.partition("\n---\n")
        self.meta = {}
        for linea in cabecera.splitlines():
            if ":" in linea:
                k, v = linea.split(":", 1)
                self.meta[k.strip()] = v.strip()
        self.numero = self.meta["numero"]
        self.titulo = self.meta["titulo"]
        self.cuaderno = carpeta / "solucion" / f"lab-{self.numero}.ipynb"
        self.celdas = celdas_por_etiqueta(self.cuaderno)
        self.problemas: list[str] = []
        self.usadas_codigo: list[str] = []
        self.usadas_salida: list[str] = []

    # ---- directivas
    def _codigo(self, et: str) -> str:
        if et not in self.celdas:
            raise SystemExit(f"{self.fuente}: la solucion no tiene la celda {et}")
        self.usadas_codigo.append(et)
        fuente = _texto(self.celdas[et]["source"]).rstrip("\n")
        return bloque_codigo(lenguaje_de_celda(fuente), fuente, celda=et)

    def _salida(self, et: str) -> str:
        if et not in self.celdas:
            raise SystemExit(f"{self.fuente}: la solucion no tiene la celda {et}")
        self.usadas_salida.append(et)
        s = salida_de_celda(self.celdas[et])
        if not s.strip():
            raise SystemExit(f"{self.fuente}: la celda {et} no dejo salida en la solucion")
        return bloque_codigo("text", s, "codigo salida", celda=et, letra=letra_de_tabla(self.celdas[et]))

    # ---- el cuerpo
    def html_cuerpo(self) -> str:
        lineas = self.cuerpo.splitlines()
        out: list[str] = []
        i = 0
        parrafo: list[str] = []
        diagrama_pendiente: list[tuple[str, str]] | None = None
        explicacion: list[str] = []

        def cerrar_parrafo():
            nonlocal parrafo
            if parrafo:
                t = " ".join(x.strip() for x in parrafo)
                out.append(f"<p>{en_linea(t)}</p>")
                if diagrama_pendiente is not None:
                    explicacion.append(t)
                parrafo = []

        def revisar_diagrama():
            nonlocal diagrama_pendiente, explicacion
            if diagrama_pendiente is None:
                return
            texto = " ".join(explicacion)
            for titulo, color in diagrama_pendiente:
                if f"**{titulo}" not in texto and f"**{titulo}**" not in texto:
                    self.problemas.append(f"diagrama sin explicar la caja '{titulo}'")
                if color not in texto:
                    self.problemas.append(f"diagrama sin nombrar el color '{color}' de '{titulo}'")
            diagrama_pendiente, explicacion = None, []

        while i < len(lineas):
            linea = lineas[i]
            s = linea.strip()
            if s.startswith("::"):
                cerrar_parrafo()
                partes = s[2:].split(None, 1)
                orden, arg = partes[0], (partes[1] if len(partes) > 1 else "")
                if orden not in ("salida",):
                    revisar_diagrama()
                if orden == "codigo":
                    out.append(self._codigo(arg))
                elif orden == "salida":
                    out.append(self._salida(arg))
                elif orden == "salto":
                    out.append('<div class="salto"></div>')
                elif orden in ("diagrama", "bloque"):
                    j = i + 1
                    buf = []
                    while lineas[j].strip() != "::fin":
                        buf.append(lineas[j])
                        j += 1
                    if orden == "diagrama":
                        svg, cajas = diagrama_svg("\n".join(buf))
                        out.append(f'<div class="figura">{svg}</div>')
                        diagrama_pendiente, explicacion = cajas, []
                    else:
                        out.append(bloque_codigo(arg or "text", "\n".join(buf)))
                    i = j
                else:
                    raise SystemExit(f"{self.fuente}: directiva desconocida {s}")
                i += 1
                continue
            if not s:
                cerrar_parrafo()
                i += 1
                continue
            m = re.match(r"(#{1,4})\s+(.*)", s)
            if m:
                cerrar_parrafo()
                revisar_diagrama()
                n = len(m.group(1))
                clase = ""
                if n == 1:
                    clase = ' class="parte"'
                out.append(f"<h{n}{clase}>{en_linea(m.group(2))}</h{n}>")
                i += 1
                continue
            if s.startswith("|"):
                cerrar_parrafo()
                filas = []
                while i < len(lineas) and lineas[i].strip().startswith("|"):
                    celdas = [c.strip() for c in lineas[i].strip().strip("|").split("|")]
                    if not all(re.fullmatch(r":?-+:?", c) for c in celdas):
                        filas.append(celdas)
                    i += 1
                t = ['<table class="tabla">']
                for k, f in enumerate(filas):
                    tag = "th" if k == 0 else "td"
                    t.append("<tr>" + "".join(f"<{tag}>{en_linea(c)}</{tag}>" for c in f) + "</tr>")
                t.append("</table>")
                out.append("\n".join(t))
                continue
            if s.startswith("> "):
                cerrar_parrafo()
                buf = []
                while i < len(lineas) and lineas[i].strip().startswith(">"):
                    buf.append(lineas[i].strip()[1:].strip())
                    i += 1
                texto = " ".join(buf)
                if diagrama_pendiente is not None:
                    explicacion.append(texto)
                out.append(f'<div class="nota"><p>{en_linea(texto)}</p></div>')
                continue
            if re.match(r"(- |\d+\. )", s):
                cerrar_parrafo()
                ordenada = bool(re.match(r"\d+\. ", s))
                items: list[str] = []
                while i < len(lineas):
                    l2 = lineas[i]
                    if re.match(r"\s*(- |\d+\. )", l2) and not l2.startswith("   "):
                        items.append(re.sub(r"^\s*(- |\d+\. )", "", l2).strip())
                    elif l2.strip() and l2.startswith("  ") and items:
                        items[-1] += " " + l2.strip()
                    else:
                        break
                    i += 1
                if diagrama_pendiente is not None:
                    explicacion.extend(items)
                tag = "ol" if ordenada else "ul"
                out.append(f"<{tag}>" + "".join(f"<li>{en_linea(x)}</li>" for x in items) + f"</{tag}>")
                continue
            parrafo.append(linea)
            i += 1
        cerrar_parrafo()
        revisar_diagrama()
        return "\n".join(pegar_titulos(out))

    def html(self) -> str:
        css = (AQUI / "estilo.css").read_text(encoding="utf-8")
        pie = f"Laboratorio {self.numero} · {self.titulo}"
        css = css.replace("__PIE__", pie.replace('"', '\\"'))
        portada = (
            '<section class="portada">'
            f'<div class="numero">Laboratorio {html.escape(self.numero)}</div>'
            f"<h1>{html.escape(self.titulo)}</h1>"
            f'<div class="subtitulo">{en_linea(self.meta.get("subtitulo", "Guía del laboratorio"))}</div>'
            "</section>"
        )
        return (
            "<!doctype html><html lang=\"es\"><head><meta charset=\"utf-8\">"
            f"<title>Laboratorio {self.numero} · {html.escape(self.titulo)}</title>"
            f"<style>{css}</style></head><body>{portada}"
            f'<main>{self.html_cuerpo()}</main></body></html>'
        )


def chrome() -> str:
    for c in CHROME_CANDIDATOS:
        if os.path.exists(c) or shutil.which(c):
            return c
    raise SystemExit("no encuentro Google Chrome ni Chromium para imprimir el PDF")


def generar(carpeta: Path) -> Path:
    g = Guia(carpeta)
    documento = g.html()
    if g.problemas:
        raise SystemExit(f"{g.fuente}:\n  " + "\n  ".join(g.problemas))
    destino = carpeta / "GUIA.pdf"
    with tempfile.TemporaryDirectory() as tmp:
        pagina = Path(tmp) / "guia.html"
        pagina.write_text(documento, encoding="utf-8")
        # Chrome escribe el PDF y a veces no termina solo: se espera a que el
        # archivo deje de crecer y se cierra.
        if destino.exists():
            destino.unlink()
        proceso = subprocess.Popen(
            [chrome(), "--headless=new", "--disable-gpu", "--no-pdf-header-footer",
             "--no-first-run", "--no-default-browser-check", "--disable-extensions",
             f"--user-data-dir={tmp}/perfil",
             f"--print-to-pdf={destino}", pagina.as_uri()],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
        tamano, quieto = -1, 0
        for _ in range(240):
            if proceso.poll() is not None:
                break
            time.sleep(0.5)
            actual = destino.stat().st_size if destino.exists() else -1
            quieto = quieto + 1 if actual == tamano and actual > 0 else 0
            tamano = actual
            if quieto >= 4:
                break
        if proceso.poll() is None:
            proceso.terminate()
            proceso.wait(timeout=10)
        if not destino.exists() or destino.stat().st_size == 0:
            raise SystemExit(f"Chrome no dejo el PDF en {destino}")
        if os.environ.get("GUIA_HTML"):
            shutil.copy(pagina, os.environ["GUIA_HTML"])
    return destino


def carpeta_del_lab(n: str) -> Path:
    encontradas = sorted(LABS.glob(f"lab-{n.zfill(2)}-*"))
    if not encontradas:
        raise SystemExit(f"no existe el laboratorio {n}")
    return encontradas[0]


def main(args: list[str]) -> None:
    if not args:
        raise SystemExit("uso: generar.py <numero de laboratorio|todos>")
    if args[0] == "todos":
        carpetas = [c for c in sorted(LABS.glob("lab-*")) if (c / "guia" / "fuente.md").exists()]
    else:
        carpetas = [carpeta_del_lab(a) for a in args]
    for c in carpetas:
        destino = generar(c)
        print(f"  {destino.relative_to(RAIZ)}")


if __name__ == "__main__":
    main(sys.argv[1:])
