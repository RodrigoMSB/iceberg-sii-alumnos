# Laboratorio 01. La tabla que recuerda

Cada celda lleva `%%sql` en la primera línea y una sola sentencia por celda.

## Paso 0. Preparar la tabla

**Celda 0.1**

**Se escribe** (cada uno el suyo).

```sql
USE mi_espacio
```

**En consola**

```
Listo. La sentencia se ejecutó.
```

**Varía entre alumnos** el nombre que escribió cada uno.

---

**Celda 0.2**

**Se escribe**

```sql
DROP TABLE IF EXISTS contribuyentes_lab01
```

**En consola**

```
Listo. La sentencia se ejecutó.
```

**Varía entre alumnos** nada.

---

**Celda 0.3**

**Se escribe**

```sql
CREATE TABLE contribuyentes_lab01 (
    rut           STRING,
    razon_social  STRING,
    segmento      STRING
) USING iceberg
```

**En consola**

```
Listo. La sentencia se ejecutó.
```

**Varía entre alumnos** nada.

---

**Celda 0.4**

**Se escribe**

```sql
INSERT INTO contribuyentes_lab01 VALUES
    ('77746521-K', 'Pehuen Logistica EIRL',    'MICRO'),
    ('77884562-8', 'Araucaria Ferreteria SpA', 'PEQUENA'),
    ('78800840-6', 'Copihue Maquinarias EIRL', 'MEDIANA'),
    ('76171162-8', 'Huemul Alimentos EIRL',    'GRANDE')
```

**En consola**

```
Listo. La sentencia se ejecutó.
```

**Varía entre alumnos** nada.

---

**Celda 0.5**

**Se escribe**

```sql
SELECT * FROM contribuyentes_lab01 ORDER BY rut
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

**Varía entre alumnos** nada.

## Paso 1. Corregir un dato

**Celda 1.1**

**Se escribe**

```sql
UPDATE contribuyentes_lab01 SET segmento = 'MEDIANA' WHERE rut = '77884562-8'
```

**En consola**

```
Listo. La sentencia se ejecutó.
```

**Varía entre alumnos** nada.

---

**Celda 1.2**

**Se escribe**

```sql
SELECT * FROM contribuyentes_lab01 ORDER BY rut
```

**En consola**

```
| rut        | razon_social             | segmento |
| 76171162-8 | Huemul Alimentos EIRL    | GRANDE   |
| 77746521-K | Pehuen Logistica EIRL    | MICRO    |
| 77884562-8 | Araucaria Ferreteria SpA | MEDIANA  |
| 78800840-6 | Copihue Maquinarias EIRL | MEDIANA  |
4 filas.
```

**Varía entre alumnos** nada.

## Paso 2. Descubrir que hay historia

**Celda 2.1**

**Se escribe** (con su propia database en la primera parte).

```sql
SELECT snapshot_id, committed_at, operation
FROM mi_espacio.contribuyentes_lab01.snapshots
ORDER BY committed_at
```

**En consola** dos filas.

```
| snapshot_id         | committed_at            | operation |
| 4719426393852070130 | 2026-08-22 23:16:42.967 | append    |
| 5449379681888003842 | 2026-08-22 23:16:46.343 | overwrite |
2 filas.
```

**Varía entre alumnos** los dos números y las dos fechas, siempre.

## Paso 3. Mirar el pasado

**Celda 3.1**

**Se escribe** (con su propio identificador).

```sql
SELECT * FROM contribuyentes_lab01 VERSION AS OF <TU_SNAPSHOT_ID> ORDER BY rut
```

**En consola** las cuatro filas, y **Araucaria dice PEQUENA otra vez**.

```
| rut        | razon_social             | segmento |
| 76171162-8 | Huemul Alimentos EIRL    | GRANDE   |
| 77746521-K | Pehuen Logistica EIRL    | MICRO    |
| 77884562-8 | Araucaria Ferreteria SpA | PEQUENA  |
| 78800840-6 | Copihue Maquinarias EIRL | MEDIANA  |
4 filas.
```

**Varía entre alumnos** el número que escribió cada uno.

---

**Celda 3.2**

**Se escribe**

```sql
SELECT * FROM contribuyentes_lab01 ORDER BY rut
```

**En consola** las cuatro filas con **Araucaria en MEDIANA**, igual que antes de mirar
al pasado.

```
| rut        | razon_social             | segmento |
| 76171162-8 | Huemul Alimentos EIRL    | GRANDE   |
| 77746521-K | Pehuen Logistica EIRL    | MICRO    |
| 77884562-8 | Araucaria Ferreteria SpA | MEDIANA  |
| 78800840-6 | Copihue Maquinarias EIRL | MEDIANA  |
4 filas.
```

**Varía entre alumnos** nada.

---

**Celda 3.3**

**Se escribe** (con su propia marca de tiempo).

```sql
SELECT * FROM contribuyentes_lab01 TIMESTAMP AS OF '<TU_COMMITTED_AT>' ORDER BY rut
```

**En consola** el mismo resultado del paso anterior, con **Araucaria en PEQUENA**.

```
| rut        | razon_social             | segmento |
| 76171162-8 | Huemul Alimentos EIRL    | GRANDE   |
| 77746521-K | Pehuen Logistica EIRL    | MICRO    |
| 77884562-8 | Araucaria Ferreteria SpA | PEQUENA  |
| 78800840-6 | Copihue Maquinarias EIRL | MEDIANA  |
4 filas.
```

**Varía entre alumnos** la fecha que escribió cada uno.

## Paso 4. Volver atrás de verdad

**Celda 4.1**

**Se escribe** (con su database y su identificador).

```sql
CALL spark_catalog.system.rollback_to_snapshot('mi_espacio.contribuyentes_lab01', <TU_SNAPSHOT_ID>)
```

**En consola** una fila con dos números.

```
| previous_snapshot_id | current_snapshot_id |
| 5449379681888003842  | 4719426393852070130 |
1 fila.
```

**Varía entre alumnos** los dos números.

---

**Celda 4.2**

**Se escribe**

```sql
SELECT * FROM contribuyentes_lab01 ORDER BY rut
```

**En consola** **Araucaria dice PEQUENA**, sin haber pedido ninguna versión.

```
| rut        | razon_social             | segmento |
| 76171162-8 | Huemul Alimentos EIRL    | GRANDE   |
| 77746521-K | Pehuen Logistica EIRL    | MICRO    |
| 77884562-8 | Araucaria Ferreteria SpA | PEQUENA  |
| 78800840-6 | Copihue Maquinarias EIRL | MEDIANA  |
4 filas.
```

**Varía entre alumnos** nada.

---

**Celda 4.3**

**Se escribe** (con su propia database).

```sql
SELECT made_current_at, snapshot_id, is_current_ancestor
FROM mi_espacio.contribuyentes_lab01.history
ORDER BY made_current_at
```

**En consola** **tres** filas, y la del medio con `is_current_ancestor` en `false`.

```
| made_current_at         | snapshot_id         | is_current_ancestor |
| 2026-08-22 23:16:42.967 | 4719426393852070130 | True                |
| 2026-08-22 23:16:46.343 | 5449379681888003842 | False               |
| 2026-08-22 23:16:47.717 | 4719426393852070130 | True                |
3 filas.
```

**Varía entre alumnos** los números y las fechas.
