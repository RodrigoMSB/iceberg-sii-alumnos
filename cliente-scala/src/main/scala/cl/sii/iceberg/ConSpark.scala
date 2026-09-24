package cl.sii.iceberg

import org.apache.spark.sql.{DataFrame, SparkSession}

/**
 * La misma tabla, leida por un TERCER motor Spark.
 *
 * En el laboratorio ya hay dos que la tocan, el cuaderno de cada alumno y el
 * Thrift Server que atiende a Hue. Este es un proceso nuevo, que arranca en un
 * contenedor efimero, se conecta al mismo Metastore y ve exactamente lo mismo.
 * Ninguno de los tres le pertenece a la tabla.
 *
 * La configuracion del catalogo va aqui, en el codigo, y no en un
 * spark-defaults.conf: este contenedor no tiene instalacion de Spark de donde
 * heredarla.
 */
object ConSpark {

  def main(argumentos: Array[String]): Unit = {
    Config.imprimirEncabezado("con Spark")

    val spark = sesion()
    try {
      espacios(spark)
      val presente = tablaEnElPresente(spark)
      val paginas = paginasDeLaLibreta(spark)
      primeraPagina(spark, paginas)
      presente.unpersist()
    } finally {
      spark.stop()
    }

    Salida.titulo("Fin")
    Salida.linea("La tabla la leyo un proceso Spark que no es el cuaderno ni el Thrift Server.")
  }

  private def sesion(): SparkSession = {
    val spark = SparkSession
      .builder()
      .appName("cliente-scala-con-spark")
      .master("local[*]")
      .config("spark.sql.extensions", "org.apache.iceberg.spark.extensions.IcebergSparkSessionExtensions")
      .config("spark.sql.catalog.spark_catalog", "org.apache.iceberg.spark.SparkSessionCatalog")
      .config("spark.sql.catalog.spark_catalog.type", "hive")
      .config("spark.sql.catalog.spark_catalog.uri", Config.metastoreUri)
      .config("spark.sql.catalogImplementation", "hive")
      .config("spark.sql.warehouse.dir", Config.warehouse)
      .config("spark.hadoop.hive.metastore.uris", Config.metastoreUri)
      .config("spark.hadoop.hive.metastore.warehouse.dir", Config.warehouse)
      .config("spark.hadoop.fs.defaultFS", Config.hdfsUri)
      // El cliente vive en otro contenedor y debe alcanzar al DataNode por
      // nombre de red Docker, no por la IP interna que anuncia el NameNode.
      .config("spark.hadoop.dfs.client.use.datanode.hostname", "true")
      .config("spark.sql.shuffle.partitions", "4")
      .config("spark.ui.enabled", "false")
      .config("spark.ui.showConsoleProgress", "false")
      .enableHiveSupport()
      .getOrCreate()
    // Sin spark.sparkContext.setLogLevel: ese metodo castea el contexto de
    // log4j2 a su implementacion completa, y aqui log4j2 corre en su version
    // simple a proposito. El nivel de traza se fija por linea de comando en
    // ejecutar.sh, que es donde se decide como se ve esta pantalla.
    spark
  }

  private def espacios(spark: SparkSession): Unit = {
    Salida.titulo("Espacios que ve este proceso en el Metastore")
    val filas = spark.sql("SHOW DATABASES").collect().map(f => Seq(f.getString(0)))
    Salida.tabla(Seq("espacio"), filas.toSeq)
  }

  private def tablaEnElPresente(spark: SparkSession): DataFrame = {
    val datos = spark.table(Config.nombreCompleto).orderBy("rut")
    Salida.titulo(s"Tabla ${Config.nombreCompleto} en el presente")
    imprimir(datos)
    datos
  }

  private def paginasDeLaLibreta(spark: SparkSession): Seq[Long] = {
    val consulta =
      s"""SELECT snapshot_id, committed_at, operation
         |FROM ${Config.nombreCompleto}.snapshots
         |ORDER BY committed_at""".stripMargin
    val paginas = spark.sql(consulta)
    Salida.titulo("Paginas de la libreta, de la mas antigua a la mas nueva")
    imprimir(paginas)
    paginas.collect().map(_.getLong(0)).toSeq
  }

  private def primeraPagina(spark: SparkSession, paginas: Seq[Long]): Unit = {
    if (paginas.isEmpty) {
      Salida.titulo("La tabla no tiene paginas, no hay pasado que leer")
      return
    }
    val primera = paginas.head
    Salida.titulo(s"La misma tabla en su primera pagina, la $primera")
    imprimir(
      spark.sql(
        s"SELECT * FROM ${Config.nombreCompleto} VERSION AS OF $primera ORDER BY rut"
      )
    )
  }

  /** Vuelca un DataFrame por el impresor propio, no por el show() de Spark. */
  private def imprimir(datos: DataFrame): Unit = {
    val encabezados = datos.columns.toSeq
    val filas = datos.collect().toSeq.map { fila =>
      encabezados.indices.map { i =>
        val valor = fila.get(i)
        if (valor == null) "" else valor.toString
      }
    }
    Salida.tabla(encabezados, filas)
  }
}
