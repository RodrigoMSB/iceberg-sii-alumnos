# JupyterLab + PySpark 3.3 + Iceberg 1.3.0, una instancia por alumno.
#
# Versiones clavadas a CDP 7.1.9 (ver README). No actualizar "de cortesia":
#   Spark 3.3.x  -> parcel CDS de CDP 7.1.9
#   JDK 11       -> el JDK con que CDP corre Spark 3.3
#   Iceberg 1.3.0-> version exacta del cliente
#   Scala 2.12   -> spark-3.3.4-bin-hadoop3 es Scala 2.12, que es lo que exige
#                   el artefacto iceberg-spark-runtime-3.3_2.12
FROM eclipse-temurin:11-jdk-jammy

ARG SPARK_VERSION=3.3.4
ARG ICEBERG_VERSION=1.3.0
ARG SCALA_BINARY=2.12
ARG POSTGRES_JDBC_VERSION=42.7.4

ENV SPARK_VERSION=${SPARK_VERSION} \
    ICEBERG_VERSION=${ICEBERG_VERSION} \
    SPARK_HOME=/opt/spark \
    PATH=/opt/spark/bin:/opt/spark/sbin:${PATH} \
    PYTHONUNBUFFERED=1 \
    PYSPARK_PYTHON=python3 \
    PYSPARK_DRIVER_PYTHON=python3

# Ubuntu jammy trae Python 3.10, dentro del rango soportado por PySpark 3.3
# (3.7-3.10). Python 3.11+ rompe PySpark 3.3, por eso NO usamos una base mas nueva.
RUN set -eux; \
    apt-get update; \
    DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
        python3 python3-pip python3-dev \
        curl ca-certificates bash procps tini vim less; \
    rm -rf /var/lib/apt/lists/*; \
    python3 --version

# Spark. El tarball es identico en ambas arquitecturas (JVM + Python puro);
# no hay binarios nativos dependientes de arch, por eso una sola descarga sirve
# para amd64 y arm64.
RUN set -eux; \
    curl -fsSL --retry 3 -o /tmp/spark.tgz \
      "https://archive.apache.org/dist/spark/spark-${SPARK_VERSION}/spark-${SPARK_VERSION}-bin-hadoop3.tgz"; \
    mkdir -p /opt/spark; \
    tar -xzf /tmp/spark.tgz -C /opt/spark --strip-components=1; \
    rm -f /tmp/spark.tgz; \
    rm -rf /opt/spark/examples/src /opt/spark/data

# Iceberg horneado en la imagen (requisito de spec: NO descargar en runtime).
# CA-6 verifica exactamente este nombre de archivo en el classpath.
RUN set -eux; \
    curl -fsSL --retry 3 -o "${SPARK_HOME}/jars/iceberg-spark-runtime-3.3_${SCALA_BINARY}-${ICEBERG_VERSION}.jar" \
      "https://repo1.maven.org/maven2/org/apache/iceberg/iceberg-spark-runtime-3.3_${SCALA_BINARY}/${ICEBERG_VERSION}/iceberg-spark-runtime-3.3_${SCALA_BINARY}-${ICEBERG_VERSION}.jar"; \
    ls -l "${SPARK_HOME}/jars/iceberg-spark-runtime-3.3_${SCALA_BINARY}-${ICEBERG_VERSION}.jar"

# PySpark se toma de SPARK_HOME (no de pip) para garantizar que la version de
# Python y la de los jars sean exactamente la misma.
ENV PYTHONPATH=${SPARK_HOME}/python:${SPARK_HOME}/python/lib/py4j-0.10.9.5-src.zip

# numpy va FIJADO y antes que pandas a proposito. pandas 1.5.3 esta compilado
# contra la ABI de numpy 1.x; si se deja que pip resuelva numpy libre, instala
# 2.x y 'import pandas' revienta con "numpy.dtype size changed, may indicate
# binary incompatibility". El defecto vivio en la imagen sin que nadie lo viera
# porque ningun test importaba pandas: ahora lo cubre test_iceberg_smoke.py.
RUN set -eux; \
    pip3 install --no-cache-dir \
        "numpy<2" \
        "jupyterlab==3.6.7" \
        "notebook==6.5.6" \
        "ipywidgets==8.1.1" \
        "pandas==1.5.3" \
        "pyarrow==12.0.1" \
        "pytest==7.4.4" \
        "grpcio-status==1.48.2"; \
    jupyter --version; \
    python3 -c "import pandas, numpy; print('pandas', pandas.__version__, '/ numpy', numpy.__version__)"

COPY entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh

# Magia %%sql (SPEC-005 §3). Va al final del Dockerfile a proposito: es lo que
# mas se va a tocar, y una capa nueva aca no invalida las descargas de Spark ni
# de Iceberg, que son los minutos caros de la construccion.
#
#   ipython-startup/magia_sql.py    -> la implementacion, en /opt/lab/python
#   ipython-startup/00-magia-sql.py -> el arranque, que la importa en cada kernel
#
# El directorio de arranque de IPython vive en la IMAGEN (HOME=/root), no en
# /home/<alumno>, que es un volumen: por eso la magia sobrevive a que se
# reinicie el volumen de trabajo de un alumno, y esta en los siete Jupyter sin
# que nadie escriba %load_ext.
# Driver JDBC de PostgreSQL, para el laboratorio 16.
#
# El laboratorio simula una migracion desde una base relacional, y el alumno
# abre el origen con una vista JDBC en SQL puro. Sin este jar, la vista falla
# con "No suitable driver". Va aqui abajo y no junto al de Iceberg para no
# invalidar la capa de pip, que es cara.
#
# No toca ninguna otra version: es un jar mas en el mismo directorio.
RUN set -eux; \
    curl -fsSL --retry 3 -o "${SPARK_HOME}/jars/postgresql-${POSTGRES_JDBC_VERSION}.jar" \
      "https://repo1.maven.org/maven2/org/postgresql/postgresql/${POSTGRES_JDBC_VERSION}/postgresql-${POSTGRES_JDBC_VERSION}.jar"; \
    ls -l "${SPARK_HOME}/jars/postgresql-${POSTGRES_JDBC_VERSION}.jar"

# Cliente HDFS, para el laboratorio 11.
#
# El laboratorio muestra cuanto ocupa en disco una tabla, y para eso hace falta
# preguntarle al sistema de archivos y no solo a la libreta. NO se instala el
# tarball de Hadoop: FsShell ya viene dentro de los jars sombreados que trae
# Spark, y lo unico que le faltaba era /opt/spark/conf en el classpath, que es
# donde esta montado core-site.xml. Son cuatro lineas y cero megabytes.
RUN set -eux; \
    printf '%s\n' \
      '#!/bin/sh' \
      '# Cliente HDFS minimo, sobre los jars que Spark ya trae.' \
      '# Acepta "hdfs dfs -du -s /ruta" y tambien "hdfs -du -s /ruta".' \
      '[ "$1" = "dfs" ] && shift' \
      'exec java -cp "/opt/spark/conf:/opt/spark/jars/*" org.apache.hadoop.fs.FsShell "$@"' \
      > /usr/local/bin/hdfs; \
    chmod +x /usr/local/bin/hdfs

COPY ipython-startup/magia_sql.py    /opt/lab/python/magia_sql.py
COPY ipython-startup/00-magia-sql.py /root/.ipython/profile_default/startup/00-magia-sql.py

EXPOSE 8888
ENTRYPOINT ["/usr/bin/tini", "--", "/usr/local/bin/entrypoint.sh"]
