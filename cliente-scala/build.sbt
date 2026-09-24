// Cliente Scala independiente del laboratorio de Iceberg.
//
// Son DOS programas y DOS jars, y estan separados a proposito: el jar de
// SinSpark no debe llevar Spark adentro. Esa ausencia es la demostracion, no
// un detalle de empaquetado. Si los dos compartieran un jar, la afirmacion
// "esto lee la tabla sin Spark" no se podria sostener.
//
// Las tres fuentes viven en un solo arbol, src/main/scala/cl/sii/iceberg, y
// cada modulo declara cuales toma. Los directorios bajo modulos/ existen solo
// para que sbt tenga donde dejar su salida; no llevan codigo.
//
// SinSpark.scala se compila SOLO, sin Config.scala. El laboratorio 09 muestra
// ese archivo entero en el cuaderno, y un programa que llama a Config y a
// Salida no se puede leer de corrido: el alumno ve nombres que vienen de otro
// archivo que nunca abre. Config y Salida siguen existiendo para ConSpark.

ThisBuild / organization := "cl.sii"
ThisBuild / version      := "1.0.0"
ThisBuild / scalaVersion := "2.12.18"

// Cloudera 7.1.9. Ninguna actualizacion de cortesia.
val versionSpark    = "3.3.4"
val versionIceberg  = "1.3.0"
val versionHive     = "3.1.3"
val versionHadoop   = "3.3.6"

def fuentes(raiz: File, nombres: String*): Seq[File] = {
  val directorio = raiz / "src" / "main" / "scala" / "cl" / "sii" / "iceberg"
  nombres.map(directorio / _)
}

// Los recursos tambien viven en el arbol compartido, no bajo modulos/.
def recursos(raiz: File): Seq[File] = Seq(raiz / "src" / "main" / "resources")

// Un fat jar junta miles de archivos y varios se repiten entre dependencias.
// Los descartes de abajo son los habituales: firmas de jars, indices de
// modulos de Java 9 y metadatos duplicados.
val estrategiaDeMezcla = assembly / assemblyMergeStrategy := {
  case ruta if ruta.endsWith("module-info.class")                 => MergeStrategy.discard
  case ruta if ruta.startsWith("META-INF/versions/")              => MergeStrategy.first
  case ruta if ruta.endsWith(".SF") || ruta.endsWith(".DSA") ||
               ruta.endsWith(".RSA")                              => MergeStrategy.discard
  case "META-INF/MANIFEST.MF"                                     => MergeStrategy.discard
  case ruta if ruta.startsWith("META-INF/services/")              => MergeStrategy.concat
  case "reference.conf" | "application.conf"                      => MergeStrategy.concat
  // El log4j.properties propio va primero en el classpath del modulo, asi que
  // 'first' se queda con el nuestro y no con el que traiga alguna dependencia.
  case "log4j.properties"                                         => MergeStrategy.first
  case "git.properties" | "mozilla/public-suffix-list.txt"        => MergeStrategy.first
  case ruta if ruta.endsWith(".properties") || ruta.endsWith(".xml") ||
               ruta.endsWith(".txt") || ruta.endsWith(".types")   => MergeStrategy.first
  case _                                                          => MergeStrategy.first
}

// POR QUE log4j QUEDA EN EL JAR PERO NO ENCIENDE
//
// log4j2 no encuentra sus conversores por escaneo sino en un indice binario,
// META-INF/.../Log4j2Plugins.dat, y varios artefactos traen el suyo. Al armar
// un fat jar hay que quedarse con uno y el elegido no tiene los plugins de los
// demas. El sintoma llena la pantalla antes del primer dato:
//
//   ERROR StatusLogger Unrecognized conversion specifier [d] ...
//   ERROR StatusLogger Reconfiguration failed: No configuration found ...
//
// Sacar log4j entero no es opcion: Spark 3.3 nombra org.apache.logging.log4j.
// core.Filter en su propio Logging y sin esa clase no arranca. Lo que si se
// puede es dejar las clases y quitarle el puente hacia slf4j, para que el
// enlace de slf4j lo tome slf4j-simple.
//
// Eso no basta por si solo, porque algo del arbol llama a log4j2 directamente
// y lo despierta igual. El cierre esta en ejecutar.sh, que arranca la JVM con
// loggerContextFactory apuntando a la implementacion simple de log4j2, la que
// no necesita indice de plugins. Las clases estan, nadie enciende el nucleo, y
// la pantalla queda limpia.
val sinPuenteLog4j = excludeDependencies ++= Seq(
  ExclusionRule("org.apache.logging.log4j", "log4j-slf4j-impl"),
  ExclusionRule("org.apache.logging.log4j", "log4j-slf4j2-impl"),
  ExclusionRule("org.slf4j", "slf4j-log4j12"),
  ExclusionRule("log4j", "log4j"),
)

val comunes = Seq(
  scalacOptions ++= Seq("-deprecation", "-feature", "-unchecked"),
  Compile / unmanagedResourceDirectories := recursos((ThisBuild / baseDirectory).value),
  assembly / assemblyOption ~= { _.withIncludeScala(true) },
  estrategiaDeMezcla,
  sinPuenteLog4j,
  libraryDependencies += "org.slf4j" % "slf4j-simple" % "1.7.36",
)

