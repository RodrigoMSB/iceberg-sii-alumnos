#!/usr/bin/env bash
# Arranca NameNode o DataNode en foreground (sin sbin/start-dfs.sh, que asume ssh).
set -euo pipefail

ROLE="${1:-namenode}"

case "${ROLE}" in
  namenode)
    NN_DIR="${HDFS_NAMENODE_DIR:-/hadoop/dfs/name}"
    mkdir -p "${NN_DIR}"
    # Formatear solo la primera vez: si ya hay VERSION, el volumen persiste.
    if [ ! -f "${NN_DIR}/current/VERSION" ]; then
      echo "==> NameNode sin formatear, ejecutando 'hdfs namenode -format'"
      hdfs namenode -format -force -nonInteractive
    else
      echo "==> NameNode ya formateado, se conserva el estado existente"
    fi
    exec hdfs namenode
    ;;
  datanode)
    DN_DIR="${HDFS_DATANODE_DIR:-/hadoop/dfs/data}"
    mkdir -p "${DN_DIR}"
    exec hdfs datanode
    ;;
  # Escotilla de escape: permite 'docker compose run namenode hdfs dfs -ls /'
  *)
    exec "$@"
    ;;
esac
