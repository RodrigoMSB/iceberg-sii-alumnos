# Laboratorio 08. Dejar la libreta ordenada

Cada celda lleva `%%sql` en la primera línea y una sola sentencia por celda.

## Paso 0. Un año de ingesta, mes a mes

**Celda 0.1**

**Se escribe**

```sql
USE mi_espacio
```

**En consola** `Listo. La sentencia se ejecutó.`

**Cambia en tu corrida** nada.

---

**Celda 0.2**

**Se escribe**

```sql
DROP TABLE IF EXISTS documentos_recibidos
```

**En consola** `Listo. La sentencia se ejecutó.`

**Cambia en tu corrida** nada.

---

**Celda 0.3**

**Se escribe**

```sql
CREATE TABLE documentos_recibidos USING iceberg AS
SELECT * FROM curso.dte_2024
WHERE month(fecha_emision) = 1
```

**En consola** `Listo. La sentencia se ejecutó.`

**Cambia en tu corrida** nada.

---

**Celda 0.4**

**Se escribe**

```sql
INSERT INTO documentos_recibidos
SELECT * FROM curso.dte_2024
WHERE month(fecha_emision) = 2
```

**En consola** `Listo. La sentencia se ejecutó.`

**Cambia en tu corrida** nada.

---

**Celda 0.5**

**Se escribe**

```sql
INSERT INTO documentos_recibidos
SELECT * FROM curso.dte_2024
WHERE month(fecha_emision) = 3
```

**En consola** `Listo. La sentencia se ejecutó.`

**Cambia en tu corrida** nada.

---

**Celda 0.6**

**Se escribe**

```sql
INSERT INTO documentos_recibidos
SELECT * FROM curso.dte_2024
WHERE month(fecha_emision) = 4
```

**En consola** `Listo. La sentencia se ejecutó.`

**Cambia en tu corrida** nada.

---

**Celda 0.7**

**Se escribe**

```sql
INSERT INTO documentos_recibidos
SELECT * FROM curso.dte_2024
WHERE month(fecha_emision) = 5
```

**En consola** `Listo. La sentencia se ejecutó.`

**Cambia en tu corrida** nada.

---

**Celda 0.8**

**Se escribe**

```sql
INSERT INTO documentos_recibidos
SELECT * FROM curso.dte_2024
WHERE month(fecha_emision) = 6
```

**En consola** `Listo. La sentencia se ejecutó.`

**Cambia en tu corrida** nada.

---

**Celda 0.9**

**Se escribe**

```sql
INSERT INTO documentos_recibidos
SELECT * FROM curso.dte_2024
WHERE month(fecha_emision) = 7
```

**En consola** `Listo. La sentencia se ejecutó.`

**Cambia en tu corrida** nada.

---

**Celda 0.10**

**Se escribe**

```sql
INSERT INTO documentos_recibidos
SELECT * FROM curso.dte_2024
WHERE month(fecha_emision) = 8
```

**En consola** `Listo. La sentencia se ejecutó.`

**Cambia en tu corrida** nada.

---

**Celda 0.11**

**Se escribe**

```sql
INSERT INTO documentos_recibidos
SELECT * FROM curso.dte_2024
WHERE month(fecha_emision) = 9
```

**En consola** `Listo. La sentencia se ejecutó.`

**Cambia en tu corrida** nada.

---

**Celda 0.12**

**Se escribe**

```sql
INSERT INTO documentos_recibidos
SELECT * FROM curso.dte_2024
WHERE month(fecha_emision) = 10
```

**En consola** `Listo. La sentencia se ejecutó.`

**Cambia en tu corrida** nada.

---

**Celda 0.13**

**Se escribe**

```sql
INSERT INTO documentos_recibidos
SELECT * FROM curso.dte_2024
WHERE month(fecha_emision) = 11
```

**En consola** `Listo. La sentencia se ejecutó.`

**Cambia en tu corrida** nada.

---

**Celda 0.14**

**Se escribe**

