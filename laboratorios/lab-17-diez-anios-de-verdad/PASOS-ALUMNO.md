# Laboratorio 17. Diez años de verdad

Cada celda lleva `%%sql` en la primera línea y una sola sentencia por celda.

## Paso 0. La bodega de diez años

**Celda 0.1**

**Se escribe**

```sql
SELECT count(*) AS documentos
FROM curso.dte_10_anios
WHERE fecha_emision = DATE '2015-01-05'
```

**En consola**

```
| documentos |
| 2234       |
1 fila.
```

**Cambia en tu corrida** nada.

---

**Celda 0.2**

**Se escribe**

```sql
SELECT count(*) AS documentos
FROM curso.dte_10_anios_por_mes
WHERE fecha_emision = DATE '2015-01-05'
```

**En consola**

```
| documentos |
| 2234       |
1 fila.
```

**Cambia en tu corrida** nada.

---

**Celda 0.3**

**Se escribe**

```sql
SELECT sum(record_count) AS documentos
FROM curso.dte_10_anios.files
```

**En consola**

```
| documentos |
| 10000000   |
1 fila.
CPU times: user 11.4 ms, sys: 5.36 ms, total: 16.7 ms
Wall time: 598 ms
```

**Cambia en tu corrida** el tiempo, siempre.

---

**Celda 0.4**

**Se escribe**

```sql
SELECT sum(record_count) AS documentos
FROM curso.dte_10_anios_por_mes.files
```

**En consola**

```
| documentos |
| 10000000   |
1 fila.
CPU times: user 10.9 ms, sys: 3.11 ms, total: 14 ms
Wall time: 217 ms
```

**Cambia en tu corrida** el tiempo.

## Paso 1. Contar la bodega entera

**Celda 1.1**

**Se escribe**

```sql
SELECT count(*) AS documentos FROM curso.dte_10_anios
```

**En consola**

```
| documentos |
| 10000000   |
1 fila.
CPU times: user 10.2 ms, sys: 4.84 ms, total: 15 ms
Wall time: 317 ms
```

## Paso 2. Junio de 2020

**Celda 2.1**

**Se escribe**

```sql
SELECT sum(monto_total) AS total_de_junio
FROM curso.dte_10_anios
WHERE fecha_emision BETWEEN '2020-06-01' AND '2020-06-30'
```

**En consola**

```
| total_de_junio  |
| 799678968699.81 |
1 fila.
CPU times: user 15.8 ms, sys: 4.29 ms, total: 20.1 ms
Wall time: 1.88 s
```

**Cambia en tu corrida** el tiempo, y bastante.

---

**Celda 2.2**

**Se escribe**

```sql
SELECT sum(monto_total) AS total_de_junio
FROM curso.dte_10_anios_por_mes
WHERE fecha_emision BETWEEN '2020-06-01' AND '2020-06-30'
```

**En consola**

```
| total_de_junio  |
| 799678968699.81 |
1 fila.
CPU times: user 11.1 ms, sys: 3.55 ms, total: 14.7 ms
Wall time: 239 ms
```

## Paso 3. Cuánto pesa cada una

**Celda 3.1**

**Se escribe** (ya viene escrita).

```
!hdfs dfs -du -s -h /warehouse/iceberg/curso.db/dte_10_anios
```

**En consola**

```
246.5 M  739.4 M  /warehouse/iceberg/curso.db/dte_10_anios
```

**Cambia en tu corrida** nada.

---

**Celda 3.2**

**Se escribe** (ya viene escrita).

```
!hdfs dfs -du -s -h /warehouse/iceberg/curso.db/dte_10_anios_por_mes
```

**En consola**

```
227.0 M  681.1 M  /warehouse/iceberg/curso.db/dte_10_anios_por_mes
```

## Paso 4. Muchos papelitos chicos

**Se escribe** el mi_espacio, en su cuaderno.

```sql-mi_espacio
SELECT count(*)                 AS papelitos,
       sum(record_count)        AS documentos,
       sum(file_size_in_bytes)  AS bytes
FROM mi_espacio.dte_un_anio_fragmentado.files
```

**En consola**

```
| papelitos | documentos | bytes    |
| 1464      | 1000000    | 33488658 |
1 fila.
```

---

**Se escribe** el mi_espacio, en su cuaderno.

```sql-mi_espacio
SELECT count(*) AS documentos
FROM mi_espacio.dte_un_anio_fragmentado
WHERE fecha_emision = DATE '2024-03-15'
```

**En consola**

```
| documentos |
| 2423       |
1 fila.
```

---

**Se escribe** el mi_espacio, en su cuaderno.

```sql-mi_espacio
SELECT sum(monto_total) AS total_del_anio
FROM mi_espacio.dte_un_anio_fragmentado
```

**En consola**

```
| total_del_anio   |
| 9646638010265.48 |
1 fila.
Wall time: 4.7 s
```

---

**Se escribe** el mi_espacio, en su cuaderno.

```sql-mi_espacio
CALL spark_catalog.system.rewrite_data_files('mi_espacio.dte_un_anio_fragmentado')
```

**En consola**

```
| rewritten_data_files_count | added_data_files_count | rewritten_bytes_count |
| 1464                       | 1                      | 33488658              |
1 fila.
Wall time: 19.2 s
```

---

**Se escribe** el mi_espacio, en su cuaderno.

```sql-mi_espacio
SELECT count(*)                 AS papelitos,
       sum(record_count)        AS documentos,
       sum(file_size_in_bytes)  AS bytes
FROM mi_espacio.dte_un_anio_fragmentado.files
```

**En consola**

```
| papelitos | documentos | bytes    |
| 1         | 1000000    | 22769408 |
1 fila.
```

---

**Se escribe** el mi_espacio, en su cuaderno.

```sql-mi_espacio
SELECT sum(monto_total) AS total_del_anio
FROM mi_espacio.dte_un_anio_fragmentado
```

**En consola**

```
| total_del_anio   |
| 9646638010265.48 |
1 fila.
Wall time: 276 ms
```

---

**Se escribe** el mi_espacio, en su cuaderno.

```sql-mi_espacio
SELECT (SELECT count(*)                  FROM mi_espacio.dte_un_anio_fragmentado.files)     AS papelitos_vigentes,
       (SELECT sum(file_size_in_bytes)   FROM mi_espacio.dte_un_anio_fragmentado.files)     AS bytes_vigentes,
       (SELECT count(DISTINCT file_path) FROM mi_espacio.dte_un_anio_fragmentado.all_files) AS papelitos_en_disco,
       (SELECT sum(bytes) FROM (SELECT DISTINCT file_path, file_size_in_bytes AS bytes
                                FROM mi_espacio.dte_un_anio_fragmentado.all_files))         AS bytes_en_disco
```

**En consola**

```
| papelitos_vigentes | bytes_vigentes | papelitos_en_disco | bytes_en_disco |
| 1                  | 22769408       | 1465               | 56258066       |
1 fila.
```
