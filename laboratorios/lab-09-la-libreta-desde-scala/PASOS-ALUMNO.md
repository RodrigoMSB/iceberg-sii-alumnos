# Laboratorio 09. La libreta desde Scala

Cada celda lleva `%%sql` en la primera línea y una sola sentencia por celda.

## Paso 0. Qué vas a correr, y la libreta de hoy

**Celda 0.1**

**Se escribe** (cada uno el suyo).

```sql
USE mi_espacio
```

**En consola** `Listo. La sentencia se ejecutó.` Primera celda del día.

**Varía entre alumnos** el nombre que escribió cada uno.

---

**Celda 0.2**

**Se escribe**

```sql
DROP TABLE IF EXISTS contribuyentes_lab09
```

**En consola** `Listo. La sentencia se ejecutó.`

**Varía entre alumnos** nada.

---

**Celda 0.3**

**Se escribe**

```sql
CREATE TABLE contribuyentes_lab09 (
    rut           STRING,
    razon_social  STRING,
    segmento      STRING
) USING iceberg
```

**En consola** `Listo. La sentencia se ejecutó.`

**Varía entre alumnos** nada.

---

**Celda 0.4**

**Se escribe**

```sql
INSERT INTO contribuyentes_lab09 VALUES
    ('77746521-K', 'Pehuen Logistica EIRL',    'MICRO'),
    ('77884562-8', 'Araucaria Ferreteria SpA', 'PEQUENA'),
    ('78800840-6', 'Copihue Maquinarias EIRL', 'MEDIANA'),
    ('76171162-8', 'Huemul Alimentos EIRL',    'GRANDE')
```

**En consola** `Listo. La sentencia se ejecutó.`

**Varía entre alumnos** nada.

## Paso 1. El código, sin Spark

**Se escribe** nada.

**En consola** nada.

**Varía entre alumnos** nada.

---

**Se escribe** nada.

**En consola** nada.

**Varía entre alumnos** nada.

## Paso 2. Correrlo

**Celda 2.1**

**Se escribe** (con su espacio en los dos lugares).

```
!ESPACIO=mi_espacio TABLA=contribuyentes_lab09 java -jar /home/mi_espacio/sin-spark.jar
```

**En consola** los cinco pasos numerados del programa.

```
Tabla pedida: mi_espacio.contribuyentes_lab09

1. HDFS en hdfs://namenode:8020
2. Catalogo Hive en thrift://hive-metastore:9083

3. Portada leida. Columnas: rut, razon_social, segmento
   Paginas de la libreta, en hora UTC, igual que .snapshots:
   438635771283733634   2026-09-21 22:38:51.731   append

4. Las filas, leidas registro a registro y sin motor de consultas.
   Pagina vigente:
   76171162-8   Huemul Alimentos EIRL      GRANDE
   77746521-K   Pehuen Logistica EIRL      MICRO
   77884562-8   Araucaria Ferreteria SpA   PEQUENA
   78800840-6   Copihue Maquinarias EIRL   MEDIANA
   4 filas
   Primera pagina, la 438635771283733634:
   76171162-8   Huemul Alimentos EIRL      GRANDE
   77746521-K   Pehuen Logistica EIRL      MICRO
   77884562-8   Araucaria Ferreteria SpA   PEQUENA
   78800840-6   Copihue Maquinarias EIRL   MEDIANA
   4 filas

5. Parquet escrito: hdfs://namenode:8020/warehouse/iceberg/mi_espacio.db/contribuyentes_lab09/data/sin-spark-c3bcb01e-a619-47d6-9dbe-1f07142c0bdc.parquet
   Indice de esa pagina: hdfs://namenode:8020/warehouse/iceberg/mi_espacio.db/contribuyentes_lab09/metadata/snap-1956004222642998237-1-6c515f41-6493-4868-94db-5083021e9e71.avro
   Commit hecho. Pagina nueva 1956004222642998237.

Fin. Ni la lectura ni la escritura pasaron por Spark. No hay Spark en este jar.
```

**Varía entre alumnos** el nombre del espacio, los identificadores, las fechas y los
nombres de archivo.

## Paso 3. Comprobar en SQL

**Celda 3.1**

**Se escribe**

```sql
REFRESH TABLE contribuyentes_lab09
```

**En consola** `Listo. La sentencia se ejecutó.`

**Varía entre alumnos** nada.

---

**Celda 3.2**

**Se escribe**

```sql
SELECT * FROM contribuyentes_lab09 ORDER BY rut
```

**En consola** cinco filas.

```
| rut        | razon_social             | segmento |
| 76171162-8 | Huemul Alimentos EIRL    | GRANDE   |
| 77746521-K | Pehuen Logistica EIRL    | MICRO    |
| 77884562-8 | Araucaria Ferreteria SpA | PEQUENA  |
| 78800840-6 | Copihue Maquinarias EIRL | MEDIANA  |
| 79856201-3 | Litre Transportes SpA    | MICRO    |
5 filas.
```

**Varía entre alumnos** nada.

---

**Celda 3.3**

**Se escribe** (con su propia database).

```sql
SELECT snapshot_id, committed_at, operation
FROM mi_espacio.contribuyentes_lab09.snapshots
ORDER BY committed_at
```

**En consola** dos páginas.

```
| snapshot_id         | committed_at            | operation |
| 438635771283733634  | 2026-09-21 22:38:51.731 | append    |
| 1956004222642998237 | 2026-09-21 22:38:56.775 | append    |
2 filas.
```

**Varía entre alumnos** los dos identificadores y las dos fechas.

## Paso 4. Las dependencias

**Se escribe** nada.

**En consola** nada.

**Varía entre alumnos** nada.

## Paso 5. El mismo programa con Spark

**Se escribe** nada.

**En consola** nada.

**Varía entre alumnos** nada.
