# Laboratorio 05. La columna que no existía

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
DROP TABLE IF EXISTS documentos_lab05
```

**En consola** `Listo. La sentencia se ejecutó.`

**Cambia en tu corrida** nada.

---

**Celda 0.3**

**Se escribe**

```sql
CREATE TABLE documentos_lab05 USING iceberg AS
SELECT * FROM curso.dte_2024
```

**En consola** `Listo. La sentencia se ejecutó.` Es de las celdas más lentas, un par de
segundos.

**Cambia en tu corrida** nada.

---

**Celda 0.4**

**Se escribe**

```sql
SELECT count(*) AS documentos FROM documentos_lab05
```

**En consola**

```
| documentos |
| 30000      |
```

**Cambia en tu corrida** nada.

---

**Celda 0.5**

**Se escribe**

```sql
DESCRIBE TABLE documentos_lab05
```

**En consola** 13 filas.

```
| col_name            | data_type     |
| rut_emisor          | string        |
| razon_social_emisor | string        |
| tipo_dte            | int           |
| folio               | bigint        |
| fecha_emision       | date          |
| fecha_recepcion     | timestamp     |
| monto_neto          | decimal(18,2) |
| monto_iva           | decimal(18,2) |
| monto_total         | decimal(18,2) |
| estado_sii          | string        |
|                     |               |
| # Partitioning      |               |
| Not partitioned     |               |
13 filas.
```

**Cambia en tu corrida** nada.

## Paso 1. Llega el formato nuevo

**Celda 1.1**

**Se escribe**

```sql
DESCRIBE TABLE curso.dte_2026_reciente
```

**En consola** 15 filas.

```
| canal_emision   | string |
| codigo_sucursal | string |
```

**Cambia en tu corrida** nada.

---

**Celda 1.2**

**Se escribe**

```sql
INSERT INTO documentos_lab05 SELECT * FROM curso.dte_2026_reciente
```

**En consola** un aviso rojo, no una tabla.

```
Spark rechazó la sentencia:
Cannot write to 'spark_catalog.mi_espacio.documentos_lab05', too many data columns:
Table columns: 'rut_emisor', 'razon_social_emisor', …
Data columns:  'rut_emisor', 'razon_social_emisor', …
```

**Cambia en tu corrida** nada.

## Paso 2. Agregar las columnas

**Celda 2.1**

**Se escribe**

```sql
ALTER TABLE documentos_lab05
ADD COLUMNS (canal_emision STRING, codigo_sucursal STRING)
```

**En consola** `Listo. La sentencia se ejecutó.` Y fue **instantánea**.

**Cambia en tu corrida** nada.

---

**Celda 2.2**

**Se escribe**

```sql
SELECT rut_emisor, folio, monto_total, canal_emision, codigo_sucursal
FROM documentos_lab05
ORDER BY rut_emisor, tipo_dte, folio
LIMIT 3
```

**En consola**

```
| rut_emisor | folio | monto_total | canal_emision | codigo_sucursal |
| 76000262-3 | 3     | 11401907.65 | None          | None            |
| 76000262-3 | 42    | 6219295.81  | None          | None            |
| 76000262-3 | 62    | 2852995.25  | None          | None            |
3 filas.
```

**Cambia en tu corrida** nada.

---

**Celda 2.3**

**Se escribe**

```sql
SELECT count(*)             AS documentos,
       count(canal_emision) AS con_canal
FROM documentos_lab05
```

**En consola**

```
| documentos | con_canal |
| 30000      | 0         |
```

**Cambia en tu corrida** nada.

## Paso 3. Cargar el lote nuevo

**Celda 3.1**

**Se escribe**

```sql
INSERT INTO documentos_lab05 SELECT * FROM curso.dte_2026_reciente
```

**En consola** `Listo. La sentencia se ejecutó.`

**Cambia en tu corrida** nada.

---

**Celda 3.2**

**Se escribe**

```sql
SELECT year(fecha_emision)   AS anio,
       count(*)              AS documentos,
       count(canal_emision)  AS con_canal
