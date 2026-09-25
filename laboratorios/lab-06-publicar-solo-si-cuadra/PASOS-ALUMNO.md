# Laboratorio 06. Publicar solo si cuadra

Cada celda lleva `%%sql` en la primera línea y una sola sentencia por celda.

## Paso 0. Preparar la tabla

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
DROP TABLE IF EXISTS recepcion_lab06
```

**En consola** `Listo. La sentencia se ejecutó.`

**Cambia en tu corrida** nada.

---

**Celda 0.3**

**Se escribe**

```sql
CREATE TABLE recepcion_lab06 USING iceberg AS
SELECT * FROM curso.recepcion_limpia
```

**En consola** `Listo. La sentencia se ejecutó.`

**Cambia en tu corrida** nada.

---

**Celda 0.4**

**Se escribe**

```sql
SELECT count(*)         AS documentos,
       sum(monto_total) AS total_del_mes
FROM recepcion_lab06
```

**En consola**

```
| documentos | total_del_mes |
| 1000       | 9117709433.18 |
```

**Cambia en tu corrida** nada.

## Paso 1. El riesgo, mostrado

**Celda 1.1**

**Se escribe**

```sql
INSERT INTO recepcion_lab06 SELECT * FROM curso.recepcion_sospechosa
```

**En consola** `Listo. La sentencia se ejecutó.`

**Cambia en tu corrida** nada.

---

**Celda 1.2**

**Se escribe**

```sql
SELECT count(*) AS documentos,
       sum(CASE WHEN abs(monto_iva - round(monto_neto * 0.19)) > 2
                THEN 1 ELSE 0 END) AS errores_iva,
       sum(CASE WHEN abs(monto_total - (monto_neto + monto_exento + monto_iva)) > 2
                THEN 1 ELSE 0 END) AS errores_suma,
       sum(CASE WHEN monto_total < 0 AND tipo_dte <> 61
                THEN 1 ELSE 0 END) AS errores_negativos
FROM recepcion_lab06
```

**En consola**

```
| documentos | errores_iva | errores_suma | errores_negativos |
| 1500       | 13          | 20           | 7                 |
```

**Cambia en tu corrida** nada.

---

**Celda 1.3**

**Se escribe**

```sql
SELECT count(*) AS documentos_que_no_cuadran
FROM recepcion_lab06
WHERE abs(monto_iva - round(monto_neto * 0.19)) > 2
   OR abs(monto_total - (monto_neto + monto_exento + monto_iva)) > 2
   OR (monto_total < 0 AND tipo_dte <> 61)
```

**En consola**

```
| documentos_que_no_cuadran |
| 20                        |
```

**Cambia en tu corrida** nada.

---

**Celda 1.4**

**Se escribe**

```sql
SELECT snapshot_id, committed_at, operation
FROM mi_espacio.recepcion_lab06.snapshots
ORDER BY committed_at
```

**En consola**

```
| snapshot_id         | committed_at            | operation |
| 1276068155314944172 | 2026-08-23 18:49:45.569 | append    |
| 8948402203407673627 | 2026-08-23 18:49:48.454 | append    |
```

**Cambia en tu corrida** los identificadores y las horas, siempre.

---

**Celda 1.5**

**Se escribe**

```sql
CALL spark_catalog.system.rollback_to_snapshot('mi_espacio.recepcion_lab06', <TU_SNAPSHOT_ID>)
```

**En consola**

```
| previous_snapshot_id | current_snapshot_id |
| 8948402203407673627  | 1276068155314944172 |
```

**Cambia en tu corrida** los dos números.

---

**Celda 1.6**

**Se escribe**

```sql
SELECT count(*) AS documentos,
       sum(CASE WHEN abs(monto_iva - round(monto_neto * 0.19)) > 2
                THEN 1 ELSE 0 END) AS errores_iva,
       sum(CASE WHEN abs(monto_total - (monto_neto + monto_exento + monto_iva)) > 2
                THEN 1 ELSE 0 END) AS errores_suma,
       sum(CASE WHEN monto_total < 0 AND tipo_dte <> 61
                THEN 1 ELSE 0 END) AS errores_negativos
