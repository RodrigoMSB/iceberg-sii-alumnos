# Laboratorio 04. Buscar sin dar vuelta el almacén

Cada celda lleva `%%sql` en la primera línea y una sola sentencia por celda.

## Paso 0. Preparar la tabla

**Celda 0.1**

**Se escribe**

```sql
USE mi_espacio
```

**En consola** `Listo. La sentencia se ejecutó.` Primera celda.

**Cambia en tu corrida** nada.

---

**Celda 0.2**

**Se escribe**

```sql
DROP TABLE IF EXISTS documentos_sin_particion
```

**En consola** `Listo. La sentencia se ejecutó.`

**Cambia en tu corrida** nada.

---

**Celda 0.3**

**Se escribe**

```sql
DROP TABLE IF EXISTS documentos_por_mes
```

**En consola** `Listo. La sentencia se ejecutó.`

**Cambia en tu corrida** nada.

---

**Celda 0.4**

**Se escribe**

```sql
CREATE TABLE documentos_sin_particion USING iceberg AS
SELECT * FROM curso.dte_2024
```

**En consola** `Listo. La sentencia se ejecutó.` Es de las celdas más lentas del
laboratorio, unos segundos.

**Cambia en tu corrida** nada.

---

**Celda 0.5**

**Se escribe**

```sql
SELECT * FROM documentos_sin_particion
ORDER BY fecha_emision, rut_emisor, tipo_dte, folio
LIMIT 5
```

**En consola** cinco filas y diez columnas.

```
| rut_emisor | razon_social_emisor      | tipo_dte | folio | fecha_emision | fecha_recepcion       | monto_neto | monto_iva  | monto_total | estado_sii |
| 76114218-6 | Coihue Maquinarias SpA   | 33       | 1     | 2024-01-01    | 2024-01-01 13:46:49.0 | 1656950.00 | 314820.50  | 1971770.50  | ACEPTADO   |
| 76169126-0 | Ulmo Maquinarias Ltda.   | 33       | 1     | 2024-01-01    | 2024-01-03 14:40:08.0 | 235404.00  | 44726.76   | 280130.76   | ACEPTADO   |
| 76194732-K | Boldo Importadora Ltda.  | 39       | 1     | 2024-01-01    | 2024-01-02 01:42:09.0 | 113373.00  | 21540.87   | 134913.87   | ACEPTADO   |
| 76253726-5 | Ulmo Transportes S.A.    | 33       | 4     | 2024-01-01    | 2024-01-03 13:28:12.0 | 8458882.00 | 1607187.58 | 10066069.58 | ACEPTADO   |
| 76257050-5 | Araucaria Agricola Ltda. | 39       | 11    | 2024-01-01    | 2024-01-02 09:49:18.0 | 41107.00   | 7810.33    | 48917.33    | ACEPTADO   |
5 filas.
```

**Cambia en tu corrida** nada.

---

**Celda 0.6**

**Se escribe**

```sql
SELECT count(*) AS documentos FROM documentos_sin_particion
```

**En consola**

```
| documentos |
| 30000      |
```

**Cambia en tu corrida** nada.

## Paso 1. La consulta lenta

**Celda 1.1**

**Se escribe**

```sql
SELECT count(*)          AS documentos,
       sum(monto_total)  AS total_junio
FROM documentos_sin_particion
WHERE fecha_emision BETWEEN DATE '2024-06-01' AND DATE '2024-06-30'
```

**En consola**

```
| documentos | total_junio    |
| 2500       | 24547341762.59 |
```

**Cambia en tu corrida** nada.

---

**Celda 1.2**

**Se escribe**

```sql
SELECT record_count                                AS filas,
       readable_metrics.fecha_emision.lower_bound  AS desde,
       readable_metrics.fecha_emision.upper_bound  AS hasta
FROM mi_espacio.documentos_sin_particion.files
ORDER BY desde
```

**En consola**

```
| filas | desde      | hasta      |
| 30000 | 2024-01-01 | 2024-12-31 |
1 fila.
```

**Cambia en tu corrida** nada.

---

**Celda 1.3**

**Se escribe**

```sql
SELECT count(*)                AS archivos_a_leer,
       sum(record_count)       AS filas_a_leer,
       sum(file_size_in_bytes) AS bytes_a_leer
FROM mi_espacio.documentos_sin_particion.files
WHERE readable_metrics.fecha_emision.upper_bound >= DATE '2024-06-01'
  AND readable_metrics.fecha_emision.lower_bound <= DATE '2024-06-30'
```

**En consola**

```
| archivos_a_leer | filas_a_leer | bytes_a_leer |
| 1               | 30000        | 776514       |
```

**Cambia en tu corrida** nada.

## Paso 2. Crear la tabla particionada

**Celda 2.1**

**Se escribe**

```sql
CREATE TABLE documentos_por_mes USING iceberg
PARTITIONED BY (months(fecha_emision)) AS
SELECT * FROM curso.dte_2024 ORDER BY fecha_emision
```

