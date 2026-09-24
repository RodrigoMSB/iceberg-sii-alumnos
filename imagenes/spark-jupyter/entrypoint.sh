#!/usr/bin/env bash
# Arranca JupyterLab para el alumno, en su propia maquina.
#
# El ambiente es de un solo usuario y no hay proxy delante, asi que JupyterLab
# vive en la raiz (base_url "/") y se abre en http://localhost:8888/.
set -euo pipefail

LAB_USER="${LAB_USER:-mi_espacio}"
LAB_HOME="/home/${LAB_USER}"
JUPYTER_TOKEN="${JUPYTER_TOKEN:?falta JUPYTER_TOKEN: copia .env.example a .env}"

mkdir -p "${LAB_HOME}/trabajo"
cd "${LAB_HOME}"

# Si no viene una config de Spark propia, hereda la del ambiente.
export SPARK_CONF_DIR="${SPARK_CONF_DIR:-/opt/spark/conf}"

echo "==> JupyterLab para ${LAB_USER}, en http://localhost:8888/"
echo "==> SPARK_HOME=${SPARK_HOME} SPARK_CONF_DIR=${SPARK_CONF_DIR}"

exec jupyter lab \
  --ip=0.0.0.0 \
  --port=8888 \
  --no-browser \
  --allow-root \
  --ServerApp.token="${JUPYTER_TOKEN}" \
  --ServerApp.password='' \
  --ServerApp.root_dir="${LAB_HOME}" \
  --ServerApp.allow_remote_access=True
