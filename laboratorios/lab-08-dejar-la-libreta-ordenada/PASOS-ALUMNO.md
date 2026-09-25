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
| documentos | total_general   |
| 30000      | 291293351462.71 |
1 fila.
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
| archivos | documentos | bytes_por_archivo | bytes_totales |
| 12       | 30000      | 74031             | 888378        |
1 fila.
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

```
| documentos | bytes | desde      | hasta      |
| 2500       | 73189 | 2024-01-01 | 2024-01-31 |
| 2500       | 73627 | 2024-02-01 | 2024-02-29 |
| 2500       | 73442 | 2024-03-01 | 2024-03-31 |
| 2500       | 74229 | 2024-04-01 | 2024-04-30 |
| 2500       | 73711 | 2024-05-01 | 2024-05-31 |
| 2500       | 74192 | 2024-06-01 | 2024-06-30 |
| 2500       | 74452 | 2024-07-01 | 2024-07-31 |
| 2500       | 74327 | 2024-08-01 | 2024-08-31 |
| 2500       | 74232 | 2024-09-01 | 2024-09-30 |
| 2500       | 74333 | 2024-10-01 | 2024-10-31 |
| 2500       | 74467 | 2024-11-01 | 2024-11-30 |
| 2500       | 74177 | 2024-12-01 | 2024-12-31 |
12 filas.
```

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

```
| periodo | documentos | total_del_periodo |
| 2024-01 | 2500       | 23381729910.07    |
| 2024-02 | 2500       | 24831948613.59    |
| 2024-03 | 2500       | 26699931432.64    |
| 2024-04 | 2500       | 23722997990.55    |
| 2024-05 | 2500       | 24328007216.84    |
| 2024-06 | 2500       | 24547341762.59    |
| 2024-07 | 2500       | 23621609483.83    |
| 2024-08 | 2500       | 23648615665.89    |
| 2024-09 | 2500       | 24136964210.51    |
| 2024-10 | 2500       | 23106058024.78    |
| 2024-11 | 2500       | 24722608269.83    |
| 2024-12 | 2500       | 24545538881.59    |
12 filas.
```

**Cambia en tu corrida** nada.

## Paso 2. Pasar en limpio

**Celda 2.1**

**Se escribe**

```sql
CALL spark_catalog.system.rewrite_data_files(table => 'mi_espacio.documentos_recibidos')
```

**En consola** una fila con el recibo de lo que hizo.

```
| rewritten_data_files_count | added_data_files_count | rewritten_bytes_count |
| 12                         | 1                      | 888378                |
1 fila.
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
| archivos | documentos | bytes_por_archivo | bytes_totales |
| 1        | 30000      | 761212            | 761212        |
1 fila.
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
| documentos | total_general   |
| 30000      | 291293351462.71 |
1 fila.
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

```
| snapshot_id         | committed_at            | operation |
| 7561399047907185895 | 2026-09-25 18:24:05.778 | append    |
| 5013964436874795132 | 2026-09-25 18:24:06.939 | append    |
| 5605958553486786000 | 2026-09-25 18:24:08.367 | append    |
| 1802040594104167461 | 2026-09-25 18:24:09.361 | append    |
| 1009743359021141391 | 2026-09-25 18:24:10.738 | append    |
| 2700393237366741854 | 2026-09-25 18:24:12.531 | append    |
| 4370442779747130215 | 2026-09-25 18:24:13.891 | append    |
| 3256189979838852168 | 2026-09-25 18:24:15.136 | append    |
| 1041927787630357096 | 2026-09-25 18:24:16.432 | append    |
| 17116443147193272   | 2026-09-25 18:24:17.391 | append    |
| 5355173705741653654 | 2026-09-25 18:24:18.644 | append    |
| 5991328770865681656 | 2026-09-25 18:24:19.063 | append    |
| 7875847062182413290 | 2026-09-25 18:24:24.762 | replace   |
13 filas.
```

**Cambia en tu corrida** `snapshot_id` y `committed_at`.

---

**Celda 3.2**

**Se escribe**

```sql
SELECT count(*) AS documentos FROM documentos_recibidos VERSION AS OF <TU_SNAPSHOT_ID>
```

**En consola** una fila con **2.500** documentos.

```
| documentos |
| 2500       |
1 fila.
```

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
| archivos_guardados | bytes_ocupados |
| 13                 | 1649590        |
1 fila.
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
| deleted_data_files_count | deleted_position_delete_files_count | deleted_equality_delete_files_count | deleted_manifest_files_count | deleted_manifest_lists_count | deleted_statistics_files_count |
| 12                       | 0                                   | 0                                   | 12                           | 12                           | 0                              |
1 fila.
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

Cannot find snapshot with ID 7561399047907185895
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

```
| snapshot_id         | committed_at            | operation |
| 7875847062182413290 | 2026-09-25 18:24:24.762 | replace   |
1 fila.
```

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
| archivos_guardados | bytes_ocupados |
| 1                  | 761212         |
1 fila.
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
| documentos | total_general   |
| 30000      | 291293351462.71 |
1 fila.
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

```
| orphan_file_location |
0 filas.
```

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
Spark rechazó la sentencia:

Cannot remove orphan files with an interval less than 24 hours. Executing this procedure with a short interval may corrupt the table if other operations are happening at the same time. If you are absolutely confident that no concurrent operations will be affected by removing orphan files with such a short interval, you can use the Action API to remove orphan files with an arbitrary interval.
```

**Cambia en tu corrida** la marca de tiempo que escribiste.

## Paso 6. La rutina (conversación, sin celdas)

**Se escribe** nada.

**En consola** nada.

**Cambia en tu corrida** nada.

## Paso 7. Las preguntas que quedaron abiertas (sin celdas)

**Se escribe** nada.

**En consola** nada.

**Cambia en tu corrida** nada.