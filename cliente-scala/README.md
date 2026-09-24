# Cliente Scala del laboratorio

Una aplicación Scala que lee las tablas Iceberg del laboratorio desde fuera de Jupyter y
fuera de Hue. Sirve para mostrar en vivo, y en una sola corrida, que la tabla no le
pertenece a ningún motor.

Son dos programas.

| Programa | Qué demuestra |
|---|---|
| **ConSpark** | Levanta su propio `SparkSession` contra el mismo Metastore. Es un tercer motor Spark, además del cuaderno del alumno y del Thrift Server que atiende a Hue |
| **SinSpark** | Usa la API Java de Iceberg directamente. Sin Spark en ninguna parte. Abre un `HiveCatalog`, carga la tabla, lee los registros con `IcebergGenerics` y le escribe una fila |

El segundo es el que cierra el argumento. Una tabla Iceberg es un directorio de archivos
Parquet más unos índices que dicen cuáles cuentan, y cualquier programa que sepa leer ese
formato la lee. No hace falta el motor que la escribió.

## Cómo se usa

El laboratorio tiene que estar arriba. El contenedor es efímero, entra a la red del
laboratorio mientras dura la corrida y no se agrega ningún servicio al compose del
ambiente.

```bash
docker build -t iceberg-alumnos/cliente-scala:1.0.0 .

./ejecutar.sh con-spark
./ejecutar.sh sin-spark
```

Para apuntar a otra tabla, por ejemplo la de un alumno:

```bash
ESPACIO=mi_espacio TABLA=contribuyentes_lab01 ./ejecutar.sh sin-spark
```

## Configuración

| Variable | Valor por omisión | Quién la lee |
|---|---|---|
| `METASTORE_URI` | `thrift://hive-metastore:9083` | `Config`, y por él ConSpark |
| `HDFS_URI` | `hdfs://namenode:8020` | `Config`, y por él ConSpark |
| `WAREHOUSE` | `hdfs://namenode:8020/warehouse/iceberg` | `Config`, y por él ConSpark |
| `ESPACIO` | `mi_espacio` | los dos programas |
| `TABLA` | `contribuyentes_lab01` | los dos programas |
| `ZONA_HORARIA` | la de la JVM, que en este contenedor es `Etc/UTC` | `Config`, y por él ConSpark |
| `RED_LAB` | `iceberg-alumnos` | `ejecutar.sh` |
| `IMAGEN` | `iceberg-alumnos/cliente-scala:1.0.0` | `ejecutar.sh` |

**SinSpark no pasa por `Config`.** Se muestra entero en el cuaderno del laboratorio 09 y
tiene que leerse de corrido, sin saltar a otro archivo, así que lleva las direcciones
escritas y lee de su propio `main` las dos variables que sí cambian entre alumnos,
`ESPACIO` y `TABLA`. Son las mismas direcciones que trae `Config` por omisión, de modo
que `./ejecutar.sh sin-spark` funciona igual. Si alguna vez cambian, hay que cambiarlas
en los dos lados. Las horas las imprime en UTC, que es la zona en que corren los
contenedores del ambiente y la que muestra `.snapshots`.

Los valores salen de `este repositorio`, de `conf/spark-defaults.conf` y del bloque
`networks` de su compose. Dentro de la red resuelven tanto los nombres de contenedor
`namenode` y `hive-metastore` como los nombres de servicio `namenode` y
`hive-metastore`; aquí se usan los primeros, que son el contrato público documentado.

**La zona horaria tiene que ser la misma que usa la sesión Spark del laboratorio.** Si no,
los dos programas muestran horas distintas para el mismo snapshot y la demostración de que
están viendo la misma tabla se cae sola. El laboratorio no fija `spark.sql.session.timeZone`,
así que Spark toma la de su JVM, y los contenedores del ambiente corren en `Etc/UTC`. Este
contenedor también, de modo que basta con preguntarle a la JVM. Se comprueba con

```sql
SET spark.sql.session.timeZone
```

contra el Thrift Server. `ZONA_HORARIA` existe por si algún día el ambiente fija esa
propiedad a otra cosa.

Kerberos está fuera de alcance, igual que en todo el curso.

## Versiones

Son las de Cloudera 7.1.9. Ninguna actualización de cortesía.

| Componente | Versión |
|---|---|
| Scala | 2.12.18 |
| JDK | 11 |
| Spark | 3.3.4 |
| Iceberg | 1.3.0 |
| Hive Metastore cliente | 3.1.3 |
| Hadoop cliente | 3.3.6 |
| sbt | 1.10.7 |

Con una salvedad. **ConSpark no usa Hadoop 3.3.6 sino el que trae Spark 3.3.4, que es
3.3.2.** Spark empaqueta su cliente Hadoop en un artefacto sombreado y forzarle otra
versión por encima es una fuente conocida de fallas de enlace. Donde la versión de Hadoop
se declara de verdad, que es SinSpark, sí es 3.3.6.

## La lista mínima de dependencias

### ConSpark

```
org.apache.spark  %% spark-sql                       % 3.3.4
org.apache.spark  %% spark-hive                      % 3.3.4
org.apache.iceberg % iceberg-spark-runtime-3.3_2.12  % 1.3.0
```

