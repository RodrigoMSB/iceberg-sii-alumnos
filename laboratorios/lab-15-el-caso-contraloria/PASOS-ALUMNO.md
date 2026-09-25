# Laboratorio 15. El caso Contraloría

Cada celda lleva `%%sql` en la primera línea y una sola sentencia por celda.

## Paso 0. Montaje, no leas todavía

**Celda 0.1**

**Se escribe** ya viene escrito en la práctica.

```sql
USE mi_espacio
```

**En consola** `Listo. La sentencia se ejecutó.` Es la primera celda del día.

**Cambia en tu corrida** nada.

---

**Celda 0.2**

**Se escribe** ya viene escrito en la práctica.

```sql
DROP TABLE IF EXISTS contribuyentes_lab15
```

**En consola** `Listo. La sentencia se ejecutó.`

**Cambia en tu corrida** nada.

---

**Celda 0.3**

**Se escribe** ya viene escrito en la práctica.

```sql
CREATE TABLE contribuyentes_lab15 (
    rut           STRING,
    razon_social  STRING,
    segmento      STRING
) USING iceberg
```

**En consola** `Listo. La sentencia se ejecutó.`

**Cambia en tu corrida** nada.

---

**Celda 0.4**

**Se escribe** ya viene escrito en la práctica.

```sql
INSERT INTO contribuyentes_lab15 VALUES
    ('77746521-K', 'Pehuen Logistica EIRL',     'MICRO'),
    ('77884562-8', 'Araucaria Ferreteria SpA',  'PEQUENA'),
    ('78800840-6', 'Copihue Maquinarias EIRL',  'MEDIANA'),
    ('76171162-8', 'Huemul Alimentos EIRL',     'GRANDE'),
    ('76000262-3', 'Boldo Importadora EIRL',    'MICRO'),
    ('76002248-9', 'Andes Consultores SpA',     'MEDIANA'),
    ('76005135-7', 'Huemul Servicios SpA',      'GRANDE'),
    ('76008516-2', 'Boldo Logistica SpA',       'PEQUENA'),
    ('76011940-7', 'Canelo Servicios EIRL',     'MICRO'),
    ('76015893-3', 'Lenga Consultores Ltda.',   'MEDIANA')
```

**En consola** `Listo. La sentencia se ejecutó.`

**Cambia en tu corrida** nada.

---

**Celda 0.5**

**Se escribe** ya viene escrito en la práctica.

```sql
UPDATE contribuyentes_lab15 SET segmento = 'MEDIANA' WHERE rut = '77884562-8'
```

**En consola** `Listo. La sentencia se ejecutó.`

**Cambia en tu corrida** nada.

---

**Celda 0.6**

**Se escribe** ya viene escrito en la práctica.

```sql
INSERT INTO contribuyentes_lab15 VALUES
    ('76004358-3', 'Ulmo Constructora Ltda.',   'PEQUENA'),
    ('76006049-6', 'Canelo Constructora S.A.',  'MEDIANA'),
    ('76007969-3', 'Maiten Alimentos EIRL',     'GRANDE')
```

**En consola** `Listo. La sentencia se ejecutó.`

**Cambia en tu corrida** nada.

---

**Celda 0.7**

**Se escribe** ya viene escrito en la práctica.

```python
# Montaje. Vuelve la libreta a su primera pagina.
#
# Va en Python y no en %%sql por una sola razon: 'CALL' solo acepta literales,
# asi que el identificador de la pagina hay que buscarlo antes y pegarlo dentro
# de la sentencia. Es la funcion auxiliar de la Regla 6 del estandar didactico:
# no es una operacion del trabajo del alumno y su sintaxis no se evalua.
tabla = spark.catalog.currentDatabase() + ".contribuyentes_lab15"

primera = spark.sql(
    "SELECT snapshot_id FROM " + tabla + ".snapshots ORDER BY committed_at LIMIT 1"
).first()[0]

spark.sql(
    "CALL spark_catalog.system.rollback_to_snapshot('" + tabla + "', " + str(primera) + ")"
)
print("Montaje: listo.")
```

**En consola** la celda imprime `Montaje: listo.` y nada más.

```
Montaje: listo.
```

**Cambia en tu corrida** nada.

---

**Celda 0.8**

**Se escribe** ya viene escrito en la práctica.

```sql
UPDATE contribuyentes_lab15 SET segmento = 'GRANDE' WHERE rut = '77884562-8'
```

**En consola** `Listo. La sentencia se ejecutó.`

**Cambia en tu corrida** nada.

---

**Celda 0.9**

**Se escribe** ya viene escrito en la práctica.

```sql
ALTER TABLE contribuyentes_lab15 ADD COLUMN region STRING
```

**En consola** `Listo. La sentencia se ejecutó.` Esta celda **no deja página**, porque
no toca archivos.

**Cambia en tu corrida** nada.

---

**Celda 0.10**

**Se escribe** ya viene escrito en la práctica.

```sql
DELETE FROM contribuyentes_lab15 WHERE rut = '76011940-7'
```

**En consola** `Listo. La sentencia se ejecutó.`

**Cambia en tu corrida** nada.

## Paso 1. El oficio

**Se escribe** nada.

**En consola** nada.

**Cambia en tu corrida** nada.

## Paso 2. Primera pregunta

**Celda 2.1**

**En consola**

```
| rut        | razon_social             | segmento | region |
| 77884562-8 | Araucaria Ferreteria SpA | GRANDE   | NULL   |
1 fila.
```

**Cambia en tu corrida** nada.

## Paso 3. Segunda pregunta

**Celda 3.1**

**En consola** **no devuelve filas, devuelve un error**, y es el correcto.

```
org.apache.iceberg.exceptions.ValidationException:
Cannot find a snapshot older than 2026-06-01T00:00:00+00:00
```

**Cambia en tu corrida** nada.

---

**Celda 3.2**

**En consola** una fila con la fecha de la carga inicial.

```
| desde_cuando_hay_registro |
| 2026-09-15 23:39:21.293   |
```

**Cambia en tu corrida** la fecha, que es la de tu corrida.

## Paso 4. Tercera pregunta

**Celda 4.1**

**En consola** cinco filas.

```
| snapshot_id         | committed_at            | operation |
| 3982178124195812129 | 2026-09-15 23:34:37.582 | append    |
| 5569299777714703742 | 2026-09-15 23:34:41.286 | overwrite |
| 429530069112526782  | 2026-09-15 23:34:41.619 | append    |
| 2328263972627456536 | 2026-09-15 23:34:44.695 | overwrite |
| 8028937501850124557 | 2026-09-15 23:34:46.268 | overwrite |
5 filas.
```

**Cambia en tu corrida** los identificadores y las fechas.

## Paso 5. Cuarta pregunta

**Celda 5.1**

**En consola** seis filas, y dos en `false`.

```
| made_current_at         | snapshot_id         | is_current_ancestor |
| 2026-09-15 23:34:37.582 | 3982178124195812129 | true                |
| 2026-09-15 23:34:41.286 | 5569299777714703742 | false               |
| 2026-09-15 23:34:41.619 | 429530069112526782  | false               |
| 2026-09-15 23:34:42.900 | 3982178124195812129 | true                |
| 2026-09-15 23:34:44.695 | 2328263972627456536 | true                |
| 2026-09-15 23:34:46.268 | 8028937501850124557 | true                |
6 filas.
```

**Cambia en tu corrida** los identificadores y las fechas.

## Paso 6. La respuesta

**Se escribe** nada.

**En consola** nada.

**Cambia en tu corrida** nada.