```sql
INSERT INTO documentos_recibidos
SELECT * FROM curso.dte_2024
WHERE month(fecha_emision) = 12
```

**En consola** `Listo. La sentencia se ejecutó.`

**Cambia en tu corrida** nada.

---

**Celda 0.15**

**Se escribe**

```sql
SELECT count(*)         AS documentos,
       sum(monto_total) AS total_general
FROM documentos_recibidos
```

**En consola** una fila.

```
documentos | total_general
30000      | 291293351462.71
```

**Cambia en tu corrida** nada.

## Paso 1. Medir el costo

**Celda 1.1**

**Se escribe**

```sql
SELECT count(*)                                AS archivos,
       sum(record_count)                        AS documentos,
       cast(avg(file_size_in_bytes) AS BIGINT)  AS bytes_por_archivo,
       sum(file_size_in_bytes)                  AS bytes_totales
FROM mi_espacio.documentos_recibidos.files
```

**En consola** una fila.

```
archivos | documentos | bytes_por_archivo | bytes_totales
12       | 30000      | 74031             | 888378
```

**Cambia en tu corrida** nada.

---

**Celda 1.2**

**Se escribe**

```sql
SELECT record_count                                  AS documentos,
       file_size_in_bytes                            AS bytes,
       readable_metrics.fecha_emision.lower_bound    AS desde,
       readable_metrics.fecha_emision.upper_bound    AS hasta
FROM mi_espacio.documentos_recibidos.files
ORDER BY desde
```

**En consola** doce filas, una por archivo, todas con 2.500 documentos y entre 73.000 y
74.500 bytes.

**Cambia en tu corrida** nada.

---

**Celda 1.3**

**Se escribe**

```sql
SELECT date_format(fecha_emision, 'yyyy-MM') AS periodo,
       count(*)                             AS documentos,
       sum(monto_total)                     AS total_del_periodo
FROM documentos_recibidos
GROUP BY date_format(fecha_emision, 'yyyy-MM')
ORDER BY periodo
```

**En consola** doce filas, de `2024-01` a `2024-12`, con 2.500 documentos cada una.

**Cambia en tu corrida** nada.

## Paso 2. Pasar en limpio

**Celda 2.1**

**Se escribe**

```sql
CALL spark_catalog.system.rewrite_data_files(table => 'mi_espacio.documentos_recibidos')
```

**En consola** una fila con el recibo de lo que hizo.

```
rewritten_data_files_count | added_data_files_count | rewritten_bytes_count
12                         | 1                      | 888378
```

**Cambia en tu corrida** nada.

---

**Celda 2.2**

**Se escribe**

```sql
SELECT count(*)                                AS archivos,
       sum(record_count)                        AS documentos,
       cast(avg(file_size_in_bytes) AS BIGINT)  AS bytes_por_archivo,
       sum(file_size_in_bytes)                  AS bytes_totales
FROM mi_espacio.documentos_recibidos.files
```

**En consola** una fila.

```
archivos | documentos | bytes_por_archivo | bytes_totales
1        | 30000      | 762542            | 762542
```

**Cambia en tu corrida** el tamaño, en algunos cientos de bytes.

---

**Celda 2.3**

**Se escribe**

```sql
SELECT count(*)         AS documentos,
       sum(monto_total) AS total_general
FROM documentos_recibidos
```

**En consola** la misma fila del paso 0, idéntica.

```
documentos | total_general
30000      | 291293351462.71
```

**Cambia en tu corrida** nada.

## Paso 3. Lo que no se liberó

**Celda 3.1**

**Se escribe**

```sql
SELECT snapshot_id, committed_at, operation
FROM mi_espacio.documentos_recibidos.snapshots
ORDER BY committed_at
```

**En consola** **trece filas**.

**Cambia en tu corrida** `snapshot_id` y `committed_at`.

---

**Celda 3.2**

**Se escribe**

```sql
SELECT count(*) AS documentos FROM documentos_recibidos VERSION AS OF <TU_SNAPSHOT_ID>
```

**En consola** una fila con **2.500** documentos.