**En consola** `Listo. La sentencia se ejecutó.` Es la celda más lenta del laboratorio.

**Cambia en tu corrida** nada.

---

**Celda 2.2**

**Se escribe**

```sql
SELECT count(*) AS documentos FROM documentos_por_mes
```

**En consola**

```
| documentos |
| 30000      |
```

**Cambia en tu corrida** nada.

## Paso 3. La misma consulta, ahora sí

**Celda 3.1**

**Se escribe**

```sql
SELECT count(*)          AS documentos,
       sum(monto_total)  AS total_junio
FROM documentos_por_mes
WHERE fecha_emision BETWEEN DATE '2024-06-01' AND DATE '2024-06-30'
```

**En consola** exactamente el mismo resultado del paso 1.

```
| documentos | total_junio    |
| 2500       | 24547341762.59 |
```

**Cambia en tu corrida** nada.

---

**Celda 3.2**

**Se escribe**

```sql
SELECT count(*)                AS archivos_a_leer,
       sum(record_count)       AS filas_a_leer,
       sum(file_size_in_bytes) AS bytes_a_leer
FROM mi_espacio.documentos_por_mes.files
WHERE readable_metrics.fecha_emision.upper_bound >= DATE '2024-06-01'
  AND readable_metrics.fecha_emision.lower_bound <= DATE '2024-06-30'
```

**En consola**

```
| archivos_a_leer | filas_a_leer | bytes_a_leer |
| 1               | 2500         | 71779        |
```

```
sin particionar        1 archivo    30.000 filas    776.514 bytes
particionada por mes   1 archivo     2.500 filas     71.779 bytes
```

**Cambia en tu corrida** los bytes, en algunas unidades.

## Paso 4. El particionamiento oculto

**Celda 4.1**

**Se escribe**

```sql
DESCRIBE TABLE EXTENDED documentos_por_mes
```

**En consola** 27 filas.

```
| # Partitioning |                       |
| Part 0         | months(fecha_emision) |
```

**Cambia en tu corrida** nada.

---

**Celda 4.2**

**Se escribe**

```sql
SELECT add_months(DATE '1970-01-01', partition.fecha_emision_month) AS mes,
       record_count AS documentos,
       file_count   AS archivos
FROM mi_espacio.documentos_por_mes.partitions
ORDER BY mes
```

**En consola** doce filas, una por mes.

```
| mes        | documentos | archivos |
| 2024-01-01 | 2500       | 1        |
| 2024-02-01 | 2500       | 1        |
…
12 filas.
```

**Cambia en tu corrida** nada.

## Paso 5. Cambiar el criterio

**Celda 5.1**

**Se escribe**

```sql
ALTER TABLE documentos_por_mes
REPLACE PARTITION FIELD months(fecha_emision) WITH days(fecha_emision)
```

**En consola** `Listo. La sentencia se ejecutó.` Instantánea.

**Cambia en tu corrida** nada.

---

**Celda 5.2**

**Se escribe**

```sql
DESCRIBE TABLE EXTENDED documentos_por_mes
```

**En consola** otra vez 27 filas, y la **fila 13** ahora dice.

```
| Part 0 | days(fecha_emision) |
```

**Cambia en tu corrida** nada.

---

**Celda 5.3**

**Se escribe**

```sql
INSERT INTO documentos_por_mes
SELECT * FROM curso.dte_2025_enero ORDER BY fecha_emision
```

**En consola** `Listo. La sentencia se ejecutó.`

**Cambia en tu corrida** nada.

---

**Celda 5.4**

**Se escribe**

```sql
SELECT spec_id,
       count(*)          AS archivos,
       sum(record_count) AS documentos
FROM mi_espacio.documentos_por_mes.files
GROUP BY spec_id
ORDER BY spec_id
```

**En consola**

```
| spec_id | archivos | documentos |
| 0       | 12       | 30000      |
| 1       | 31       | 2500       |
2 filas.
```

**Cambia en tu corrida** nada.

---

**Celda 5.5**

**Se escribe**

```sql
SELECT count(*)          AS documentos,
       sum(monto_total)  AS total_junio
FROM documentos_por_mes
WHERE fecha_emision BETWEEN DATE '2024-06-01' AND DATE '2024-06-30'
```

**En consola** el mismo resultado de siempre.

```
| documentos | total_junio    |
| 2500       | 24547341762.59 |
```

**Cambia en tu corrida** nada.

---

**Celda 5.6**

**Se escribe**

```sql
SELECT count(*)          AS documentos,
       sum(monto_total)  AS total_enero_2025
FROM documentos_por_mes
WHERE fecha_emision BETWEEN DATE '2025-01-01' AND DATE '2025-01-31'
```

**En consola**

```
| documentos | total_enero_2025 |
| 2500       | 24895193513.17   |
```

**Cambia en tu corrida** nada.