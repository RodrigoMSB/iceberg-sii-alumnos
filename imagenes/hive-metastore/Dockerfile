# Hive Metastore 3.1.3 standalone -> PostgreSQL, catalogo Iceberg central.
#
# Corre con JDK 11 (mismo JDK que Spark 3.3 en CDP 7.1.9). Ver README
# "Problemas conocidos" para los parches que exige Hive 3.1.3 sobre JDK 11.
FROM eclipse-temurin:11-jdk-jammy

ARG HIVE_VERSION=3.1.3
ARG HADOOP_VERSION=3.3.6
ARG POSTGRES_JDBC_VERSION=42.6.0
ARG ICEBERG_VERSION=1.3.0
ARG TARGETARCH

ENV HIVE_VERSION=${HIVE_VERSION} \
    HADOOP_VERSION=${HADOOP_VERSION} \
    HIVE_HOME=/opt/hive \
    HADOOP_HOME=/opt/hadoop \
    HADOOP_CONF_DIR=/opt/hadoop/etc/hadoop \
    PATH=/opt/hive/bin:/opt/hadoop/bin:${PATH}

RUN set -eux; \
    apt-get update; \
    DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
        curl ca-certificates bash procps tini netcat-openbsd; \
    rm -rf /var/lib/apt/lists/*

# Hadoop: el metastore necesita los jars de cliente Hadoop en el classpath.
# Igual que en images/hadoop, tarball aarch64 nativo en ARM.
RUN set -eux; \
    case "${TARGETARCH}" in \
      arm64) HADOOP_TARBALL="hadoop-${HADOOP_VERSION}-aarch64.tar.gz" ;; \
      amd64) HADOOP_TARBALL="hadoop-${HADOOP_VERSION}.tar.gz" ;; \
      *) echo "arquitectura no soportada: '${TARGETARCH}'" >&2; exit 1 ;; \
    esac; \
    curl -fsSL --retry 3 -o /tmp/hadoop.tar.gz \
      "https://archive.apache.org/dist/hadoop/common/hadoop-${HADOOP_VERSION}/${HADOOP_TARBALL}"; \
    mkdir -p /opt/hadoop; \
    tar -xzf /tmp/hadoop.tar.gz -C /opt/hadoop --strip-components=1; \
    rm -f /tmp/hadoop.tar.gz; \
    rm -rf /opt/hadoop/share/doc

RUN set -eux; \
    curl -fsSL --retry 3 -o /tmp/hive.tar.gz \
      "https://archive.apache.org/dist/hive/hive-${HIVE_VERSION}/apache-hive-${HIVE_VERSION}-bin.tar.gz"; \
    mkdir -p /opt/hive; \
    tar -xzf /tmp/hive.tar.gz -C /opt/hive --strip-components=1; \
    rm -f /tmp/hive.tar.gz

# --- Parches obligatorios de Hive 3.1.3 -------------------------------------
# 1) guava: Hive 3.1.3 trae guava-19, Hadoop 3.3.6 trae guava-27. Con guava-19
#    en el classpath el metastore muere con
#    NoSuchMethodError: com.google.common.base.Preconditions.checkArgument(ZLjava/lang/String;Ljava/lang/Object;)V
#    Se elimina la de Hive y se usa la de Hadoop.
# 2) log4j-slf4j duplicado entre Hive y Hadoop -> warning ruidoso de binding multiple.
# 3) Hive 3.1.3 empaqueta postgresql-9.4.1208.jre7.jar. Si se deja, quedan DOS
#    drivers JDBC de PostgreSQL declarando org.postgresql.Driver y el orden del
#    classloader decide cual gana: contra PostgreSQL 15 el driver 9.4 es una
#    fuente de fallos silenciosos. Se elimina y queda solo el 42.6.0.
RUN set -eux; \
    rm -f ${HIVE_HOME}/lib/guava-*.jar; \
    cp ${HADOOP_HOME}/share/hadoop/common/lib/guava-*.jar ${HIVE_HOME}/lib/; \
    echo "guava en uso:"; ls -1 ${HIVE_HOME}/lib/guava-*.jar; \
    rm -f ${HIVE_HOME}/lib/log4j-slf4j-impl-*.jar; \
    rm -f ${HIVE_HOME}/lib/postgresql-9.*.jar

# Driver JDBC de PostgreSQL (backend del metastore).
RUN set -eux; \
    curl -fsSL --retry 3 -o ${HIVE_HOME}/lib/postgresql-${POSTGRES_JDBC_VERSION}.jar \
      "https://repo1.maven.org/maven2/org/postgresql/postgresql/${POSTGRES_JDBC_VERSION}/postgresql-${POSTGRES_JDBC_VERSION}.jar"

# iceberg-hive-runtime: necesario para el PLAN A (HiveServer2 leyendo Iceberg).
# Se hornea aunque el plan activo sea B, para poder reintentar A sin rebuild.
RUN set -eux; \
    curl -fsSL --retry 3 -o ${HIVE_HOME}/lib/iceberg-hive-runtime-${ICEBERG_VERSION}.jar \
      "https://repo1.maven.org/maven2/org/apache/iceberg/iceberg-hive-runtime/${ICEBERG_VERSION}/iceberg-hive-runtime-${ICEBERG_VERSION}.jar"

COPY entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh

# 9083 metastore thrift | 10000 HiveServer2 | 10002 HS2 UI
EXPOSE 9083 10000 10002

ENTRYPOINT ["/usr/bin/tini", "--", "/usr/local/bin/entrypoint.sh"]
CMD ["metastore"]
