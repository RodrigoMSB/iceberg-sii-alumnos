# Laboratorio 03. El folio que llegó dos veces

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
DROP TABLE IF EXISTS documentos_lab03
```

**En consola** `Listo. La sentencia se ejecutó.`

**Cambia en tu corrida** nada.

---

**Celda 0.3**

**Se escribe**

```sql
CREATE TABLE documentos_lab03 USING iceberg AS
SELECT * FROM curso.recepcion_lote1
```

**En consola** `Listo. La sentencia se ejecutó.`

**Cambia en tu corrida** nada.

---

**Celda 0.4**

**Se escribe**

```sql
SELECT count(*) AS documentos FROM documentos_lab03
```

**En consola**

```
| documentos |
| 30         |
1 fila.
```

**Cambia en tu corrida** nada.

---

**Celda 0.5**

**Se escribe**

```sql
SELECT rut_emisor, tipo_dte, folio, fecha_recepcion, monto_total, estado_sii
FROM documentos_lab03
ORDER BY rut_emisor, tipo_dte, folio
LIMIT 5
```

**En consola**

```
| rut_emisor | tipo_dte | folio | fecha_recepcion     | monto_total | estado_sii |
| 76030854-4 | 39       | 864   | 2026-06-06 17:23:16 | 29857.10    | ACEPTADO   |
| 76034637-3 | 39       | 860   | 2026-06-08 03:17:22 | 70864.50    | ACEPTADO   |
| 76057484-8 | 33       | 226   | 2026-06-12 00:29:09 | 6972860.93  | ACEPTADO   |
| 76133016-0 | 61       | 12    | 2026-06-10 03:23:20 | -895572.58  | ACEPTADO   |
| 76252637-9 | 33       | 972   | 2026-06-07 08:21:09 | 17190434.17 | ACEPTADO   |
5 filas.
```

**Cambia en tu corrida** nada.

## Paso 1. Llega el lote nuevo

**Celda 1.1**

**Se escribe**

```sql
SELECT count(*) AS documentos FROM curso.recepcion_lote2
```

**En consola**

```
| documentos |
| 20         |
1 fila.
```

**Cambia en tu corrida** nada.

---

**Celda 1.2**

**Se escribe**

```sql
SELECT count(*) AS ya_los_teniamos
FROM curso.recepcion_lote2 AS nuevo
JOIN documentos_lab03 AS actual
  ON  actual.rut_emisor = nuevo.rut_emisor
  AND actual.tipo_dte   = nuevo.tipo_dte
  AND actual.folio      = nuevo.folio
```

**En consola**

```
| ya_los_teniamos |
| 12              |
1 fila.
```

**Cambia en tu corrida** nada.

## Paso 2. El error que hay que ver

**Celda 2.1**

**Se escribe**

```sql
INSERT INTO documentos_lab03 SELECT * FROM curso.recepcion_lote2
```

**En consola** `Listo. La sentencia se ejecutó.`

**Cambia en tu corrida** nada.

---

**Celda 2.2**

**Se escribe**

```sql
SELECT count(*) AS documentos FROM documentos_lab03
```

**En consola**

```
| documentos |
| 50         |
1 fila.
```

**Cambia en tu corrida** nada.

---

**Celda 2.3**

**Se escribe**

```sql
SELECT rut_emisor, tipo_dte, folio, count(*) AS veces
FROM documentos_lab03
GROUP BY rut_emisor, tipo_dte, folio
HAVING count(*) > 1
ORDER BY rut_emisor, tipo_dte, folio
```

**En consola** doce filas, todas con `veces = 2`.

```
| rut_emisor | tipo_dte | folio | veces |
| 76057484-8 | 33       | 226   | 2     |
| 76133016-0 | 61       | 12    | 2     |
| 76705019-4 | 34       | 149   | 2     |
| 76899472-2 | 61       | 28    | 2     |
| 76913181-7 | 39       | 778   | 2     |
| 77612645-4 | 61       | 100   | 2     |
| 77781727-2 | 39       | 15    | 2     |
| 78086012-K | 39       | 223   | 2     |
| 78914770-1 | 61       | 10    | 2     |
| 79068554-7 | 33       | 52    | 2     |
| 79324470-3 | 33       | 16    | 2     |
| 79961054-K | 39       | 889   | 2     |
12 filas.
```

**Cambia en tu corrida** nada.

---

**Celda 2.4**

**Se escribe**

```sql
SELECT rut_emisor, tipo_dte, folio, fecha_recepcion, monto_total, estado_sii
FROM documentos_lab03
WHERE rut_emisor = '76057484-8' AND tipo_dte = 33 AND folio = 226
ORDER BY fecha_recepcion
```

**En consola** **dos filas**, idénticas salvo la fecha de recepción.

```
| rut_emisor | tipo_dte | folio | fecha_recepcion     | monto_total | estado_sii |
| 76057484-8 | 33       | 226   | 2026-06-12 00:29:09 | 6972860.93  | ACEPTADO   |
| 76057484-8 | 33       | 226   | 2026-06-13 15:41:09 | 6972860.93  | ACEPTADO   |
2 filas.
```

**Cambia en tu corrida** nada, ni siquiera el orden.

## Paso 3. Deshacer

**Celda 3.1**

**Se escribe**

```sql
SELECT snapshot_id, committed_at, operation
FROM mi_espacio.documentos_lab03.snapshots
ORDER BY committed_at
```

**En consola** dos páginas.

```
| snapshot_id         | committed_at            | operation |
| 7877079783851262128 | 2026-09-25 18:22:19.586 | append    |
| 8377222337610389612 | 2026-09-25 18:22:21.583 | append    |
2 filas.
```

**Cambia en tu corrida** los identificadores y las fechas, siempre.

---

**Celda 3.2**

**Se escribe** (con tu identificador).

```sql
CALL spark_catalog.system.rollback_to_snapshot('mi_espacio.documentos_lab03', <TU_SNAPSHOT_ID>)
```

**En consola** una fila con dos números.

```
| previous_snapshot_id | current_snapshot_id |
| 8377222337610389612  | 7877079783851262128 |
1 fila.
```

**Cambia en tu corrida** los dos números.

---

**Celda 3.3**

**Se escribe**

```sql
SELECT count(*) AS documentos FROM documentos_lab03
```

**En consola**

```
| documentos |
| 30         |
1 fila.
```

**Cambia en tu corrida** nada.

## Paso 4. La fusión

**Celda 4.1**

**Se escribe**

```sql
MERGE INTO documentos_lab03 AS destino
USING curso.recepcion_lote2 AS origen
  ON  destino.rut_emisor = origen.rut_emisor
  AND destino.tipo_dte   = origen.tipo_dte
  AND destino.folio      = origen.folio
