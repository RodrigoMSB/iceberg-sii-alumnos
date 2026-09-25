#!/usr/bin/env bash
#
# Verifica las guias contra la solucion ejecutada de cada laboratorio.
#
#   bin/verificar-guias.sh          todas
#   bin/verificar-guias.sh 10       solo la del laboratorio 10
#
# Hace falta pdftotext y pdfinfo (poppler).

set -euo pipefail
cd "$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
exec python3 bin/guia/verificar.py "$@"
