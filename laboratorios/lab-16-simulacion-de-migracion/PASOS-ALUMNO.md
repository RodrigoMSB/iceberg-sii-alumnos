# Laboratorio 16. Simulación de migración

Cada celda lleva `%%sql` en la primera línea y una sola sentencia por celda.

## Paso 0. Qué es migrar, y qué es la marca de agua

**Se escribe** nada.

**En consola** nada.

**Varía entre alumnos** nada.

## Paso 1. Mirar el origen

**Celda 1.1**

**Se escribe** (cada uno el suyo).

```sql
USE mi_espacio
```

**En consola** `Listo. La sentencia se ejecutó.` Primera celda del día.

**Varía entre alumnos** el nombre que escribió cada uno.

---

**Celda 1.2**

**Se escribe**

```sql
CREATE TEMPORARY VIEW origen_pg USING jdbc OPTIONS (
    url      'jdbc:postgresql://iceberg-postgres:5432/origen',
    dbtable  'contribuyentes',
    user     'lector',
    password ''
)
```

**En consola** `Listo. La sentencia se ejecutó.` La clave va vacía a propósito.

**Varía entre alumnos** nada.

---

**Celda 1.3**

**Se escribe**

```sql
SELECT * FROM origen_pg ORDER BY rut
```

**En consola** veinte contribuyentes, todos con `actualizado_en` del 1 de septiembre.

```
| rut        | razon_social               | segmento | actualizado_en      |
| 76000262-3 | Boldo Importadora EIRL     | MICRO    | 2026-09-01 08:00:00 |
| 76000503-7 | Calafate Ferreteria EIRL   | PEQUENA  | 2026-09-01 08:05:00 |
| 76002248-9 | Andes Consultores SpA      | MEDIANA  | 2026-09-01 08:10:00 |
| 76002652-2 | Calafate Constructora S.A. | GRANDE   | 2026-09-01 08:15:00 |
| ...        |                            |          |                     |
| 76016523-9 | Andes Maquinarias EIRL     | GRANDE   | 2026-09-01 09:35:00 |
20 filas.
```

**Varía entre alumnos** nada.

## Paso 2. Carga inicial

**Celda 2.1**

**Se escribe**

```sql
DROP TABLE IF EXISTS contribuyentes_lab16
```

**En consola** `Listo. La sentencia se ejecutó.`

**Varía entre alumnos** nada.

---

**Celda 2.2**

**Se escribe**

```sql
CREATE TABLE contribuyentes_lab16 USING iceberg AS
SELECT * FROM origen_pg
```

**En consola** `Listo. La sentencia se ejecutó.` Es de las celdas más lentas, un par de
segundos.

**Varía entre alumnos** nada.

---

**Celda 2.3**

**Se escribe**

```sql
SELECT count(*) AS contribuyentes FROM contribuyentes_lab16
```

**En consola**

```
| contribuyentes |
| 20             |
```

**Varía entre alumnos** nada.

---

**Celda 2.4**

**Se escribe**

```sql
SELECT max(actualizado_en) AS marca_de_agua FROM contribuyentes_lab16
```

**En consola**

```
| marca_de_agua       |
| 2026-09-01 09:35:00 |
```

**Varía entre alumnos** nada.

## Paso 3. El origen sigue vivo

**Se escribe** nada.

**En consola** nada.

**Varía entre alumnos** nada.

## Paso 4. Detectar qué cambió

**Celda 4.1**

**Se escribe** (con la marca de agua que anotaron).

```sql
SELECT * FROM origen_pg
WHERE actualizado_en > TIMESTAMP '2026-09-01 09:35:00'
ORDER BY rut
```

**En consola** cinco filas.

```
| rut        | razon_social           | segmento | actualizado_en      |
| 76000262-3 | Boldo Importadora EIRL | PEQUENA  | 2026-09-15 12:00:00 |
| 76002248-9 | Andes Consultores SpA  | GRANDE   | 2026-09-15 12:00:00 |
| 76005135-7 | Huemul Servicios SpA   | MEDIANA  | 2026-09-15 12:00:00 |
| 77129445-1 | Lenga Transportes SpA  | MICRO    | 2026-09-15 12:00:00 |
| 78440174-7 | Copihue Alimentos EIRL | PEQUENA  | 2026-09-15 12:00:00 |
5 filas.
```

**Varía entre alumnos** nada.

## Paso 5. Carga incremental

**Celda 5.1**

**Se escribe** (con la misma marca de agua).

```sql
MERGE INTO contribuyentes_lab16 AS destino
USING (
    SELECT * FROM origen_pg
    WHERE actualizado_en > TIMESTAMP '2026-09-01 09:35:00'
) AS origen
ON destino.rut = origen.rut
WHEN MATCHED THEN UPDATE SET
    destino.razon_social   = origen.razon_social,
    destino.segmento       = origen.segmento,
    destino.actualizado_en = origen.actualizado_en
WHEN NOT MATCHED THEN INSERT *
```

**En consola** `Listo. La sentencia se ejecutó.` Es la celda más lenta del laboratorio,
unos segundos.

**Varía entre alumnos** nada.

---

**Celda 5.2**

**Se escribe**

```sql
SELECT count(*) AS contribuyentes FROM contribuyentes_lab16
```

**En consola**

```
| contribuyentes |
| 22             |
```

**Varía entre alumnos** nada.

## Paso 6. Validar

**Celda 6.1**

**Se escribe**

```sql
SELECT
    (SELECT count(*) FROM origen_pg)                                        AS filas_origen,
    (SELECT count(*) FROM contribuyentes_lab16)                             AS filas_iceberg,
    (SELECT sum(crc32(concat(rut, razon_social, segmento))) FROM origen_pg) AS control_origen,
    (SELECT sum(crc32(concat(rut, razon_social, segmento))) FROM contribuyentes_lab16) AS control_iceberg
```

**En consola** los cuatro números, y los pares cuadran.

```
| filas_origen | filas_iceberg | control_origen | control_iceberg |
| 22           | 22            | 39995702816    | 39995702816     |
```

**Varía entre alumnos** nada.

## Paso 7. Lo que quedó escrito

**Celda 7.1**

**Se escribe** (con su propia database).

```sql
SELECT snapshot_id, committed_at, operation
FROM mi_espacio.contribuyentes_lab16.snapshots
ORDER BY committed_at
```

**En consola** dos páginas.

```
| snapshot_id         | committed_at            | operation |
| 4587895169207763573 | 2026-09-15 20:04:05.625 | append    |
| 8947180928895479897 | 2026-09-15 20:04:13.919 | overwrite |
2 filas.
```

**Varía entre alumnos** los dos identificadores y las dos fechas.
