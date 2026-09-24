#!/usr/bin/env bash
#
# El ambiente del curso, en tu maquina.
#
#   bin/ambiente.sh arriba          levanta lo necesario y espera a que este sano
#   bin/ambiente.sh arriba --sql    ademas Hue y el Spark Thrift Server (labs 02 y 07)
#   bin/ambiente.sh estado          que hay corriendo y si esta sano
#   bin/ambiente.sh abajo           apaga, SIN perder nada
#   bin/ambiente.sh borrar-todo     apaga y borra los datos. No hay vuelta atras
#
# La primera vez demora, porque construye las imagenes y baja Spark. Las
# siguientes son rapidas.

set -euo pipefail
cd "$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

if [ -t 1 ]; then
  ROJO=$'\033[31m'; VERDE=$'\033[32m'; AMARILLO=$'\033[33m'; NEGRITA=$'\033[1m'; FIN=$'\033[0m'
else
  ROJO=""; VERDE=""; AMARILLO=""; NEGRITA=""; FIN=""
fi
ok()    { printf '%s  OK  %s %s\n' "${VERDE}" "${FIN}" "$*"; }
aviso() { printf '%s AVISO%s %s\n' "${AMARILLO}" "${FIN}" "$*"; }
morir() { printf '%s FALLA%s %s\n' "${ROJO}" "${FIN}" "$1"; shift; for l in "$@"; do printf '        %s\n' "$l"; done; exit 1; }

command -v docker >/dev/null 2>&1 || morir "no encuentro Docker." \
  "Instala Docker Desktop y vuelve a intentar."
docker info >/dev/null 2>&1 || morir "Docker no responde." "Abre Docker Desktop y espera a que termine de partir."

[ -f .env ] || morir "falta el archivo .env." \
  "CreALO copiando el ejemplo y cambiando el token:" \
  "    cp .env.example .env"

SERVICIOS_BASE=(iceberg-postgres iceberg-namenode iceberg-datanode iceberg-hive-metastore iceberg-jupyter)
SERVICIOS_SQL=(iceberg-spark-thrift iceberg-hue)

sano() {
  local estado
  estado="$(docker inspect --format '{{if .State.Health}}{{.State.Health.Status}}{{else}}{{.State.Status}}{{end}}' "$1" 2>/dev/null || echo ausente)"
  [ "${estado}" = "healthy" ] || [ "${estado}" = "running" ]
}

esperar() {
  local nombre="$1" intentos="${2:-60}"
  printf '  esperando a %s ' "${nombre}"
  for _ in $(seq 1 "${intentos}"); do
    if sano "${nombre}"; then echo " listo"; return 0; fi
    printf '.'
    sleep 5
  done
  echo
  morir "${nombre} no quedo sano." "Mira que dice con:  docker logs ${nombre}"
}

case "${1:-}" in
  arriba)
    CON_SQL="no"
    [ "${2:-}" = "--sql" ] && CON_SQL="si"
    echo "${NEGRITA}Levantando el ambiente${FIN}"
    echo "  La primera vez construye las imagenes y baja Spark: puede tomar entre"
    echo "  diez y veinte minutos segun tu conexion. Las siguientes son de un minuto."
    echo
    if [ "${CON_SQL}" = "si" ]; then
      docker compose --profile sql up -d --build
    else
      docker compose up -d --build
    fi
    echo
    for s in "${SERVICIOS_BASE[@]}"; do esperar "$s"; done
    if [ "${CON_SQL}" = "si" ]; then
      for s in "${SERVICIOS_SQL[@]}"; do esperar "$s" 90; done
    fi
    echo
    TOKEN="$(grep -E '^JUPYTER_TOKEN=' .env | cut -d= -f2-)"
    PUERTO="$(grep -E '^JUPYTER_PORT=' .env | cut -d= -f2- || true)"
    ok "el ambiente esta arriba"
    echo
    echo "  Abre JupyterLab en:  ${NEGRITA}http://localhost:${PUERTO:-8888}/${FIN}"
    echo "  y cuando pida la clave, escribe el token de tu .env:  ${TOKEN}"
    echo
    if ! docker exec iceberg-jupyter test -d /home/mi_espacio/trabajo/.datos-cargados 2>/dev/null; then
      aviso "todavia no estan los datos. Cargalos una sola vez con:"
      echo "         bin/cargar-datos.sh"
    fi
    ;;

  estado)
    printf '%-28s %s\n' "SERVICIO" "ESTADO"
    for s in "${SERVICIOS_BASE[@]}" "${SERVICIOS_SQL[@]}"; do
      estado="$(docker inspect --format '{{if .State.Health}}{{.State.Health.Status}}{{else}}{{.State.Status}}{{end}}' "$s" 2>/dev/null || echo "-")"
      printf '%-28s %s\n' "$s" "${estado}"
    done
    ;;

  abajo)
    echo "Apagando. Los datos quedan guardados: al volver a levantar esta todo igual."
    docker compose --profile sql down
    ok "apagado"
    ;;

  borrar-todo)
    echo
    echo "${ROJO}${NEGRITA}  ESTO BORRA TODO Y NO HAY VUELTA ATRAS.${FIN}"
    echo
    echo "  Se pierden:"
    echo "    - todas las tablas que creaste en mi_espacio"
    echo "    - las tablas de referencia de la base curso"
    echo "    - la base origen del laboratorio 16"
    echo "    - todo lo que hayas guardado en la carpeta trabajo/ de Jupyter"
    echo
    echo "  NO se pierden los cuadernos del repositorio: esos estan en laboratorios/"
    echo "  y se vuelven a copiar solos."
    echo
    echo "  Despues de esto hay que volver a correr bin/cargar-datos.sh, que"
    echo "  demora unos minutos."
    echo
    printf "  Para confirmar, escribe exactamente  ${NEGRITA}borrar todo${FIN}  y presiona Enter: "
    read -r respuesta
    if [ "${respuesta}" != "borrar todo" ]; then
      aviso "no se borro nada."
      exit 0
    fi
    docker compose --profile sql down -v
    ok "borrado. Para partir de cero:  bin/ambiente.sh arriba  y despues  bin/cargar-datos.sh"
    ;;

  *)
    echo "uso: $0 <arriba [--sql] | estado | abajo | borrar-todo>"
    exit 2
    ;;
esac
