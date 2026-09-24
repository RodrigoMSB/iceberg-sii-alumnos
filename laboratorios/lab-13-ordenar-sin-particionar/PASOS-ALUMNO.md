# Laboratorio 13. Ordenar sin particionar

Cada celda lleva `%%sql` en la primera línea y una sola sentencia por celda.

## Paso 0. Una tabla ordenada, sin particiones

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
DROP TABLE IF EXISTS documentos_lab13
```

**En consola** `Listo. La sentencia se ejecutó.`

**Varía entre alumnos** nada.

---

**Celda 0.3**

**Se escribe**

```sql
CREATE TABLE documentos_lab13 USING iceberg AS
SELECT * FROM curso.dte_2024
ORDER BY fecha_emision
```

**En consola** `Listo. La sentencia se ejecutó.` Es de las celdas más lentas del
laboratorio, unos segundos, porque además ordena.

**Varía entre alumnos** nada.

---

**Celda 0.4**

**Se escribe**

```sql
SELECT count(*) AS documentos FROM documentos_lab13
```

**En consola**

```
| documentos |
| 30000      |
```

**Varía entre alumnos** nada.

---

**Celda 0.5**

**Se escribe** (con su propia database).

```sql
SELECT record_count                                AS filas,
       readable_metrics.fecha_emision.lower_bound AS desde,
       readable_metrics.fecha_emision.upper_bound AS hasta
FROM mi_espacio.documentos_lab13.files
ORDER BY desde
```

**En consola** una sola fila.

```
| filas | desde      | hasta      |
| 30000 | 2024-01-01 | 2024-12-31 |
1 fila.
```

**Varía entre alumnos** nada.

## Paso 1. Partirla en varios archivos

**Celda 1.1**

**Se escribe** (con su propia database).

```sql
CALL spark_catalog.system.rewrite_data_files(
    table      => 'mi_espacio.documentos_lab13',
    strategy   => 'sort',
    sort_order => 'fecha_emision ASC NULLS LAST',
    options    => map('target-file-size-bytes', '250000',
                      'min-input-files',        '1',
                      'rewrite-all',            'true')
)
```

**En consola** una fila con lo que reescribió, un archivo leído y nueve escritos.

**Varía entre alumnos** los bytes, en algunos miles.

---

**Celda 1.2**

**Se escribe** (con su propia database).

```sql
SELECT record_count                                AS filas,
       readable_metrics.fecha_emision.lower_bound AS desde,
       readable_metrics.fecha_emision.upper_bound AS hasta
FROM mi_espacio.documentos_lab13.files
ORDER BY desde
```

**En consola** nueve archivos, cada uno con su tramo del año.

```
| filas | desde      | hasta      |
| 4000  | 2024-01-01 | 2024-02-18 |
| 4000  | 2024-02-18 | 2024-04-06 |
| 1791  | 2024-04-06 | 2024-04-27 |
| 4000  | 2024-04-28 | 2024-06-16 |
| 4000  | 2024-06-16 | 2024-08-04 |
| 1807  | 2024-08-04 | 2024-08-26 |
| 4000  | 2024-08-27 | 2024-10-14 |
| 4000  | 2024-10-14 | 2024-12-02 |
| 2402  | 2024-12-02 | 2024-12-31 |
9 filas.
```

**Varía entre alumnos** los conteos de filas de los archivos parciales varían en algunas
unidades.

## Paso 2. La regla de medir

**Celda 2.1**

**Se escribe** (con su propia database).

```sql
SELECT count(*)          AS archivos_a_leer,
       sum(record_count)  AS filas_a_leer
FROM mi_espacio.documentos_lab13.files
WHERE readable_metrics.fecha_emision.upper_bound >= DATE '2024-06-01'
  AND readable_metrics.fecha_emision.lower_bound <= DATE '2024-06-30'
```

**En consola**

```
| archivos_a_leer | filas_a_leer |
| 2               | 8000         |
```

**Varía entre alumnos** las filas varían en algunas unidades.

## Paso 3. El cuadro completo

**Se escribe** nada.

**En consola** nada.

**Varía entre alumnos** nada.

## Paso 4. Lo que pasa cuando llega una carga desordenada

**Celda 4.1**

**Se escribe**

```sql
INSERT INTO documentos_lab13
SELECT * FROM curso.dte_2024 ORDER BY rand()
```

**En consola** `Listo. La sentencia se ejecutó.` Unos segundos.

**Varía entre alumnos** nada.

---

**Celda 4.2**

**Se escribe** (con su propia database).

```sql
SELECT record_count                                AS filas,
       readable_metrics.fecha_emision.lower_bound AS desde,
       readable_metrics.fecha_emision.upper_bound AS hasta