// --- ConSpark: un tercer motor Spark, ademas del cuaderno y del Thrift -------
lazy val conSpark = (project in file("modulos/con-spark"))
  .settings(comunes)
  .settings(
    name := "con-spark",
    Compile / unmanagedSources :=
      fuentes((ThisBuild / baseDirectory).value, "Config.scala", "ConSpark.scala"),
    assembly / mainClass       := Some("cl.sii.iceberg.ConSpark"),
    assembly / assemblyJarName := "con-spark.jar",
    libraryDependencies ++= Seq(
      "org.apache.spark"  %% "spark-sql"                        % versionSpark,
      // spark-hive no esta en la spec y hace falta igual: sin el, Spark no
      // tiene HiveExternalCatalog y catalogImplementation=hive no arranca.
      "org.apache.spark"  %% "spark-hive"                       % versionSpark,
      "org.apache.iceberg" % "iceberg-spark-runtime-3.3_2.12"   % versionIceberg,
    ),
  )

// --- SinSpark: la API Java de Iceberg, sin Spark en ningun lado -------------
lazy val sinSpark = (project in file("modulos/sin-spark"))
  .settings(comunes)
  .settings(
    name := "sin-spark",
    // Hive 3 trae el puente log4j-1.2-api. Con el nucleo de log4j2 apagado, ese
    // puente no encuentra appenders y avisa tres veces antes del primer dato.
    // Aqui no lo necesita nadie: el catalogo de Iceberg habla por slf4j.
    excludeDependencies += ExclusionRule("org.apache.logging.log4j", "log4j-1.2-api"),
    Compile / unmanagedSources :=
      fuentes((ThisBuild / baseDirectory).value, "SinSpark.scala"),
    assembly / mainClass       := Some("cl.sii.iceberg.SinSpark"),
    assembly / assemblyJarName := "sin-spark.jar",
    libraryDependencies ++= Seq(
      "org.apache.iceberg" % "iceberg-core"           % versionIceberg,
      "org.apache.iceberg" % "iceberg-data"           % versionIceberg,
      "org.apache.iceberg" % "iceberg-parquet"        % versionIceberg,
      "org.apache.iceberg" % "iceberg-hive-metastore" % versionIceberg,
      // hive-metastore 3.1.3 arrastra medio Hive. Lo que SI hace falta es
      // hive-common, porque HiveCatalog construye un HiveConf; sacarlo revienta
      // en NoClassDefFoundError apenas se llama a initialize(). Lo que sobra es
      // el motor de consultas, ORC, HBase, Tephra y los Jetty embebidos.
      //
      // Los log4j se van a proposito y la traza sale por slf4j-simple: los que
      // trae Hive vienen con un log4j2.properties que la propia biblioteca no
      // sabe leer y ensucia la pantalla con decenas de lineas StatusLogger
      // antes del primer dato. Esta salida se proyecta.
      ("org.apache.hive" % "hive-metastore" % versionHive)
        .exclude("org.apache.hive", "hive-exec")
        .exclude("org.apache.hbase", "hbase-client")
        .exclude("org.apache.orc", "orc-core")
        .exclude("org.apache.hadoop", "hadoop-yarn-server-resourcemanager")
        .exclude("org.apache.hadoop", "hadoop-yarn-server-applicationhistoryservice")
        .exclude("org.apache.hadoop", "hadoop-yarn-server-common")
        .exclude("org.apache.hadoop", "hadoop-yarn-server-web-proxy")
        .exclude("org.eclipse.jetty", "jetty-server")
        .exclude("org.eclipse.jetty", "jetty-servlet")
        .exclude("org.eclipse.jetty", "jetty-webapp")
        .exclude("org.eclipse.jetty", "jetty-runner")
        .exclude("co.cask.tephra", "tephra-api")
        .exclude("co.cask.tephra", "tephra-core")
        .exclude("co.cask.tephra", "tephra-hbase-compat-1.0")
        .exclude("org.apache.parquet", "parquet-hadoop-bundle")
        .exclude("com.tdunning", "json")
        .exclude("org.slf4j", "slf4j-log4j12")
        .exclude("log4j", "log4j")
        .exclude("org.apache.logging.log4j", "log4j-core")
        .exclude("org.apache.logging.log4j", "log4j-api")
        .exclude("org.apache.logging.log4j", "log4j-slf4j-impl")
        .exclude("org.apache.logging.log4j", "log4j-1.2-api")
        .exclude("org.apache.logging.log4j", "log4j-web"),
      ("org.apache.hadoop" % "hadoop-client" % versionHadoop)
        .exclude("org.slf4j", "slf4j-log4j12")
        .exclude("log4j", "log4j")
        .exclude("org.apache.logging.log4j", "log4j-slf4j-impl"),
    ),
  )

lazy val raiz = (project in file("."))
  .aggregate(conSpark, sinSpark)
  .settings(name := "cliente-scala", publish / skip := true)
