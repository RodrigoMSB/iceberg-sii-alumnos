#!/usr/bin/env bash
#
# Genera los datos del curso y los deja cargados. Se corre UNA VEZ, despues de
# levantar el ambiente por primera vez.
#
#   bin/cargar-datos.sh            genera lo que falte y carga
#   bin/cargar-datos.sh --rehacer  lo vuelve a generar todo desde cero
#
# QUE DEJA
#
#   mi_espacio   tu base de trabajo, vacia. Es donde vas a crear tus tablas
#   curso        las tablas de referencia que leen los laboratorios
#   origen       la base PostgreSQL que el laboratorio 16 migra a Iceberg
#
# Los datos son sinteticos y deterministas: la misma semilla produce los mismos
# bytes, asi que los numeros que te salgan son los mismos que salen en clase.
#
# NO incluye la bodega de diez millones del laboratorio 17, que va aparte
# porque demora bastante mas:  bin/crear-bodega.sh

set -euo pipefail
cd "$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

if [ -t 1 ]; then VERDE=$'\033[32m'; ROJO=$'\033[31m'; NEGRITA=$'\033[1m'; FIN=$'\033[0m'
else VERDE=""; ROJO=""; NEGRITA=""; FIN=""; fi
ok()    { printf '%s  OK  %s %s\n' "${VERDE}" "${FIN}" "$*"; }
paso()  { printf '\n%s==> %s%s\n' "${NEGRITA}" "$*" "${FIN}"; }
morir() { printf '%s FALLA%s %s\n' "${ROJO}" "${FIN}" "$1"; shift; for l in "$@"; do printf '        %s\n' "$l"; done; exit 1; }

docker inspect iceberg-jupyter >/dev/null 2>&1 || morir \
  "el ambiente no esta arriba." "Levantalo primero con:  bin/ambiente.sh arriba"

REHACER="no"
[ "${1:-}" = "--rehacer" ] && REHACER="si"

# --- 1. Generar los datos --------------------------------------------------
# El generador corre DENTRO del contenedor de Jupyter, que ya trae Python y
# pyarrow. Asi el alumno no instala nada en su maquina.
if [ "${REHACER}" = "si" ] || ! docker exec iceberg-jupyter test -f /opt/datos/manifiesto.json 2>/dev/null; then
  paso "generando los datos (un minuto y medio, mas o menos)"
  docker exec iceberg-jupyter mkdir -p /opt/datos
  docker cp datagen iceberg-jupyter:/opt/datagen >/dev/null
  docker exec iceberg-jupyter python3 -m pip install --quiet pyarrow 2>/dev/null || true
  docker exec -w /opt iceberg-jupyter env PYTHONPATH=/opt/datagen \
    python3 -m datagen --escala curso --salida /opt/datos/
  ok "datos generados"
else
  ok "los datos ya estaban generados (usa --rehacer para volver a hacerlos)"
fi

# --- 2. Cargar las tablas de 'curso' y crear 'mi_espacio' ------------------
paso "cargando las tablas en el catalogo"
docker cp bin/cargar-datos.py iceberg-jupyter:/opt/cargar-datos.py >/dev/null
docker exec -w /opt iceberg-jupyter python3 /opt/cargar-datos.py --dentro
ok "tablas cargadas"

# --- 2b. La tabla compartida del laboratorio 10 ----------------------------
paso "preparando la tabla del laboratorio 10"
bin/reiniciar-lab.sh 10 >/dev/null
ok "tabla del 10 lista"

# --- 3. El origen del laboratorio 16 ---------------------------------------
paso "preparando el origen del laboratorio 16"
bin/origen-lab16.sh >/dev/null 2>&1 || bin/origen-lab16.sh
ok "origen listo"

# --- 4. El jar del laboratorio 09 ------------------------------------------
paso "compilando el programa Scala del laboratorio 09"
bin/compilar-jar.sh
ok "jar listo"

docker exec iceberg-jupyter mkdir -p /home/mi_espacio/trabajo/.datos-cargados
echo
ok "todo listo. Abre JupyterLab y empieza por laboratorios/lab-00-tu-primera-libreta/"