FROM mi_espacio.documentos_lab13.files
ORDER BY desde
```

**En consola** diez archivos, y el primero es el problema.

```
| filas | desde      | hasta      |
| 30000 | 2024-01-01 | 2024-12-31 |
| 4000  | 2024-01-01 | 2024-02-18 |
| 4000  | 2024-02-18 | 2024-04-06 |
| ...   |            |            |
| 2402  | 2024-12-02 | 2024-12-31 |
10 filas.
```

**Varía entre alumnos** nada relevante.

---

**Celda 4.3**

**Se escribe** (con su propia database).

```sql
SELECT count(*)          AS archivos_a_leer,
       sum(record_count)  AS filas_a_leer
FROM mi_espacio.documentos_lab13.files
WHERE readable_metrics.fecha_emision.upper_bound >= DATE '2024-06-01'
  AND readable_metrics.fecha_emision.lower_bound <= DATE '2024-06-30'
```

**En consola**

```
| archivos_a_leer | filas_a_leer |
| 3               | 38000        |
```

**Varía entre alumnos** las filas, en algunas unidades.

## Paso 5. Reordenar lo que ya está

**Celda 5.1**

**Se escribe** (con su propia database).

```sql
CALL spark_catalog.system.rewrite_data_files(
    table      => 'mi_espacio.documentos_lab13',
    strategy   => 'sort',
    sort_order => 'fecha_emision ASC NULLS LAST',
    options    => map('target-file-size-bytes', '250000',
                      'min-input-files',        '1',
                      'rewrite-all',            'true')
)
```

**En consola** diez archivos leídos y dieciocho escritos.

```
| rewritten_data_files_count | added_data_files_count | rewritten_bytes |
| 10                         | 18                     | 1608083         |
```

**Varía entre alumnos** los bytes.

---

**Celda 5.2**

**Se escribe** (con su propia database).

```sql
SELECT record_count                                AS filas,
       readable_metrics.fecha_emision.lower_bound AS desde,
       readable_metrics.fecha_emision.upper_bound AS hasta
FROM mi_espacio.documentos_lab13.files
ORDER BY desde
```

**En consola** dieciocho archivos, otra vez con rangos consecutivos y más finos que
antes, porque ahora hay sesenta mil documentos repartidos.

```
| filas | desde      | hasta      |
| 4000  | 2024-01-01 | 2024-01-25 |
| 4000  | 2024-01-25 | 2024-02-18 |
| 1310  | 2024-02-18 | 2024-02-25 |
| ...   |            |            |
| 1534  | 2024-12-22 | 2024-12-31 |
18 filas.
```

**Varía entre alumnos** los cortes exactos.

---

**Celda 5.3**

**Se escribe** (con su propia database).

```sql
SELECT count(*)          AS archivos_a_leer,
       sum(record_count)  AS filas_a_leer
FROM mi_espacio.documentos_lab13.files
WHERE readable_metrics.fecha_emision.upper_bound >= DATE '2024-06-01'
  AND readable_metrics.fecha_emision.lower_bound <= DATE '2024-06-30'
```

**En consola**

```
| archivos_a_leer | filas_a_leer |
| 3               | 9816         |
```

**Varía entre alumnos** las filas, en algunas unidades.

---

**Celda 5.4**

**Se escribe** (con su propia database).

```sql
SELECT snapshot_id, committed_at, operation
FROM mi_espacio.documentos_lab13.snapshots
ORDER BY committed_at
```

**En consola** cuatro páginas.

```
| snapshot_id         | committed_at            | operation |
| 5905954432758642680 | 2026-09-15 23:19:47.143 | append    |
| 3817757125605190733 | 2026-09-15 23:19:51.929 | replace   |
| 2262320413508159755 | 2026-09-15 23:19:54.294 | append    |
| 5078509714547263149 | 2026-09-15 23:19:58.428 | replace   |
4 filas.
```

**Varía entre alumnos** los identificadores y las fechas.
