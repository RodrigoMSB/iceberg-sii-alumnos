#!/usr/bin/env bash
#
# Genera la guia del alumno de un laboratorio, en PDF.
#
#   bin/generar-guia.sh 10       laboratorios/lab-10-.../GUIA.pdf
#   bin/generar-guia.sh todos    todas las que tengan fuente
#
# La fuente esta en laboratorios/lab-XX-.../guia/fuente.md. El codigo y las
# salidas no se escriben en la fuente: se leen de solucion/lab-XX.ipynb cada vez.
# Hace falta Python 3 y Google Chrome. No hace falta el ambiente arriba.

set -euo pipefail
cd "$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
exec python3 bin/guia/generar.py "${@:-todos}"