**Cambia en tu corrida** el número que escribiste; el resultado, 2.500, es siempre el mismo.

---

**Celda 3.3**

**Se escribe**

```sql
SELECT count(*)               AS archivos_guardados,
       sum(file_size_in_bytes) AS bytes_ocupados
FROM mi_espacio.documentos_recibidos.all_data_files
```

**En consola** una fila.

```
archivos_guardados | bytes_ocupados
13                 | 1650920
```

**Cambia en tu corrida** los `bytes_ocupados`, en algunos cientos, por lo mismo de la celda anterior. Los `archivos_guardados` son siempre 13.

## Paso 4. Botar los borradores

**Celda 4.1**

**Se escribe**

```sql
CALL spark_catalog.system.expire_snapshots(
    table       => 'mi_espacio.documentos_recibidos',
    older_than  => TIMESTAMP '<TU_ULTIMO_COMMITTED_AT>',
    retain_last => 1)
```

**En consola** una fila con el recibo de lo que se botó.

```
deleted_data_files_count | ... | deleted_manifest_files_count | deleted_manifest_lists_count | ...
12                       |     | 12                           | 12                           |
```

**Cambia en tu corrida** la marca de tiempo que escribiste.

---

**Celda 4.2**

**Se escribe**

```sql
SELECT count(*) AS documentos FROM documentos_recibidos VERSION AS OF <TU_SNAPSHOT_ID>
```

**En consola** el aviso rojo de la magia.

```
Spark rechazó la sentencia:

Cannot find snapshot with ID <el número que copiaste>
```

**Cambia en tu corrida** el identificador que aparece en el mensaje.

---

**Celda 4.3**

**Se escribe**

```sql
SELECT snapshot_id, committed_at, operation
FROM mi_espacio.documentos_recibidos.snapshots
ORDER BY committed_at
```

**En consola** **una sola fila**, la `replace` de la compactación.

**Cambia en tu corrida** el `snapshot_id` y la marca de tiempo.

---

**Celda 4.4**

**Se escribe**

```sql
SELECT count(*)               AS archivos_guardados,
       sum(file_size_in_bytes) AS bytes_ocupados
FROM mi_espacio.documentos_recibidos.all_data_files
```

**En consola** una fila.

```
archivos_guardados | bytes_ocupados
1                  | 762542
```

**Cambia en tu corrida** nada; los bytes son los mismos que salieron en la celda del paso 2.

---

**Celda 4.5**

**Se escribe**

```sql
SELECT count(*)         AS documentos,
       sum(monto_total) AS total_general
FROM documentos_recibidos
```

**En consola** la misma fila del paso 0 y del paso 2.

```
documentos | total_general
30000      | 291293351462.71
```

**Cambia en tu corrida** nada.

## Paso 5. Los archivos que nadie reclama

**Celda 5.1**

**Se escribe**

```sql
CALL spark_catalog.system.remove_orphan_files(
    table   => 'mi_espacio.documentos_recibidos',
    dry_run => true)
```

**En consola** la tabla vacía, con la columna `orphan_file_location` y el aviso `0
filas`.

**Cambia en tu corrida** nada.

---

**Celda 5.2**

**Se escribe**

```sql
CALL spark_catalog.system.remove_orphan_files(
    table      => 'mi_espacio.documentos_recibidos',
    older_than => TIMESTAMP '<TU_ULTIMO_COMMITTED_AT>',
    dry_run    => true)
```

**En consola** el aviso rojo.

```
Cannot remove orphan files with an interval less than 24 hours. Executing this
procedure with a short interval may corrupt the table if other operations are
happening at the same time...
```

**Cambia en tu corrida** la marca de tiempo que escribiste.

## Paso 6. La rutina (conversación, sin celdas)

**Se escribe** nada.

**En consola** nada.

**Cambia en tu corrida** nada.

## Paso 7. Cerrar el curso (conversación, sin celdas)

**Se escribe** nada.

**En consola** nada.

**Cambia en tu corrida** nada.