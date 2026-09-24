package cl.sii.iceberg

import java.time.ZoneId

/**
 * Lo que el cliente necesita saber del laboratorio, y de donde lo saca.
 *
 * Todo entra por variables de entorno y todo tiene un valor por omision que
 * apunta al laboratorio tal como esta hoy. Asi el mi_espacio lanza el contenedor
 * sin argumentos y funciona; y si algun dia cambia un puerto, cambia la
 * variable y no el codigo.
 *
 * Los nombres por omision son los de contenedor (hive-metastore,
 * namenode), que este repositorio declara como contrato publico. Dentro de
 * la red los nombres de servicio (hive-metastore, namenode) resuelven a la
 * misma direccion, asi que los dos sirven.
 */
object Config {

  private def variable(nombre: String, porOmision: String): String =
    sys.env.get(nombre).filter(_.trim.nonEmpty).getOrElse(porOmision)

  val metastoreUri: String = variable("METASTORE_URI", "thrift://hive-metastore:9083")
  val hdfsUri: String      = variable("HDFS_URI", "hdfs://namenode:8020")
  val warehouse: String    = variable("WAREHOUSE", s"$hdfsUri/warehouse/iceberg")
  val espacio: String      = variable("ESPACIO", "mi_espacio")
  val tabla: String        = variable("TABLA", "contribuyentes_lab01")

  /**
   * La zona en que se muestran las marcas de tiempo.
   *
   * Tiene que ser la MISMA que usa la sesion Spark del laboratorio o los dos
   * programas muestran horas distintas para el mismo snapshot, y entonces la
   * demostracion de que estan viendo la misma tabla se cae sola.
   *
   * El laboratorio no fija spark.sql.session.timeZone, asi que Spark toma la
   * zona por omision de su JVM, y los contenedores del ambiente corren en
   * Etc/UTC. Este contenedor tambien, asi que basta con preguntarle a la JVM
   * en vez de escribir una zona a mano. Se comprueba con
   *
   *     SET spark.sql.session.timeZone
   *
   * contra el Thrift Server del laboratorio. ZONA_HORARIA existe por si algun
   * dia el ambiente fija esa propiedad a otra cosa.
   */
  val zonaHoraria: ZoneId =
    sys.env.get("ZONA_HORARIA").filter(_.trim.nonEmpty).map(ZoneId.of).getOrElse(ZoneId.systemDefault())

  /** El nombre a dos partes, que es como se nombra la tabla en una consulta. */
  val nombreCompleto: String = s"$espacio.$tabla"

  def imprimirEncabezado(programa: String): Unit = {
    Salida.titulo(s"Cliente Scala del laboratorio, modo $programa")
    Salida.tabla(
      Seq("ajuste", "valor"),
      Seq(
        Seq("metastore", metastoreUri),
        Seq("hdfs", hdfsUri),
        Seq("warehouse", warehouse),
        Seq("tabla", nombreCompleto),
        Seq("zona horaria", zonaHoraria.toString),
      ),
      contarFilas = false,
    )
  }
}

/**
 * Impresion alineada, pensada para proyector.
 *
 * No se usa el show() de Spark porque dibuja marcos con guiones y el material
 * del curso va sin rayas. Y porque SinSpark no tiene Spark con que dibujar,
 * asi que los dos programas tienen que imprimir igual para que la comparacion
 * en pantalla sea honesta.
 */
object Salida {

  private val separacion = 3

  def titulo(texto: String): Unit = {
    println()
    println(texto)
  }

  def linea(texto: String): Unit = println(texto)

  def tabla(encabezados: Seq[String], filas: Seq[Seq[String]], contarFilas: Boolean = true): Unit = {
    if (filas.isEmpty) {
      println("sin filas")
      return
    }
    val anchos = encabezados.indices.map { columna =>
      (encabezados(columna).length +: filas.map(fila => celda(fila, columna).length)).max
    }
    def formatear(celdas: Seq[String]): String =
      celdas.indices
        .map(i => celdas(i).padTo(anchos(i) + separacion, ' '))
        .mkString
        .replaceAll("\\s+$", "")

    println(formatear(encabezados))
    filas.foreach(fila => println(formatear(encabezados.indices.map(celda(fila, _)))))
    if (contarFilas) println(if (filas.size == 1) "1 fila" else s"${filas.size} filas")
  }

  private def celda(fila: Seq[String], columna: Int): String =
    if (columna < fila.length && fila(columna) != null) fila(columna) else ""
}
