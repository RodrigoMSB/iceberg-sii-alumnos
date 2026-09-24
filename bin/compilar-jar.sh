#!/usr/bin/env bash
#
# Compila el programa Scala del laboratorio 09 y lo deja donde el cuaderno lo
# busca, en /home/mi_espacio/sin-spark.jar.
#
#   bin/compilar-jar.sh            compila si falta
#   bin/compilar-jar.sh --rehacer  vuelve a compilar aunque ya exista
#
# POR QUE NO VIENE COMPILADO EN EL REPOSITORIO
#
# El jar pesa 117 MB y GitHub no acepta archivos sobre 100 MB. Asi que el
# repositorio trae el codigo fuente, en cliente-scala/, y esto lo compila en tu
# maquina. La primera vez baja sbt y las dependencias y demora varios minutos;
# despues queda hecho.
#
# El codigo esta en cliente-scala/src/main/scala/cl/sii/iceberg/SinSpark.scala,
# y es el mismo que el cuaderno del laboratorio 09 muestra entero.

set -euo pipefail
cd "$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

IMAGEN="iceberg-alumnos/cliente-scala:1.0.0"
DESTINO="/home/mi_espacio/sin-spark.jar"

if [ "${1:-}" != "--rehacer" ] && docker exec iceberg-jupyter test -f "${DESTINO}" 2>/dev/null; then
  echo "  el jar ya estaba compilado (usa --rehacer para rehacerlo)"
  exit 0
fi

echo "  compilando. La primera vez baja sbt y sus dependencias: varios minutos."
docker build -t "${IMAGEN}" cliente-scala/

contenedor="$(docker create "${IMAGEN}")"
trap 'docker rm -f "${contenedor}" >/dev/null 2>&1 || true' EXIT
docker cp "${contenedor}:/cliente/sin-spark.jar" /tmp/sin-spark.jar >/dev/null
docker cp /tmp/sin-spark.jar iceberg-jupyter:"${DESTINO}" >/dev/null
rm -f /tmp/sin-spark.jar

docker exec iceberg-jupyter ls -lh "${DESTINO}" | awk '{print "  jar en", $9, "(" $5 ")"}'
