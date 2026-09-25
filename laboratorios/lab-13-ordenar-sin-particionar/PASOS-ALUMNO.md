# Laboratorio 13. Ordenar sin particionar

Cada celda lleva `%%sql` en la primera línea y una sola sentencia por celda.

## Paso 0. Una tabla ordenada, sin particiones

**Celda 0.1**

**Se escribe**

```sql
USE mi_espacio
```

**En consola** `Listo. La sentencia se ejecutó.` Primera celda del día.

**Cambia en tu corrida** nada.

---

**Celda 0.2**

**Se escribe**

```sql
DROP TABLE IF EXISTS documentos_lab13
```

**En consola** `Listo. La sentencia se ejecutó.`

**Cambia en tu corrida** nada.

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

**Cambia en tu corrida** nada.

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
1 fila.
```

**Cambia en tu corrida** nada.

---

**Celda 0.5**

**Se escribe**

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

**Cambia en tu corrida** nada.

## Paso 1. Partirla en varios archivos

**Celda 1.1**

**Se escribe**

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

```
| rewritten_data_files_count | added_data_files_count | rewritten_bytes_count |
| 1                          | 9                      | 720233                |
1 fila.
```

**Cambia en tu corrida** los bytes, en algunos miles.

---

**Celda 1.2**

**Se escribe**

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

**Cambia en tu corrida** los conteos de filas de los archivos parciales, en algunas unidades.

## Paso 2. La regla de medir

**Celda 2.1**

**Se escribe**

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
1 fila.
```

**Cambia en tu corrida** las filas, en algunas unidades.

## Paso 3. El cuadro completo

**Se escribe** nada.

**En consola** nada.

**Cambia en tu corrida** nada.

## Paso 4. Lo que pasa cuando llega una carga desordenada

**Celda 4.1**

**Se escribe**

```sql
INSERT INTO documentos_lab13
SELECT * FROM curso.dte_2024 ORDER BY rand()
```

**En consola** `Listo. La sentencia se ejecutó.` Unos segundos.

**Cambia en tu corrida** nada.

---

**Celda 4.2**

**Se escribe**

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
| 1791  | 2024-04-06 | 2024-04-27 |
| 4000  | 2024-04-28 | 2024-06-16 |
| 4000  | 2024-06-16 | 2024-08-04 |
| 1807  | 2024-08-04 | 2024-08-26 |
| 4000  | 2024-08-27 | 2024-10-14 |
| 4000  | 2024-10-14 | 2024-12-02 |
| 2402  | 2024-12-02 | 2024-12-31 |
10 filas.
```

**Cambia en tu corrida** nada relevante.

---

**Celda 4.3**

**Se escribe**

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
1 fila.
```

**Cambia en tu corrida** las filas, en algunas unidades.

## Paso 5. Reordenar lo que ya está

**Celda 5.1**

**Se escribe**

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
| rewritten_data_files_count | added_data_files_count | rewritten_bytes_count |
| 10                         | 18                     | 1607543               |
1 fila.
```

**Cambia en tu corrida** los bytes.

---

**Celda 5.2**

**Se escribe**

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
| 2000  | 2024-02-18 | 2024-02-29 |
| 4000  | 2024-03-01 | 2024-03-25 |
| 4000  | 2024-03-25 | 2024-04-18 |
| 1582  | 2024-04-18 | 2024-04-27 |
| 4000  | 2024-04-28 | 2024-05-23 |
| 4000  | 2024-05-23 | 2024-06-16 |
| 2110  | 2024-06-16 | 2024-06-28 |
| 4000  | 2024-06-29 | 2024-07-23 |
| 4000  | 2024-07-23 | 2024-08-17 |
| 1956  | 2024-08-17 | 2024-08-29 |
| 4000  | 2024-08-30 | 2024-09-23 |
| 4000  | 2024-09-23 | 2024-10-17 |
| 2068  | 2024-10-17 | 2024-10-29 |
| 4000  | 2024-10-30 | 2024-11-23 |
| 4000  | 2024-11-23 | 2024-12-18 |
| 2284  | 2024-12-18 | 2024-12-31 |
18 filas.
```

**Cambia en tu corrida** los cortes exactos.

---

**Celda 5.3**

**Se escribe**

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
| 3               | 10110        |
1 fila.
```

**Cambia en tu corrida** las filas, en algunas unidades.

---

**Celda 5.4**

**Se escribe**

```sql
SELECT snapshot_id, committed_at, operation
FROM mi_espacio.documentos_lab13.snapshots
ORDER BY committed_at
```

**En consola** cuatro páginas.

```
| snapshot_id         | committed_at            | operation |
| 530236845447903924  | 2026-09-25 18:10:38.144 | append    |
| 4212473458663648284 | 2026-09-25 18:10:40.540 | replace   |
| 8305626539744031014 | 2026-09-25 18:10:42.002 | append    |
| 1566782443588773562 | 2026-09-25 18:10:43.551 | replace   |
4 filas.
```

**Cambia en tu corrida** los identificadores y las fechas.