FROM recepcion_lab06
```

**En consola**

```
| documentos | errores_iva | errores_suma | errores_negativos |
| 1000       | 0           | 0            | 0                 |
```

**Cambia en tu corrida** nada.

## Paso 2. Crear la rama

**Celda 2.1**

**Se escribe**

```sql
ALTER TABLE recepcion_lab06 CREATE BRANCH revision_junio
```

**En consola** `Listo. La sentencia se ejecutó.`

**Cambia en tu corrida** nada.

---

**Celda 2.2**

**Se escribe**

```sql
SELECT name, type, snapshot_id
FROM mi_espacio.recepcion_lab06.refs
ORDER BY type, name
```

**En consola**

```
| name           | type   | snapshot_id         |
| main           | BRANCH | 1276068155314944172 |
| revision_junio | BRANCH | 1276068155314944172 |
```

**Cambia en tu corrida** los identificadores.

## Paso 3. Escribir en la rama

**Celda 3.1**

**Se escribe**

```sql
INSERT INTO mi_espacio.recepcion_lab06.branch_revision_junio
SELECT * FROM curso.recepcion_sospechosa
```

**En consola** `Listo. La sentencia se ejecutó.`

**Cambia en tu corrida** nada.

---

**Celda 3.2**

**Se escribe**

```sql
SELECT count(*)         AS documentos,
       sum(monto_total) AS total_del_mes
FROM recepcion_lab06 VERSION AS OF 'revision_junio'
```

**En consola**

```
| documentos | total_del_mes  |
| 1500       | 13693496696.68 |
```

**Cambia en tu corrida** nada.

---

**Celda 3.3**

**Se escribe**

```sql
SELECT count(*)         AS documentos,
       sum(monto_total) AS total_del_mes
FROM recepcion_lab06
```

**En consola**

```
| documentos | total_del_mes |
| 1000       | 9117709433.18 |
```

**Cambia en tu corrida** nada.

## Paso 4. Auditar

**Celda 4.1**

**Se escribe**

```sql
SELECT count(*) AS documentos,
       sum(CASE WHEN abs(monto_iva - round(monto_neto * 0.19)) > 2
                THEN 1 ELSE 0 END) AS errores_iva,
       sum(CASE WHEN abs(monto_total - (monto_neto + monto_exento + monto_iva)) > 2
                THEN 1 ELSE 0 END) AS errores_suma,
       sum(CASE WHEN monto_total < 0 AND tipo_dte <> 61
                THEN 1 ELSE 0 END) AS errores_negativos
FROM recepcion_lab06 VERSION AS OF 'revision_junio'
```

**En consola**

```
| documentos | errores_iva | errores_suma | errores_negativos |
| 1500       | 13          | 20           | 7                 |
```

**Cambia en tu corrida** nada.

---

**Celda 4.2**

**Se escribe**

```sql
SELECT count(*) AS documentos_que_no_cuadran
FROM recepcion_lab06 VERSION AS OF 'revision_junio'
WHERE abs(monto_iva - round(monto_neto * 0.19)) > 2
   OR abs(monto_total - (monto_neto + monto_exento + monto_iva)) > 2
   OR (monto_total < 0 AND tipo_dte <> 61)
```

**En consola**

```
| documentos_que_no_cuadran |
| 20                        |
```

**Cambia en tu corrida** nada.

## Paso 5. Decidir, descartar

**Celda 5.1**

**Se escribe**

```sql
ALTER TABLE recepcion_lab06 DROP BRANCH revision_junio
```

**En consola** `Listo. La sentencia se ejecutó.`

**Cambia en tu corrida** nada.

---

**Celda 5.2**

**Se escribe**

```sql
SELECT count(*) AS documentos,
       sum(CASE WHEN abs(monto_iva - round(monto_neto * 0.19)) > 2
                THEN 1 ELSE 0 END) AS errores_iva,
       sum(CASE WHEN abs(monto_total - (monto_neto + monto_exento + monto_iva)) > 2
                THEN 1 ELSE 0 END) AS errores_suma,
       sum(CASE WHEN monto_total < 0 AND tipo_dte <> 61
                THEN 1 ELSE 0 END) AS errores_negativos
