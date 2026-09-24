#!/usr/bin/env bash
#
# Funciones comunes de los scripts de operacion del curso.
#
# TODOS estos scripts los corre el INSTRUCTOR, desde su terminal, en la raiz de
# este repositorio. El alumno nunca abre una terminal: todo lo suyo pasa en el
# navegador (estandar didactico, Regla 6).
#
# Se opera el ambiente por 'docker exec' contra los nombres fijos de contenedor
# que declara este repositorio. Esos nombres son CONTRATO PUBLICO entre los dos
# repositorios: estan documentados en README.md y renombrarlos
# rompe todos los laboratorios.

set -euo pipefail

RAIZ_CURSO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# --- Contrato de nombres de contenedor --------------------------------------
PREFIJO_JUPYTER="iceberg-"
SERVICIOS_NUCLEO=(iceberg-postgres iceberg-namenode iceberg-datanode iceberg-hive-metastore)
SERVICIOS_ACCESO=(iceberg-spark-thrift iceberg-hue lab-caddy)

ESPACIO_UNICO="mi_espacio"

if [ -t 1 ]; then
  _ROJO=$'\033[31m'; _VERDE=$'\033[32m'; _AMARILLO=$'\033[33m'
  _CIAN=$'\033[36m'; _NEGRITA=$'\033[1m'; _FIN=$'\033[0m'
else
  _ROJO=""; _VERDE=""; _AMARILLO=""; _CIAN=""; _NEGRITA=""; _FIN=""
fi

ok()     { printf '%s  OK  %s %s\n' "${_VERDE}" "${_FIN}" "$*"; }
falla()  { printf '%s FALLA%s %s\n' "${_ROJO}" "${_FIN}" "$*"; }
aviso()  { printf '%s AVISO%s %s\n' "${_AMARILLO}" "${_FIN}" "$*"; }
info()   { printf '%s==> %s%s\n' "${_CIAN}" "$*" "${_FIN}"; }
titulo() { printf '\n%s%s%s\n' "${_NEGRITA}" "$*" "${_FIN}"; }

morir() {
  falla "$1"; shift
  for linea in "$@"; do printf '        %s\n' "${linea}"; done
  exit 1
}

contenedor_vivo() {
  docker ps --format '{{.Names}}' 2>/dev/null | grep -qx "$1"
}

exigir_docker() {
  command -v docker >/dev/null 2>&1 || morir \
    "no encuentro el comando 'docker'." \
    "Estos scripts se corren desde tu terminal, no dentro de Jupyter."
  docker info >/dev/null 2>&1 || morir \
    "el demonio de Docker no responde." \
    "Inicia Docker Desktop y reintenta."
}

# Usuarios con un Jupyter efectivamente arriba, en el orden del contrato.
usuarios_activos() {
  local vivos
  vivos="$(docker ps --format '{{.Names}}' | grep "^${PREFIJO_JUPYTER}" || true)"
  for usuario in "${USUARIOS_FULL[@]}"; do
    if echo "${vivos}" | grep -qx "${PREFIJO_JUPYTER}${usuario}"; then
      echo "${usuario}"
    fi
  done
}

contenedor_de() { echo "${PREFIJO_JUPYTER}$1"; }

# Ejecuta un script de Python (por stdin) dentro del Jupyter de un usuario.
python_en() {
  local usuario="$1"
  docker exec -i -e "LAB_USER=${usuario}" "$(contenedor_de "${usuario}")" python3 -
}

# Directorio del laboratorio a partir de su numero: 00 -> labs/lab-00-...
directorio_lab() {
  local numero="$1"
  numero="${numero#lab-}"
  local encontrados=("${RAIZ_CURSO}"/labs/lab-"${numero}"-*)
  if [ ! -d "${encontrados[0]}" ]; then
    morir "no existe ningun laboratorio '${numero}' en labs/." \
          "Disponibles: $(cd "${RAIZ_CURSO}/labs" 2>/dev/null && echo lab-* || echo ninguno)"
  fi
  echo "${encontrados[0]}"
}
