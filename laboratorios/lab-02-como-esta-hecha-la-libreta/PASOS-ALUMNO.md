# Laboratorio 02. Cómo está hecha la libreta

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
DROP TABLE IF EXISTS contribuyentes_lab02
```

**En consola** `Listo. La sentencia se ejecutó.`

**Cambia en tu corrida** nada.

---

**Celda 0.3**

**Se escribe**

```sql
CREATE TABLE contribuyentes_lab02 (
    rut           STRING,
    razon_social  STRING,
    segmento      STRING
) USING iceberg
```

**En consola** `Listo. La sentencia se ejecutó.`

**Cambia en tu corrida** nada.

---

**Celda 0.4**

**Se escribe**

```sql
INSERT INTO contribuyentes_lab02 VALUES
    ('77746521-K', 'Pehuen Logistica EIRL',    'MICRO'),
    ('77884562-8', 'Araucaria Ferreteria SpA', 'PEQUENA'),
    ('78800840-6', 'Copihue Maquinarias EIRL', 'MEDIANA')
```

**En consola** `Listo. La sentencia se ejecutó.`

**Cambia en tu corrida** nada.

---

**Celda 0.5**

**Se escribe**

```sql
INSERT INTO contribuyentes_lab02 VALUES
    ('76171162-8', 'Huemul Alimentos EIRL',    'GRANDE')
```

**En consola** `Listo. La sentencia se ejecutó.`

**Cambia en tu corrida** nada.

---

**Celda 0.6**

**Se escribe**

```sql
SELECT * FROM contribuyentes_lab02 ORDER BY rut
```

**En consola**

```
| rut        | razon_social             | segmento |
| 76171162-8 | Huemul Alimentos EIRL    | GRANDE   |
| 77746521-K | Pehuen Logistica EIRL    | MICRO    |
| 77884562-8 | Araucaria Ferreteria SpA | PEQUENA  |
| 78800840-6 | Copihue Maquinarias EIRL | MEDIANA  |
4 filas.
```

**Cambia en tu corrida** nada.

## Paso 1. La tabla se describe a sí misma

**Celda 1.1**

**Se escribe**

```sql
DESCRIBE TABLE EXTENDED contribuyentes_lab02
```

**En consola** unas 20 filas.

```
| Name     | spark_catalog.mi_espacio.contribuyentes_lab02          |
| Location | hdfs://namenode:8020/warehouse/iceberg/mi_espacio.db/… |
| Provider | iceberg                                             |
```

**Cambia en tu corrida** nada.

---

**Celda 1.2**

**Se escribe**

```sql
SHOW TBLPROPERTIES contribuyentes_lab02
```

**En consola**

```
| key                 | value               |
| current-snapshot-id | 3612637108659539787 |
| format              | iceberg/parquet     |
| format-version      | 1                   |
```

**Cambia en tu corrida** `current-snapshot-id`, siempre.

## Paso 2. Las páginas y los manifiestos

**Celda 2.1**

**Se escribe**

```sql
SELECT snapshot_id, committed_at, operation
FROM mi_espacio.contribuyentes_lab02.snapshots
ORDER BY committed_at
```

**En consola** dos filas, una por carga, las dos `append`.

```
| snapshot_id         | committed_at            | operation |
| 5604856730393747384 | 2026-08-23 00:44:29.638 | append    |
| 3612637108659539787 | 2026-08-23 00:44:29.985 | append    |
```

**Cambia en tu corrida** los identificadores y las fechas, siempre.

---

**Celda 2.2**

**Se escribe**

```sql
SELECT made_current_at, snapshot_id, is_current_ancestor
FROM mi_espacio.contribuyentes_lab02.history
ORDER BY made_current_at
```

**En consola** dos filas, las dos con `is_current_ancestor` en `True`.

**Cambia en tu corrida** identificadores y fechas.

---

**Celda 2.3**

**Se escribe**

```sql
SELECT path, added_snapshot_id, added_data_files_count, existing_data_files_count
FROM mi_espacio.contribuyentes_lab02.manifests
```

**En consola** dos filas, un manifiesto por carga.

```
| path        | added_snapshot_id   | added_data_files_count | existing_data_files_count |
| hdfs://…    | 3612637108659539787 | 1                      | 0                         |
| hdfs://…    | 5604856730393747384 | 2                      | 0                         |
```

**Cambia en tu corrida** las rutas y los identificadores.

## Paso 3. Dónde viven los datos

**Celda 3.1**

**Se escribe**

```sql
SELECT file_path, record_count, file_size_in_bytes
FROM mi_espacio.contribuyentes_lab02.files
```

**En consola** tres filas.

```
| file_path | record_count | file_size_in_bytes |
| hdfs://…  | 1            | 1109               |
| hdfs://…  | 1            | 1102               |
| hdfs://…  | 2            | 1091               |
```

**Cambia en tu corrida** las rutas, y los tamaños en bytes en algunas unidades.

---

**Celda 3.2**

**Se escribe**

```sql
SELECT count(*)                 AS archivos,
       sum(record_count)        AS filas,
       sum(file_size_in_bytes)  AS bytes