WHEN MATCHED THEN UPDATE SET destino.fecha_recepcion = origen.fecha_recepcion
WHEN NOT MATCHED THEN INSERT *
```

**En consola** `Listo. La sentencia se ejecutó.` Es la celda más lenta del laboratorio,
y aun así es menos de un segundo.

**Cambia en tu corrida** nada.

---

**Celda 4.2**

**Se escribe**

```sql
SELECT count(*) AS documentos FROM documentos_lab03
```

**En consola**

```
| documentos |
| 38         |
1 fila.
```

**Cambia en tu corrida** nada.

---

**Celda 4.3**

**Se escribe**

```sql
SELECT rut_emisor, tipo_dte, folio, fecha_recepcion, monto_total, estado_sii
FROM documentos_lab03
WHERE rut_emisor = '76057484-8' AND tipo_dte = 33 AND folio = 226
```

**En consola** **una sola fila**, con la fecha del reenvío.

```
| rut_emisor | tipo_dte | folio | fecha_recepcion     | monto_total | estado_sii |
| 76057484-8 | 33       | 226   | 2026-06-13 15:41:09 | 6972860.93  | ACEPTADO   |
1 fila.
```

**Cambia en tu corrida** nada.

---

**Celda 4.4**

**Se escribe**

```sql
SELECT count(*) AS folios_repetidos FROM (
    SELECT rut_emisor, tipo_dte, folio
    FROM documentos_lab03
    GROUP BY rut_emisor, tipo_dte, folio
    HAVING count(*) > 1
)
```

**En consola**

```
| folios_repetidos |
| 0                |
1 fila.
```

**Cambia en tu corrida** nada.

## Paso 5. Las otras dos operaciones

**Celda 5.1**

**Se escribe**

```sql
UPDATE documentos_lab03 SET estado_sii = 'REVISADO' WHERE tipo_dte = 61
```

**En consola** `Listo. La sentencia se ejecutó.`

**Cambia en tu corrida** nada.

---

**Celda 5.2**

**Se escribe**

```sql
SELECT estado_sii, count(*) AS documentos
FROM documentos_lab03
GROUP BY estado_sii
ORDER BY estado_sii
```

**En consola**

```
| estado_sii           | documentos |
| ACEPTADO             | 31         |
| ACEPTADO_CON_REPAROS | 2          |
| REVISADO             | 5          |
3 filas.
```

**Cambia en tu corrida** nada.

---

**Celda 5.3**

**Se escribe**

```sql
DELETE FROM documentos_lab03 WHERE monto_total < 0
```

**En consola** `Listo. La sentencia se ejecutó.`

**Cambia en tu corrida** nada.

---

**Celda 5.4**

**Se escribe**

```sql
SELECT count(*) AS documentos FROM documentos_lab03
```

**En consola**

```
| documentos |
| 33         |
1 fila.
```

**Cambia en tu corrida** nada.