`spark-hive` no estaba en la especificación y hace falta igual. Sin él Spark no tiene
`HiveExternalCatalog`, y `spark.sql.catalogImplementation=hive` no llega a arrancar.

### SinSpark

```
org.apache.iceberg % iceberg-core            % 1.3.0
org.apache.iceberg % iceberg-data            % 1.3.0
org.apache.iceberg % iceberg-parquet         % 1.3.0
org.apache.iceberg % iceberg-hive-metastore  % 1.3.0
org.apache.hive    % hive-metastore          % 3.1.3   con exclusiones
org.apache.hadoop  % hadoop-client           % 3.3.6
org.slf4j          % slf4j-simple            % 1.7.36
```

De `hive-metastore` se excluye lo que no participa en hablar thrift con el Metastore, que
es casi todo: `hive-exec`, ORC, HBase, Tephra, los servidores YARN y los Jetty embebidos.

**Lo que no se puede excluir es `hive-common`.** `HiveCatalog.initialize` construye un
`HiveConf`, y sin ese artefacto la primera línea del programa muere con

```
java.lang.NoClassDefFoundError: org/apache/hadoop/hive/conf/HiveConf$ConfVars
```

Verificado sacándolo y volviéndolo a poner.

## Por qué la traza está configurada como está

Entre Spark, Hive y Hadoop se juntan tres bibliotecas de log distintas, y al empaquetar
todo en un jar único cada una encuentra configuración ajena que no sabe leer. Sin las
medidas de abajo, las dos pantallas arrancan con treinta líneas de ruido antes del primer
dato, y esta salida se proyecta.

**log4j2 queda en el jar pero no se enciende.** No se puede sacar, porque Spark 3.3 nombra
`org.apache.logging.log4j.core.Filter` en su propio `Logging` y sin esa clase no arranca.
Lo que sí se hace es quitarle el puente hacia slf4j, para que el enlace lo tome
`slf4j-simple`, y arrancar la JVM con `log4j2.loggerContextFactory` apuntando a la
implementación simple de log4j2, que no necesita el índice binario de plugins que un fat
jar no puede armar completo. Sin eso aparece esto, dos veces:

```
ERROR StatusLogger Unrecognized conversion specifier [d] ...
ERROR StatusLogger Reconfiguration failed: No configuration found for 'Default'
```

**Por lo mismo el código no llama a `spark.sparkContext.setLogLevel`.** Ese método castea
el contexto de log4j2 a su implementación completa y aquí no la hay. El nivel se fija por
línea de comando.

**Hadoop 3.3.6 trae reload4j, que es log4j 1.x vivo.** Se le deja un
`/cliente/log4j.properties` válido en la imagen y se le indica por
`-Dlog4j.configuration`. Sin él avisa tres veces que no encuentra appenders.

**Las banderas de la JVM van en la línea de `java`, no en `JAVA_TOOL_OPTIONS`.** Con la
variable, Java anuncia en la primera línea que la recogió y eso queda proyectado arriba de
todo.

## Estructura

```
build.sbt
project/plugins.sbt          sbt-assembly
project/build.properties     version de sbt
src/main/scala/cl/sii/iceberg/
  ConSpark.scala
  SinSpark.scala             se compila solo, sin Config.scala
  Config.scala               variables de entorno, y la impresion alineada: solo ConSpark
Dockerfile                   dos etapas, compila con sbt y corre con java -jar
ejecutar.sh                  docker run en la red del laboratorio
```

Dos detalles del armado que conviene saber antes de tocarlo.

**Son dos jars y no uno.** El de SinSpark no debe llevar Spark adentro: esa ausencia es la
demostración, no un detalle de empaquetado. Se comprueba así:

```
con-spark.jar  entradas=110678  spark=10575  iceberg=13247
sin-spark.jar  entradas= 66241  spark=    0  iceberg= 2856
```

**`modulos/con-spark` y `modulos/sin-spark` no llevan código.** Existen solo para que sbt
tenga dónde dejar su salida. Las tres fuentes viven en un único árbol y cada módulo
declara en `build.sbt` cuáles toma. `sinSpark` toma **solo** `SinSpark.scala`.

**La impresión no usa el `show()` de Spark.** Dibuja marcos con guiones, y el material del
curso va sin rayas. ConSpark imprime por `Salida`, que alinea columnas; SinSpark imprime
con `println` a secas, porque se lee entero en clase y una capa de impresión propia es
una cosa más que explicar.

`IcebergGenerics` entrega los registros en el orden de los archivos, que no es ninguno.
SinSpark ordena por la primera columna antes de imprimir, para poder poner su salida al
lado de la de ConSpark, que consulta con `ORDER BY rut`. Se ordena lo que se imprime, no
lo que se lee.

## Alcance

**ConSpark es de solo lectura.** **SinSpark lee y además escribe una fila**, la de Litre
Transportes, que es la demostración del laboratorio 09: la tabla no es de nadie. Es
idempotente, así que correrlo dos veces no duplica la fila ni agrega otra página.

Ninguno de los dos crea nada en el Metastore ni agrega servicios al laboratorio.
