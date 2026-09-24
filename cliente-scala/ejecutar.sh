#!/usr/bin/env bash
#
# Lanza el cliente Scala contra el laboratorio que esta corriendo.
#
#   ./ejecutar.sh con-spark
#   ./ejecutar.sh sin-spark
#   ./ejecutar.sh probar-jar
#   ESPACIO=mi_espacio TABLA=contribuyentes_lab01 ./ejecutar.sh sin-spark
#
# El contenedor es EFIMERO y entra a la red del laboratorio solo mientras dura
# la corrida. No se agrega ningun servicio al compose de este repositorio: el
# ambiente no se entera de que esto existio.
#
# La red se llama 'iceberg-alumnos' y lo declara el compose del ambiente, en su
# bloque networks. Los nombres hive-metastore y namenode son el mismo
# contrato publico que usan los scripts del curso.
#
# Las banderas de la JVM van aqui y no en el Dockerfile, porque son sobre como
# se VE la corrida y esta pantalla se proyecta. Las --add-opens callan los
# avisos de acceso reflexivo de Spark sobre Java 11. El loggerContextFactory
# manda a log4j2 a su implementacion simple, que no necesita el indice de
# plugins que el fat jar no puede armar completo; sin eso, log4j2 escupe treinta
# lineas de StatusLogger antes del primer dato.

set -euo pipefail

RED="${RED_LAB:-iceberg-alumnos}"
IMAGEN="${IMAGEN:-iceberg-alumnos/cliente-scala:1.0.0}"

case "${1:-}" in
  con-spark) JAR="con-spark.jar" ;;
  sin-spark) JAR="sin-spark.jar" ;;
  probar-jar) JAR="" ;;
  *)
    echo "uso: $0 <con-spark|sin-spark|probar-jar>" >&2
    exit 2
    ;;
esac

# probar-jar no habla con el laboratorio: abre los dos jars y cuenta. Es la
# prueba de que "sin Spark" no es una manera de hablar.
if [ "${1}" = "probar-jar" ]; then
  exec docker run --rm --entrypoint sh "${IMAGEN}" -c '
    printf "%-14s %10s %10s %10s\n" jar entradas spark iceberg
    for j in con-spark sin-spark; do
      t=$(unzip -l /cliente/$j.jar | tail -1 | awk "{print \$2}")
      s=$(unzip -l /cliente/$j.jar | grep -c " org/apache/spark/" || true)
      i=$(unzip -l /cliente/$j.jar | grep -c " org/apache/iceberg/" || true)
      printf "%-14s %10s %10s %10s\n" "$j.jar" "$t" "$s" "$i"
    done
    echo
    echo "Las clases de Spark que lleva sin-spark.jar son las de la columna spark."
  '
fi

docker network inspect "${RED}" >/dev/null 2>&1 || {
  echo "no existe la red '${RED}'. El laboratorio tiene que estar arriba." >&2
  echo "bin/ambiente.sh arriba" >&2
  exit 1
}

exec docker run --rm \
  --network "${RED}" \
  -e METASTORE_URI="${METASTORE_URI:-thrift://hive-metastore:9083}" \
  -e HDFS_URI="${HDFS_URI:-hdfs://namenode:8020}" \
  -e WAREHOUSE="${WAREHOUSE:-hdfs://namenode:8020/warehouse/iceberg}" \
  -e ESPACIO="${ESPACIO:-mi_espacio}" \
  -e TABLA="${TABLA:-contribuyentes_lab01}" \
  "${IMAGEN}" \
  java \
    --add-opens=java.base/java.nio=ALL-UNNAMED \
    --add-opens=java.base/java.util=ALL-UNNAMED \
    --add-opens=java.base/java.lang=ALL-UNNAMED \
    --add-opens=java.base/sun.nio.ch=ALL-UNNAMED \
    -Dorg.slf4j.simpleLogger.defaultLogLevel=error \
    -Dorg.slf4j.simpleLogger.showThreadName=false \
    -Dlog4j2.loggerContextFactory=org.apache.logging.log4j.simple.SimpleLoggerContextFactory \
    -Dlog4j2.simplelogLevel=ERROR \
    -Dlog4j.configuration=file:/cliente/log4j.properties \
    -jar "/cliente/${JAR}"