FROM documentos_lab05
GROUP BY year(fecha_emision)
ORDER BY anio
```

**En consola**

```
| anio | documentos | con_canal |
| 2024 | 30000      | 0         |
| 2026 | 2500       | 2500      |
2 filas.
```

**Cambia en tu corrida** nada.

## Paso 4. Los otros cambios

**Celda 4.1**

**Se escribe**

```sql
ALTER TABLE documentos_lab05 RENAME COLUMN codigo_sucursal TO sucursal
```

**En consola** `Listo. La sentencia se ejecutó.`

**Cambia en tu corrida** nada.

---

**Celda 4.2**

**Se escribe**

```sql
SELECT rut_emisor, folio, canal_emision, sucursal
FROM documentos_lab05
WHERE canal_emision IS NOT NULL
ORDER BY rut_emisor, tipo_dte, folio
LIMIT 3
```

**En consola**

```
| rut_emisor | folio | canal_emision | sucursal |
| 76000262-3 | 33    | API_DGT       | SUC-022  |
| 76003963-2 | 1     | API_DGT       | SUC-031  |
| 76005022-9 | 43    | API_DGT       | SUC-003  |
3 filas.
```

**Cambia en tu corrida** nada.

---

**Celda 4.3**

**Se escribe**

```sql
ALTER TABLE documentos_lab05 ALTER COLUMN tipo_dte TYPE BIGINT
```

**En consola** `Listo. La sentencia se ejecutó.`

**Cambia en tu corrida** nada.

---

**Celda 4.4**

**Se escribe**

```sql
SELECT tipo_dte, count(*) AS documentos
FROM documentos_lab05
GROUP BY tipo_dte
ORDER BY tipo_dte
```

**En consola**

```
| tipo_dte | documentos |
| 33       | 13722      |
| 34       | 2305       |
| 39       | 12310      |
| 52       | 1904       |
| 56       | 637        |
| 61       | 1622       |
6 filas.
```

**Cambia en tu corrida** nada.

---

**Celda 4.5**

**Se escribe**

```sql
ALTER TABLE documentos_lab05 DROP COLUMN sucursal
```

**En consola** `Listo. La sentencia se ejecutó.`

**Cambia en tu corrida** nada.

---

**Celda 4.6**

**Se escribe**

```sql
SELECT rut_emisor, folio, canal_emision
FROM documentos_lab05
WHERE canal_emision IS NOT NULL
ORDER BY rut_emisor, tipo_dte, folio
LIMIT 3
```

**En consola** las mismas tres filas de antes, sin la columna borrada.

```
| rut_emisor | folio | canal_emision |
| 76000262-3 | 33    | API_DGT       |
| 76003963-2 | 1     | API_DGT       |
| 76005022-9 | 43    | API_DGT       |
3 filas.
```

**Cambia en tu corrida** nada.

## Paso 5. La historia del esquema

**Celda 5.1**

**Se escribe**

```sql
SELECT timestamp, latest_schema_id AS version_del_esquema
FROM mi_espacio.documentos_lab05.metadata_log_entries
ORDER BY timestamp
```

**En consola** seis filas, y la columna de la derecha **pasa de 0 a 1**.

```
| timestamp               | version_del_esquema |
| 2026-08-23 18:08:06.937 | 0                   |
| 2026-08-23 18:08:08.064 | 0                   |
| 2026-08-23 18:08:08.923 | 1                   |
| …                       | 1                   |
6 filas.
```

**Cambia en tu corrida** las horas, siempre.

---

**Celda 5.2**

**Se escribe**

```sql
SELECT snapshot_id, committed_at, operation
FROM mi_espacio.documentos_lab05.snapshots
ORDER BY committed_at
```

**En consola** dos páginas.

```
| snapshot_id         | committed_at            | operation |
| 6226388126644787856 | 2026-08-23 18:08:06.937 | append    |
| 2436349570425774481 | 2026-08-23 18:08:10.174 | append    |
2 filas.
```

**Cambia en tu corrida** los identificadores y las horas, siempre.

---

**Celda 5.3**

**Se escribe** (con tu identificador).

```sql
SELECT count(*) AS documentos FROM documentos_lab05 VERSION AS OF <TU_SNAPSHOT_ID>
```

**En consola**

```
| documentos |
| 30000      |
```

**Cambia en tu corrida** el número que escribiste, que es el de tu propia tabla.

---

**Celda 5.4**

**Se escribe** (con tu identificador).

```sql
SELECT canal_emision FROM documentos_lab05 VERSION AS OF <TU_SNAPSHOT_ID> LIMIT 1
```

**En consola**

```
Spark rechazó la sentencia:
Column 'canal_emision' does not exist. Did you mean one of the following? […]
```

**Cambia en tu corrida** el identificador dentro del mensaje.