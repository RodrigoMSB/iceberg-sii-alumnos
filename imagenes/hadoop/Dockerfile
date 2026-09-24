# HDFS (NameNode / DataNode) para el laboratorio Iceberg SII.
#
# Por que construimos en vez de usar apache/hadoop:
#   la imagen oficial apache/hadoop publica UNICAMENTE amd64 (verificado en
#   todos sus tags: 2.10, 3.3.5, 3.3.6, 3.4.x, 3.5.0). Como el lab se desarrolla
#   en Apple Silicon y se despliega en x86_64, construimos desde el tarball
#   oficial de Apache, que si tiene binario aarch64 nativo.
FROM eclipse-temurin:11-jre-jammy

ARG HADOOP_VERSION=3.3.6
# TARGETARCH lo inyecta BuildKit automaticamente (amd64 | arm64).
ARG TARGETARCH

ENV HADOOP_VERSION=${HADOOP_VERSION} \
    HADOOP_HOME=/opt/hadoop \
    HADOOP_CONF_DIR=/opt/hadoop/etc/hadoop \
    HADOOP_LOG_DIR=/var/log/hadoop \
    PATH=/opt/hadoop/bin:/opt/hadoop/sbin:${PATH}

RUN set -eux; \
    apt-get update; \
    DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
        curl ca-certificates bash procps tini; \
    rm -rf /var/lib/apt/lists/*; \
    case "${TARGETARCH}" in \
      arm64) HADOOP_TARBALL="hadoop-${HADOOP_VERSION}-aarch64.tar.gz" ;; \
      amd64) HADOOP_TARBALL="hadoop-${HADOOP_VERSION}.tar.gz" ;; \
      *) echo "arquitectura no soportada: '${TARGETARCH}'" >&2; exit 1 ;; \
    esac; \
    echo "==> descargando ${HADOOP_TARBALL} para TARGETARCH=${TARGETARCH}"; \
    curl -fsSL --retry 3 -o /tmp/hadoop.tar.gz \
      "https://archive.apache.org/dist/hadoop/common/hadoop-${HADOOP_VERSION}/${HADOOP_TARBALL}"; \
    mkdir -p /opt/hadoop /var/log/hadoop; \
    tar -xzf /tmp/hadoop.tar.gz -C /opt/hadoop --strip-components=1; \
    rm -f /tmp/hadoop.tar.gz; \
    rm -rf /opt/hadoop/share/doc; \
    /opt/hadoop/bin/hadoop version

COPY conf/ /opt/hadoop/etc/hadoop/
COPY entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh

# 8020 RPC (fs.defaultFS) | 9870 NN UI | 9864 DN UI | 9866 DN data
EXPOSE 8020 9870 9864 9866

ENTRYPOINT ["/usr/bin/tini", "--", "/usr/local/bin/entrypoint.sh"]
CMD ["namenode"]
