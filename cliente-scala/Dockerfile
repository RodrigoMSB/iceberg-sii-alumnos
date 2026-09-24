# Cliente Scala del laboratorio, en dos etapas.
#
# La primera compila con sbt sobre JDK 11 y deja los dos jars autocontenidos.
# La segunda se queda con el JRE y los jars, sin sbt, sin Scala instalado y sin
# el cache de dependencias, que pesa varios cientos de megas.

# ---------------------------------------------------------------- compilacion
FROM eclipse-temurin:11-jdk AS construccion

ARG VERSION_SBT=1.10.7

RUN apt-get update \
 && apt-get install -y --no-install-recommends curl ca-certificates \
 && rm -rf /var/lib/apt/lists/*

RUN curl -fsSL "https://github.com/sbt/sbt/releases/download/v${VERSION_SBT}/sbt-${VERSION_SBT}.tgz" \
      -o /tmp/sbt.tgz \
 && tar -xzf /tmp/sbt.tgz -C /opt \
 && rm /tmp/sbt.tgz
ENV PATH="/opt/sbt/bin:${PATH}"

WORKDIR /construccion

# Primero lo que casi nunca cambia, para que Docker reuse la capa de descargas.
COPY project/build.properties project/plugins.sbt project/
COPY build.sbt ./
RUN sbt -batch update

COPY src ./src
# Solo el jar de SinSpark: es el que usa el laboratorio 09, y saltarse
# ConSpark evita bajar Spark entero, que son cientos de megas.
RUN sbt -batch sinSpark/assembly

# ------------------------------------------------------------------ ejecucion
FROM eclipse-temurin:11-jre

# unzip es para 'ejecutar.sh probar-jar', que cuenta cuantas clases de Spark
# lleva cada jar. Esa cuenta es la prueba que se proyecta en el laboratorio 09,
# asi que tiene que salir de los jars de verdad y no de un README.
RUN apt-get update \
 && apt-get install -y --no-install-recommends unzip \
 && rm -rf /var/lib/apt/lists/*

# Las banderas de la JVM NO van en una variable de entorno. Java anuncia en la
# primera linea que la recogio ("Picked up JAVA_TOOL_OPTIONS: ...") y eso queda
# proyectado arriba de todo. Van en la linea de java, aqui y en ejecutar.sh,
# que es por donde se lanza siempre. Lo de abajo es solo para que la imagen
# tambien haga algo sensato si alguien la corre a secas.

WORKDIR /cliente

# Hadoop 3.3.6 trae reload4j, que es log4j 1.x vivo y coleando. Sin archivo de
# configuracion avisa tres veces que no encuentra appenders, y con uno en WARN
# todavia comenta que no hay libreria nativa. Va en ERROR y por salida de error.
RUN printf '%s\n' \
      'log4j.rootLogger=ERROR, consola' \
      'log4j.appender.consola=org.apache.log4j.ConsoleAppender' \
      'log4j.appender.consola.target=System.err' \
      'log4j.appender.consola.layout=org.apache.log4j.PatternLayout' \
      'log4j.appender.consola.layout.ConversionPattern=%p %c %m%n' \
    > /cliente/log4j.properties

COPY --from=construccion /construccion/modulos/sin-spark/target/scala-2.12/sin-spark.jar ./

# Sin ENTRYPOINT: ejecutar.sh elige el jar y asi el contenedor se lanza igual
# de las dos formas, sin banderas que recordar.
CMD ["java", \
     "--add-opens=java.base/java.nio=ALL-UNNAMED", \
     "--add-opens=java.base/java.util=ALL-UNNAMED", \
     "--add-opens=java.base/java.lang=ALL-UNNAMED", \
     "--add-opens=java.base/sun.nio.ch=ALL-UNNAMED", \
     "-Dorg.slf4j.simpleLogger.defaultLogLevel=error", \
     "-Dlog4j2.loggerContextFactory=org.apache.logging.log4j.simple.SimpleLoggerContextFactory", \
     "-Dlog4j.configuration=file:/cliente/log4j.properties", \
     "-jar", "/cliente/con-spark.jar"]
