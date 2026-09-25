# Laboratorio 12. El panel del administrador

Cada celda lleva `%%sql` en la primera línea y una sola sentencia por celda.

## Paso 0. La tabla de hoy, con sus achaques

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
DROP TABLE IF EXISTS panel_lab12
```

**En consola** `Listo. La sentencia se ejecutó.`

**Cambia en tu corrida** nada.

---

**Celda 0.3**

**Se escribe**

```sql
CREATE TABLE panel_lab12
USING iceberg
PARTITIONED BY (months(fecha_emision))
AS SELECT * FROM curso.dte_2024
WHERE fecha_emision BETWEEN DATE '2024-01-01' AND DATE '2024-01-31'
```

**En consola** `Listo. La sentencia se ejecutó.`

**Cambia en tu corrida** nada.

---

**Celda 0.4**

**Se escribe** (ya viene escrita).

```python
ESPACIO = "mi_espacio"

for mes in range(2, 13):
    for dia in (10, 20):
        fecha = f"2024-{mes:02d}-{dia:02d}"
        spark.sql(
            f"INSERT INTO {ESPACIO}.panel_lab12 "
            f"SELECT * FROM curso.dte_2024 WHERE fecha_emision = DATE '{fecha}'"
        )
        print("cargado", fecha)

print("listo: 22 cargas diarias")
```

**En consola** veintitrés líneas.

```
cargado 2024-02-10
cargado 2024-02-20
cargado 2024-03-10
…
cargado 2024-12-20
listo: 22 cargas diarias
```

**Cambia en tu corrida** nada.

---

**Celda 0.5**

**Se escribe**

```sql
UPDATE panel_lab12
SET estado_sii = 'ACEPTADO'
WHERE fecha_emision BETWEEN DATE '2024-01-01' AND DATE '2024-01-31'
  AND estado_sii = 'EN_REVISION'
```

**En consola** `Listo. La sentencia se ejecutó.`

**Cambia en tu corrida** nada.

---

**Celda 0.6**

**Se escribe**

```sql
UPDATE panel_lab12
SET monto_iva = round(monto_neto * 0.19)
WHERE fecha_emision = DATE '2024-01-05'
```

**En consola** `Listo. La sentencia se ejecutó.`

**Cambia en tu corrida** nada.

---

**Celda 0.7**

**Se escribe**

```sql
UPDATE panel_lab12
SET tipo_dte = 33
WHERE fecha_emision = DATE '2024-01-01'
  AND tipo_dte = 34
```

**En consola** `Listo. La sentencia se ejecutó.`

**Cambia en tu corrida** nada.

---

**Celda 0.8**

**Se escribe**

```sql
ALTER TABLE panel_lab12 ADD COLUMN revisado_por STRING
```

**En consola** `Listo. La sentencia se ejecutó.`

**Cambia en tu corrida** nada.

---

**Celda 0.9**

**Se escribe**

```sql
DELETE FROM panel_lab12 WHERE fecha_emision = DATE '2024-07-20'
```

**En consola** `Listo. La sentencia se ejecutó.`

**Cambia en tu corrida** nada.

## Paso 1. ¿Cuántos archivos tiene la tabla y cuánto pesan?

**Celda 1.1**

**Se escribe**

```sql
SELECT count(*)                AS archivos,
       sum(record_count)       AS filas,
       sum(file_size_in_bytes) AS bytes
FROM mi_espacio.panel_lab12.files
```

**En consola**

```
| archivos | filas | bytes  |
| 22       | 4232  | 208727 |
1 fila.
```

**Cambia en tu corrida** los bytes, en unas pocas unidades.

---

**Celda 1.2**

**Se escribe**

```sql
SELECT 'panel_lab12' AS tabla, count(*) AS archivos
FROM mi_espacio.panel_lab12.files
UNION ALL
SELECT 'documentos_lab11' AS tabla, count(*) AS archivos
FROM mi_espacio.documentos_lab11.files
ORDER BY archivos DESC
```

**En consola**

```
| tabla            | archivos |
| panel_lab12      | 22       |
| documentos_lab11 | 1        |
2 filas.
```

**Cambia en tu corrida** los archivos de `documentos_lab11`, según cómo haya quedado esa tabla.

## Paso 2. ¿Cuántos archivos chicos hay?

**Celda 2.1**

**Se escribe**

```sql
SELECT count(*)                                                 AS archivos,
       count(CASE WHEN file_size_in_bytes < 1048576 THEN 1 END) AS chicos,
       min(file_size_in_bytes)                                  AS el_mas_chico
