# Laboratorio 10. Dos escritores al mismo tiempo

Cada celda lleva `%%sql` en la primera línea y una sola sentencia por celda.

## Paso 0. La tabla compartida

**Celda 0.1**

**Se escribe**

```sql
SELECT * FROM curso.escritores_lab10 ORDER BY rut
```

**En consola** cuatro contribuyentes.

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

**Celda 0.2**

**Se escribe**

```sql
SELECT snapshot_id, committed_at, operation
FROM curso.escritores_lab10.snapshots
ORDER BY committed_at
```

**En consola** una fila.

```
| snapshot_id         | committed_at            | operation |
| 5489459193992190112 | 2026-09-15 20:11:20.607 | append    |
1 fila.
```

**Varía entre alumnos** el identificador y la fecha, que son los de la última vez que se
repuso la tabla.

## Paso 1. Todos insertan a la vez

**Celda 1.1**

**Se escribe** (cada uno con su espacio).

```sql
INSERT INTO curso.escritores_lab10 VALUES
    ('99000001-1', 'Escritor mi_espacio SpA', 'MICRO')
```

**En consola** `Listo. La sentencia se ejecutó.` A nadie le falla.

**Varía entre alumnos** el nombre que escribió cada uno.

---

**Celda 1.2**

**Se escribe**

```sql
SELECT count(*) AS filas FROM curso.escritores_lab10
```

```
| filas |
| 6     |
```

**Varía entre alumnos** nada entre ellos, pero **sí depende de cuántos ejecutaron**.

---

**Celda 1.3**

**Se escribe**

```sql
SELECT snapshot_id, committed_at, operation
FROM curso.escritores_lab10.snapshots
ORDER BY committed_at
```

**En consola** la página inicial más una por cada escritor, todas `append`.

```
| snapshot_id         | committed_at            | operation |
| 5489459193992190112 | 2026-09-15 20:11:20.607 | append    |
| 7638901174419374418 | 2026-09-15 20:12:42.170 | append    |
| 6948472985130829003 | 2026-09-15 20:12:42.599 | append    |
3 filas.
```

**Varía entre alumnos** los identificadores y las fechas.

## Paso 2. Todos corrigen la misma fila

**Celda 2.1**

**Se escribe** (cada uno con su espacio).

```sql
UPDATE curso.escritores_lab10
SET segmento = 'CORREGIDO POR mi_espacio'
WHERE rut = '77746521-K'
```

**En consola** a uno le dice `Listo. La sentencia se ejecutó.` y a los demás les sale un
error largo.

```
org.apache.spark.SparkException: Writing job aborted
```

```
org.apache.iceberg.exceptions.ValidationException: Found conflicting files that can
contain records matching ref(name="rut") == "77746521-K":
[hdfs://namenode:8020/warehouse/iceberg/curso.db/escritores_lab10/data/00002-3-fa44257a-...parquet]
```

**Varía entre alumnos** a quién le falla.

---

**Celda 2.2**

**Se escribe**

```sql
SELECT * FROM curso.escritores_lab10 WHERE rut = '77746521-K'
```

**En consola** una fila, con el nombre del que ganó.

```
| rut        | razon_social          | segmento              |
| 77746521-K | Pehuen Logistica EIRL | CORREGIDO POR mi_espacio |
1 fila.
```

---

**Celda 2.3**

**Se escribe**

```sql
SELECT made_current_at, snapshot_id, is_current_ancestor
FROM curso.escritores_lab10.history
ORDER BY made_current_at
```

**En consola** las páginas del paso 1 más **una sola** del paso 2, y todas con
`is_current_ancestor` en `true`.

```
| made_current_at         | snapshot_id         | is_current_ancestor |
| 2026-09-15 20:11:20.607 | 5489459193992190112 | true                |
| 2026-09-15 20:12:42.170 | 7638901174419374418 | true                |
| 2026-09-15 20:12:42.599 | 6948472985130829003 | true                |
| 2026-09-15 20:14:15.578 | 4242012492127956567 | true                |
4 filas.
```

**Varía entre alumnos** los identificadores y las fechas.

## Paso 3. Concurrencia optimista

**Se escribe** nada.

**En consola** nada.

**Varía entre alumnos** nada.
