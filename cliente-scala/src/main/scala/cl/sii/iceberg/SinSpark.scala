package cl.sii.iceberg

import java.time.Instant
import java.time.ZoneOffset
import java.time.format.DateTimeFormatter
import java.util.UUID
import java.util.function.{Function => FuncionJava}

import scala.collection.JavaConverters._

import org.apache.hadoop.conf.Configuration
import org.apache.iceberg.PartitionSpec
import org.apache.iceberg.catalog.TableIdentifier
import org.apache.iceberg.data.{GenericRecord, IcebergGenerics, Record}
import org.apache.iceberg.data.parquet.GenericParquetWriter
import org.apache.iceberg.expressions.Expressions
import org.apache.iceberg.hive.HiveCatalog
import org.apache.iceberg.io.CloseableIterable
import org.apache.iceberg.parquet.{Parquet, ParquetValueWriter}
import org.apache.parquet.schema.MessageType

/**
 * La misma tabla, sin Spark en ninguna parte.
 *
 * Este jar no lleva Spark adentro y esa ausencia es el punto: una tabla
 * Iceberg es un directorio de archivos Parquet mas unos indices que dicen
 * cuales cuentan, y cualquier programa que sepa leer ese formato la lee. No
 * hace falta el motor que la escribio, ni ningun servidor que preste el dato.
 *
 * Se lee de arriba abajo, en cinco pasos numerados, y cada cosa se crea en el
 * paso anterior al que la usa. Es lo que el alumno tiene delante en el
 * laboratorio 09: esto es exactamente lo que corre el jar.
 */
object SinSpark {

  def main(argumentos: Array[String]): Unit = {

    // El espacio y la tabla los pone quien lanza el programa, nunca este
    // archivo: cada alumno corre la celda con el suyo, y si el nombre viniera
    // escrito aqui, todos leerian y escribirian en la tabla del mismo.
    val espacio = sys.env.getOrElse("ESPACIO", "")
    val tabla = sys.env.getOrElse("TABLA", "")
    if (espacio.isEmpty || tabla.isEmpty) {
      println("Faltan las variables ESPACIO y TABLA. El programa se lanza asi:")
      println("  ESPACIO=mi_espacio TABLA=contribuyentes_lab09 java -jar sin-spark.jar")
      return
    }
    println(s"Tabla pedida: $espacio.$tabla")

    // 1. Decirle donde esta HDFS. La direccion es la misma en los siete espacios.
    val hadoop = new Configuration()
    hadoop.set("fs.defaultFS", "hdfs://namenode:8020")
    hadoop.set("dfs.client.use.datanode.hostname", "true")
    hadoop.set("hive.metastore.uris", "thrift://hive-metastore:9083")
    println()
    println("1. HDFS en hdfs://namenode:8020")

    // 2. Conectarse al catalogo, que es el clavo del que cuelga la libreta.
    val catalogo = new HiveCatalog()
    catalogo.setConf(hadoop)
    catalogo.initialize("laboratorio", Map(
      "uri" -> "thrift://hive-metastore:9083",
      "warehouse" -> "hdfs://namenode:8020/warehouse/iceberg").asJava)
    println("2. Catalogo Hive en thrift://hive-metastore:9083")

    // 3. Pedir la tabla. Esto lee la portada y todavia ningun dato.
    val libreta = catalogo.loadTable(TableIdentifier.of(espacio, tabla))
    val reloj = DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss.SSS").withZone(ZoneOffset.UTC)
    val paginas = libreta.snapshots().asScala.toSeq.sortBy(_.timestampMillis())
    println()
    println("3. Portada leida. Columnas: " +
      libreta.schema().columns().asScala.map(_.name()).mkString(", "))
    println("   Paginas de la libreta, en hora UTC, igual que .snapshots:")
    paginas.foreach(pagina => println("   %s   %s   %s".format(
      pagina.snapshotId(),
      reloj.format(Instant.ofEpochMilli(pagina.timestampMillis())),
      pagina.operation())))

    // 4. Leer las filas de la pagina vigente y de la primera pagina.
    def mostrar(titulo: String, registros: CloseableIterable[Record]): Unit = {
      println("   " + titulo)
      try {
        val filas = registros.asScala.toSeq.map(registro => "   %-12s %-26s %s".format(
          registro.getField("rut"), registro.getField("razon_social"),
          registro.getField("segmento")))
        filas.sorted.foreach(println)
        println("   %d filas".format(filas.size))
      } finally registros.close()
    }
    println()
    println("4. Las filas, leidas registro a registro y sin motor de consultas.")
    mostrar("Pagina vigente:", IcebergGenerics.read(libreta).build())
    if (paginas.nonEmpty) {
      val primera = paginas.head.snapshotId()
      mostrar(s"Primera pagina, la $primera:",
        IcebergGenerics.read(libreta).useSnapshot(primera).build())
    }

    // 5. Escribir la fila de Litre Transportes: el Parquet, el indice y el commit.
    val rut = "79856201-3"
    val buscado = IcebergGenerics.read(libreta).where(Expressions.equal("rut", rut)).build()
    val yaEsta = try buscado.iterator().hasNext finally buscado.close()
    println()
    if (yaEsta) {
      println(s"5. El contribuyente $rut ya estaba en la tabla. No se escribe de nuevo.")
      println("   Esta celda se puede correr las veces que quieras.")
    } else {
      val registro = GenericRecord.create(libreta.schema())
      registro.setField("rut", rut)
      registro.setField("razon_social", "Litre Transportes SpA")
      registro.setField("segmento", "MICRO")
      val destino = libreta.io().newOutputFile(
        libreta.locationProvider().newDataLocation(s"sin-spark-${UUID.randomUUID()}.parquet"))
      val escritor = Parquet.writeData(destino)
        .schema(libreta.schema())
        .createWriterFunc(new FuncionJava[MessageType, ParquetValueWriter[_]] {
          override def apply(tipo: MessageType): ParquetValueWriter[_] =
            GenericParquetWriter.buildWriter(tipo)
        })
        .withSpec(PartitionSpec.unpartitioned())
        .overwrite()
        .build[Record]()
      try escritor.write(registro) finally escritor.close()
      println(s"5. Parquet escrito: ${destino.location()}")
      libreta.newAppend().appendFile(escritor.toDataFile).commit()
      libreta.refresh()
      println(s"   Indice de esa pagina: ${libreta.currentSnapshot().manifestListLocation()}")
      println(s"   Commit hecho. Pagina nueva ${libreta.currentSnapshot().snapshotId()}.")
    }

    println()
    println("Fin. Ni la lectura ni la escritura pasaron por Spark. No hay Spark en este jar.")
  }
}