FROM mi_espacio.panel_lab12.files
```

**En consola**

```
| archivos | chicos | el_mas_chico |
| 22       | 22     | 5887         |
1 fila.
```

**Cambia en tu corrida** el tamaño del más chico, en unas pocas unidades.

## Paso 3. ¿Cuántas páginas acumula la tabla?

**Celda 3.1**

**Se escribe**

```sql
SELECT count(*)          AS paginas,
       min(committed_at) AS la_mas_vieja,
       max(committed_at) AS la_mas_nueva
FROM mi_espacio.panel_lab12.snapshots
```

**En consola**

```
| paginas | la_mas_vieja            | la_mas_nueva            |
| 27      | 2026-09-24 00:12:21.583 | 2026-09-24 00:12:52.648 |
1 fila.
```

**Cambia en tu corrida** las dos fechas, siempre.

## Paso 4. ¿Cuánto ocupan las páginas que ya no cuentan?

**Celda 4.1**

**Se escribe**

```sql
SELECT (SELECT count(*) FROM mi_espacio.panel_lab12.files)     AS archivos_vigentes,
       (SELECT count(*) FROM mi_espacio.panel_lab12.all_files) AS archivos_totales,
       (SELECT sum(file_size_in_bytes) FROM mi_espacio.panel_lab12.all_files)
       - (SELECT sum(file_size_in_bytes) FROM mi_espacio.panel_lab12.files) AS bytes_recuperables
```

**En consola**

```
| archivos_vigentes | archivos_totales | bytes_recuperables |
| 22                | 25               | 152322             |
1 fila.
```

**Cambia en tu corrida** los bytes, en unas pocas unidades.

## Paso 5. ¿Hay particiones desparejas?

**Celda 5.1**

**Se escribe**

```sql
SELECT partition,
       record_count AS filas,
       file_count   AS archivos
FROM mi_espacio.panel_lab12.partitions
ORDER BY record_count DESC
```

**En consola** doce filas, una por mes.

```
| partition | filas | archivos |
| (648,)    | 2500  | 1        |
| (655,)    | 188   | 2        |
| (658,)    | 181   | 2        |
| (653,)    | 174   | 2        |
| (651,)    | 169   | 2        |
| (649,)    | 165   | 2        |
| (657,)    | 165   | 2        |
| (650,)    | 158   | 2        |
| (659,)    | 157   | 2        |
| (656,)    | 143   | 2        |
| (652,)    | 142   | 2        |
| (654,)    | 90    | 1        |
12 filas.
```

**Cambia en tu corrida** nada.

## Paso 6. ¿Cuándo fue la última escritura?

**Celda 6.1**

**Se escribe**

```sql
SELECT committed_at AS ultima_escritura,
       operation    AS que_hizo
FROM mi_espacio.panel_lab12.snapshots
ORDER BY committed_at DESC
LIMIT 1
```

**En consola**

```
| ultima_escritura        | que_hizo |
| 2026-09-24 00:12:52.648 | delete   |
1 fila.
```

**Cambia en tu corrida** la fecha, siempre.

## Paso 7. ¿Cuántas versiones de portada hay?

**Celda 7.1**

**Se escribe**

```sql
SELECT count(*)              AS portadas,
       max(latest_schema_id) AS ultimo_esquema
FROM mi_espacio.panel_lab12.metadata_log_entries
```

**En consola**

```
| portadas | ultimo_esquema |
| 28       | 1              |
1 fila.
```

**Cambia en tu corrida** nada.

## Paso 8. ¿La tabla se compactó alguna vez?

**Celda 8.1**

**Se escribe**

```sql
SELECT (SELECT count(*) FROM mi_espacio.panel_lab12.files)                                 AS archivos,
       (SELECT count(*) FROM mi_espacio.panel_lab12.snapshots WHERE operation = 'replace') AS veces_compactada
```

**En consola**

```
| archivos | veces_compactada |
| 22       | 0                |
1 fila.
```

**Cambia en tu corrida** nada.