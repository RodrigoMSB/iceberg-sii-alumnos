# Laboratorio 11. El disco lleno

Cada celda lleva `%%sql` en la primera línea y una sola sentencia por celda.

## Paso 0. Un año de documentos

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
DROP TABLE IF EXISTS documentos_lab11
```

**En consola** `Listo. La sentencia se ejecutó.`

**Varía entre alumnos** nada.

---

**Celda 0.3**

**Se escribe**

```sql
CREATE TABLE documentos_lab11 USING iceberg AS
SELECT * FROM curso.dte_2024
```

**En consola** `Listo. La sentencia se ejecutó.` Es de las celdas más lentas, unos
segundos.

**Varía entre alumnos** nada.

## Paso 1. Medir el disco

**Celda 1.1**

**Se escribe** (con su propia database).

```sql
SELECT count(*)                AS archivos_vigentes,
       sum(file_size_in_bytes) AS bytes_vigentes
FROM mi_espacio.documentos_lab11.files
```

**En consola** un archivo.

```
| archivos_vigentes | bytes_vigentes |
| 1                 | 776514         |
```

**Varía entre alumnos** los bytes varían en unos cientos, porque la compresión depende
del orden en que el motor leyó las filas.

---

**Celda 1.2**

**Se escribe** (con su espacio en la ruta).

```
!hdfs dfs -du -s /warehouse/iceberg/mi_espacio.db/documentos_lab11
```

**En consola** dos números y la ruta.

```
790808  2372424  /warehouse/iceberg/mi_espacio.db/documentos_lab11
```

**Varía entre alumnos** los dos números, en unos cientos de bytes.

---

**Se escribe** nada.

**En consola** nada.

**Varía entre alumnos** nada.

## Paso 2. Cinco correcciones

**Celda 2.1**

**Se escribe**

```sql
UPDATE documentos_lab11 SET estado_sii = 'REVISADO'
WHERE tipo_dte = 33 AND fecha_emision BETWEEN DATE '2024-01-01' AND DATE '2024-01-31'
```

**En consola** `Listo. La sentencia se ejecutó.`

**Varía entre alumnos** nada.

---

**Celda 2.2**

**Se escribe**

```sql
UPDATE documentos_lab11 SET estado_sii = 'REVISADO'
WHERE tipo_dte = 33 AND fecha_emision BETWEEN DATE '2024-02-01' AND DATE '2024-02-29'
```

**En consola** `Listo. La sentencia se ejecutó.`

**Varía entre alumnos** nada.

---

**Celda 2.3**

**Se escribe**

```sql
UPDATE documentos_lab11 SET estado_sii = 'REVISADO'
WHERE tipo_dte = 33 AND fecha_emision BETWEEN DATE '2024-03-01' AND DATE '2024-03-31'
```

**En consola** `Listo. La sentencia se ejecutó.`

**Varía entre alumnos** nada.

---

**Celda 2.4**

**Se escribe**

```sql
UPDATE documentos_lab11 SET estado_sii = 'REVISADO'
WHERE tipo_dte = 33 AND fecha_emision BETWEEN DATE '2024-04-01' AND DATE '2024-04-30'
```

**En consola** `Listo. La sentencia se ejecutó.`

**Varía entre alumnos** nada.

---

**Celda 2.5**

**Se escribe**

```sql
UPDATE documentos_lab11 SET estado_sii = 'REVISADO'
WHERE tipo_dte = 33 AND fecha_emision BETWEEN DATE '2024-05-01' AND DATE '2024-05-31'
```

**En consola** `Listo. La sentencia se ejecutó.`

**Varía entre alumnos** nada.

---

**Celda 2.6**

**Se escribe**

```sql
SELECT count(*) AS documentos FROM documentos_lab11
```

**En consola**

```
| documentos |
| 30000      |
```

**Varía entre alumnos** nada.

---

**Celda 2.7**

**Se escribe** (con su espacio en la ruta).

```
!hdfs dfs -du -s /warehouse/iceberg/mi_espacio.db/documentos_lab11
```

**En consola**

```
4804920  14414760  /warehouse/iceberg/mi_espacio.db/documentos_lab11
```

**Varía entre alumnos** los números, en algunos miles.

## Paso 3. Dónde se fue el espacio

**Celda 3.1**

**Se escribe** (con su propia database).

```sql
SELECT snapshot_id, committed_at, operation
FROM mi_espacio.documentos_lab11.snapshots
ORDER BY committed_at
```

**En consola** seis filas, la primera `append` y las cinco siguientes `overwrite`.

```
| snapshot_id         | committed_at            | operation |
| 7067726178500278946 | 2026-09-15 20:19:09.516 | append    |
| 1789935202663888754 | 2026-09-15 20:19:16.565 | overwrite |
| 17782665461576858   | 2026-09-15 20:19:18.863 | overwrite |
| 6126750899679552327 | 2026-09-15 20:19:20.301 | overwrite |
| 3971060320449625847 | 2026-09-15 20:19:21.616 | overwrite |
| 4171071182007391995 | 2026-09-15 20:19:23.597 | overwrite |
6 filas.
```

**Varía entre alumnos** los identificadores y las fechas.

---

**Celda 3.2**

**Se escribe** (con su propia database).

```sql
SELECT
    (SELECT count(*)                FROM mi_espacio.documentos_lab11.files)     AS archivos_vigentes,
    (SELECT sum(file_size_in_bytes) FROM mi_espacio.documentos_lab11.files)     AS bytes_vigentes,
    (SELECT count(*)                FROM mi_espacio.documentos_lab11.all_files) AS archivos_todos,
    (SELECT sum(file_size_in_bytes) FROM mi_espacio.documentos_lab11.all_files) AS bytes_todos
```

**En consola** un archivo vigente contra seis en total.

```
| archivos_vigentes | bytes_vigentes | archivos_todos | bytes_todos |
| 1                 | 778984         | 6              | 4668576     |
```

**Varía entre alumnos** los bytes.

## Paso 4. Botar las páginas viejas

**Celda 4.1**

**Se escribe** (con su propia database).

```sql
CALL spark_catalog.system.expire_snapshots(
    table       => 'mi_espacio.documentos_lab11',
    older_than  => TIMESTAMP '2030-01-01 00:00:00',
    retain_last => 1
)
```

**En consola** una fila con lo que borró, cinco archivos de datos entre ellos.

**Varía entre alumnos** los conteos de manifiestos.

---

**Celda 4.2**

**Se escribe** (con su espacio en la ruta).

```
!hdfs dfs -du -s /warehouse/iceberg/mi_espacio.db/documentos_lab11
```

**En consola**

```
842260  2526780  /warehouse/iceberg/mi_espacio.db/documentos_lab11
```

**Varía entre alumnos** los números, en algunos miles.

---

**Celda 4.3**

**Se escribe**

```sql
SELECT count(*) AS documentos FROM documentos_lab11
```

**En consola**

```
| documentos |
| 30000      |
```

**Varía entre alumnos** nada.

## Paso 5. Los archivos que nadie reclama

**Celda 5.1**

**Se escribe** (con su propia database).

```sql
CALL spark_catalog.system.remove_orphan_files(
    table      => 'mi_espacio.documentos_lab11',
    older_than => TIMESTAMP '2026-09-01 00:00:00',
    dry_run    => true
)
```

**En consola** ninguna fila.

```
| orphan_file_location |
0 filas.
```

**Varía entre alumnos** nada.
