# Laboratorio 14. Qué cambió desde ayer

Cada celda lleva `%%sql` en la primera línea y una sola sentencia por celda.

## Paso 0. La tabla de hoy

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
DROP TABLE IF EXISTS contribuyentes_lab14
```

**En consola** `Listo. La sentencia se ejecutó.`

**Cambia en tu corrida** nada.

---

**Celda 0.3**

**Se escribe**

```sql
CREATE TABLE contribuyentes_lab14 (
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
INSERT INTO contribuyentes_lab14 VALUES
    ('77746521-K', 'Pehuen Logistica EIRL',    'MICRO'),
    ('77884562-8', 'Araucaria Ferreteria SpA', 'PEQUENA'),
    ('78800840-6', 'Copihue Maquinarias EIRL', 'MEDIANA'),
    ('76171162-8', 'Huemul Alimentos EIRL',    'GRANDE')
```

**En consola** `Listo. La sentencia se ejecutó.`

**Cambia en tu corrida** nada.

## Paso 1. Un día de movimientos

**Celda 1.1**

**Se escribe**

```sql
INSERT INTO contribuyentes_lab14 VALUES
    ('79412337-8', 'Quillay Servicios SpA',  'PEQUENA'),
    ('77129445-1', 'Lenga Transportes SpA',  'MICRO')
```

**En consola** `Listo. La sentencia se ejecutó.`

**Cambia en tu corrida** nada.

---

**Celda 1.2**

**Se escribe**

```sql
UPDATE contribuyentes_lab14
SET segmento = 'MEDIANA'
WHERE rut = '77884562-8'
```

**En consola** `Listo. La sentencia se ejecutó.`

**Cambia en tu corrida** nada.

---

**Celda 1.3**

**Se escribe**

```sql
DELETE FROM contribuyentes_lab14 WHERE rut = '78800840-6'
```

**En consola** `Listo. La sentencia se ejecutó.`

**Cambia en tu corrida** nada.

---

**Celda 1.4**

**Se escribe**

```sql
SELECT snapshot_id, committed_at, operation
FROM mi_espacio.contribuyentes_lab14.snapshots
ORDER BY committed_at
```

**En consola** cuatro filas.

```
| snapshot_id         | committed_at            | operation |
| 2909951952428611620 | 2026-09-25 18:24:57.549 | append    |
| 6810304009964451568 | 2026-09-25 18:24:57.980 | append    |
| 6660392441357658505 | 2026-09-25 18:25:01.066 | overwrite |
| 7477665559979367789 | 2026-09-25 18:25:02.147 | overwrite |
4 filas.
```

**Cambia en tu corrida** los cuatro identificadores y las cuatro fechas, siempre.

## Paso 2. La vista de cambios

**Celda 2.1**

**Se escribe**

```sql
CALL spark_catalog.system.create_changelog_view(table => 'mi_espacio.contribuyentes_lab14')
```

**En consola** el nombre de la vista que acaba de crear.

```
| changelog_view                 |
| `contribuyentes_lab14_changes` |
1 fila.
```

**Cambia en tu corrida** nada.

---

**Celda 2.2**

**Se escribe**

```sql
SELECT * FROM contribuyentes_lab14_changes
ORDER BY _change_ordinal, rut
```

**En consola** nueve filas.

```
| rut        | razon_social             | segmento | _change_type | _change_ordinal | _commit_snapshot_id |
| 76171162-8 | Huemul Alimentos EIRL    | GRANDE   | INSERT       | 0               | 2909951952428611620 |
| 77746521-K | Pehuen Logistica EIRL    | MICRO    | INSERT       | 0               | 2909951952428611620 |
| 77884562-8 | Araucaria Ferreteria SpA | PEQUENA  | INSERT       | 0               | 2909951952428611620 |
| 78800840-6 | Copihue Maquinarias EIRL | MEDIANA  | INSERT       | 0               | 2909951952428611620 |
| 77129445-1 | Lenga Transportes SpA    | MICRO    | INSERT       | 1               | 6810304009964451568 |
| 79412337-8 | Quillay Servicios SpA    | PEQUENA  | INSERT       | 1               | 6810304009964451568 |
| 77884562-8 | Araucaria Ferreteria SpA | MEDIANA  | INSERT       | 2               | 6660392441357658505 |
| 77884562-8 | Araucaria Ferreteria SpA | PEQUENA  | DELETE       | 2               | 6660392441357658505 |
| 78800840-6 | Copihue Maquinarias EIRL | MEDIANA  | DELETE       | 3               | 7477665559979367789 |
9 filas.
```

**Cambia en tu corrida** los identificadores.

## Paso 3. Solo lo de hoy

**Celda 3.1**

**Se escribe** (con tus dos identificadores).

```sql
CALL spark_catalog.system.create_changelog_view(
    table          => 'mi_espacio.contribuyentes_lab14',
    options        => map('start-snapshot-id', '<TU_SEGUNDO_SNAPSHOT_ID>',
                          'end-snapshot-id',   '<TU_ULTIMO_SNAPSHOT_ID>'),
    changelog_view => 'desde_ayer'
)
```

**En consola**

```
| changelog_view |
| desde_ayer     |
1 fila.
```

**Cambia en tu corrida** los dos identificadores que escribiste.

---

**Celda 3.2**

**Se escribe**

```sql
SELECT * FROM desde_ayer
ORDER BY _change_ordinal, rut
```

**En consola** tres filas.

```
| rut        | razon_social             | segmento | _change_type | _change_ordinal | _commit_snapshot_id |
| 77884562-8 | Araucaria Ferreteria SpA | PEQUENA  | DELETE       | 0               | 6660392441357658505 |
| 77884562-8 | Araucaria Ferreteria SpA | MEDIANA  | INSERT       | 0               | 6660392441357658505 |
| 78800840-6 | Copihue Maquinarias EIRL | MEDIANA  | DELETE       | 1               | 7477665559979367789 |
3 filas.
```

**Cambia en tu corrida** los identificadores.

## Paso 4. Cómo lo usa un proceso nocturno

**Se escribe** nada.

**En consola** nada.

**Cambia en tu corrida** nada.