FROM recepcion_lab06
```

**En consola**

```
| documentos | errores_iva | errores_suma | errores_negativos |
| 1000       | 0           | 0            | 0                 |
```

**Cambia en tu corrida** nada.

---

**Celda 5.3**

**Se escribe**

```sql
SELECT name, type
FROM mi_espacio.recepcion_lab06.refs
ORDER BY type, name
```

**En consola**

```
| name | type   |
| main | BRANCH |
```

**Cambia en tu corrida** nada.

## Paso 5 (continúa). Decidir, corregir y publicar

**Celda 5.4**

**Se escribe**

```sql
ALTER TABLE recepcion_lab06 CREATE BRANCH revision_junio_v2
```

**En consola** `Listo. La sentencia se ejecutó.`

**Cambia en tu corrida** nada.

---

**Celda 5.5**

**Se escribe**

```sql
INSERT INTO mi_espacio.recepcion_lab06.branch_revision_junio_v2
SELECT * FROM curso.recepcion_sospechosa
WHERE abs(monto_iva - round(monto_neto * 0.19)) <= 2
  AND abs(monto_total - (monto_neto + monto_exento + monto_iva)) <= 2
  AND (monto_total >= 0 OR tipo_dte = 61)
```

**En consola** `Listo. La sentencia se ejecutó.`

**Cambia en tu corrida** nada.

---

**Celda 5.6**

**Se escribe**

```sql
SELECT count(*) AS documentos,
       sum(CASE WHEN abs(monto_iva - round(monto_neto * 0.19)) > 2
                THEN 1 ELSE 0 END) AS errores_iva,
       sum(CASE WHEN abs(monto_total - (monto_neto + monto_exento + monto_iva)) > 2
                THEN 1 ELSE 0 END) AS errores_suma,
       sum(CASE WHEN monto_total < 0 AND tipo_dte <> 61
                THEN 1 ELSE 0 END) AS errores_negativos
FROM recepcion_lab06 VERSION AS OF 'revision_junio_v2'
```

**En consola**

```
| documentos | errores_iva | errores_suma | errores_negativos |
| 1480       | 0           | 0            | 0                 |
```

**Cambia en tu corrida** nada.

---

**Celda 5.7**

**Se escribe**

```sql
SELECT snapshot_id
FROM mi_espacio.recepcion_lab06.refs
WHERE name = 'revision_junio_v2'
```

**En consola**

```
| snapshot_id         |
| 5971121042725466227 |
```

**Cambia en tu corrida** el identificador, siempre.

---

**Celda 5.8**

**Se escribe**

```sql
ALTER TABLE recepcion_lab06 REPLACE BRANCH main AS OF VERSION <TU_SNAPSHOT_DE_LA_RAMA>
```

**En consola** `Listo. La sentencia se ejecutó.`

**Cambia en tu corrida** el número que escribiste, que es el de tu propia tabla.

---

**Celda 5.9**

**Se escribe**

```sql
SELECT count(*) AS documentos,
       sum(CASE WHEN abs(monto_iva - round(monto_neto * 0.19)) > 2
                THEN 1 ELSE 0 END) AS errores_iva,
       sum(CASE WHEN abs(monto_total - (monto_neto + monto_exento + monto_iva)) > 2
                THEN 1 ELSE 0 END) AS errores_suma,
       sum(CASE WHEN monto_total < 0 AND tipo_dte <> 61
                THEN 1 ELSE 0 END) AS errores_negativos
FROM recepcion_lab06
```

**En consola**

```
| documentos | errores_iva | errores_suma | errores_negativos |
| 1480       | 0           | 0            | 0                 |
```

**Cambia en tu corrida** nada.

---

**Celda 5.10**

**Se escribe**

```sql
ALTER TABLE recepcion_lab06 DROP BRANCH revision_junio_v2
```

**En consola** `Listo. La sentencia se ejecutó.`

**Cambia en tu corrida** nada.

## Paso 6. Etiquetar el cierre

**Celda 6.1**

**Se escribe**

```sql
ALTER TABLE recepcion_lab06 CREATE TAG cierre_junio_2026
```

**En consola** `Listo. La sentencia se ejecutó.`

**Cambia en tu corrida** nada.

---

**Celda 6.2**

**Se escribe**

```sql
SELECT count(*)         AS documentos,
       sum(monto_total) AS total_del_mes
FROM recepcion_lab06 VERSION AS OF 'cierre_junio_2026'
```

**En consola**

```
| documentos | total_del_mes  |
| 1480       | 13576071743.67 |
```

**Cambia en tu corrida** nada.

---

**Celda 6.3**

**Se escribe**

```sql
SELECT name, type, snapshot_id
FROM mi_espacio.recepcion_lab06.refs
ORDER BY type, name
```

**En consola**

```
| name              | type   | snapshot_id         |
| main              | BRANCH | 5971121042725466227 |
| cierre_junio_2026 | TAG    | 5971121042725466227 |
```

**Cambia en tu corrida** los identificadores.