FROM mi_espacio.contribuyentes_lab02.files
```

**En consola**

```
| archivos | filas | bytes |
| 3        | 4     | 3302  |
```

**Cambia en tu corrida** `bytes`.

## Paso 4. El mismo dato desde otro motor

**Se escribe** (en Hue).

```sql-hue
SELECT * FROM mi_espacio.contribuyentes_lab02 ORDER BY rut
```

**En consola** las **mismas cuatro filas** que en el notebook.

```
| rut        | razon_social             | segmento |
| 76171162-8 | Huemul Alimentos EIRL    | GRANDE   |
| 77746521-K | Pehuen Logistica EIRL    | MICRO    |
| 77884562-8 | Araucaria Ferreteria SpA | PEQUENA  |
| 78800840-6 | Copihue Maquinarias EIRL | MEDIANA  |
```

**Cambia en tu corrida** nada.

---

**Se escribe** (en Hue).

```sql-hue
INSERT INTO mi_espacio.contribuyentes_lab02 VALUES ('79412337-8','Quillay Servicios SpA','PEQUENA')
```

**En consola** Hue muestra una tabla con una sola columna `Result` y ninguna fila.

**Cambia en tu corrida** nada.

---

**Celda 4.1**

**Se escribe**

```sql
SELECT * FROM contribuyentes_lab02 ORDER BY rut
```

**En consola** **cuatro filas todavía**, no cinco.

```
| rut        | razon_social             | segmento |
| 76171162-8 | Huemul Alimentos EIRL    | GRANDE   |
| 77746521-K | Pehuen Logistica EIRL    | MICRO    |
| 77884562-8 | Araucaria Ferreteria SpA | PEQUENA  |
| 78800840-6 | Copihue Maquinarias EIRL | MEDIANA  |
4 filas.
```

**Cambia en tu corrida** puede que salgan cinco, si la copia que el motor tenía en memoria ya se venció.

---

**Celda 4.2**

**Se escribe**

```sql
REFRESH TABLE contribuyentes_lab02
```

**En consola** `Listo. La sentencia se ejecutó.`

**Cambia en tu corrida** nada.

---

**Celda 4.3**

**Se escribe**

```sql
SELECT * FROM contribuyentes_lab02 ORDER BY rut
```

**En consola** cinco filas.

```
| rut        | razon_social             | segmento |
| 76171162-8 | Huemul Alimentos EIRL    | GRANDE   |
| 77746521-K | Pehuen Logistica EIRL    | MICRO    |
| 77884562-8 | Araucaria Ferreteria SpA | PEQUENA  |
| 78800840-6 | Copihue Maquinarias EIRL | MEDIANA  |
| 79412337-8 | Quillay Servicios SpA    | PEQUENA  |
5 filas.
```

**Cambia en tu corrida** nada, si escribiste en Hue la misma fila que aparece aquí.

---

**Celda 4.4**

**Se escribe**

```sql
SELECT snapshot_id, committed_at, operation
FROM mi_espacio.contribuyentes_lab02.snapshots
ORDER BY committed_at
```

**En consola** **tres** páginas.

```
| snapshot_id         | committed_at            | operation |
| 5604856730393747384 | 2026-08-23 00:44:29.638 | append    |
| 3612637108659539787 | 2026-08-23 00:44:29.985 | append    |
| 1526672598735946670 | 2026-08-23 00:44:34.191 | append    |
```

**Cambia en tu corrida** identificadores y fechas.