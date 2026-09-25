# Laboratorio 10. Dos escritores al mismo tiempo

Las celdas SQL llevan `%%sql` en la primera línea y una sola sentencia por celda. Las
celdas 1.1 y 2.1 son de Python y ya vienen escritas.

Antes de empezar, deja la tabla como recién creada, desde la carpeta del repositorio.

```bash
bin/reiniciar-lab.sh 10
```

## Paso 0. La tabla compartida

**Celda 0.1**

**Se escribe**

```sql
SELECT * FROM curso.escritores_lab10 ORDER BY rut
```

**En consola** cuatro contribuyentes, después de los avisos de arranque de Spark.

```
| rut        | razon_social             | segmento |
| 76171162-8 | Huemul Alimentos EIRL    | GRANDE   |
| 77746521-K | Pehuen Logistica EIRL    | MICRO    |
| 77884562-8 | Araucaria Ferreteria SpA | PEQUENA  |
| 78800840-6 | Copihue Maquinarias EIRL | MEDIANA  |
4 filas.
```

**Cambia en tu corrida** nada.

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
| 7355731461086440536 | 2026-09-25 18:05:23.416 | append    |
1 fila.
```

**Cambia en tu corrida** el identificador y la fecha, que son los de la última vez que
se repuso la tabla.

## Paso 1. Dos escritores insertan a la vez

**Celda 1.1**

**Se escribe** (ya viene escrita).

```python
import threading

def escribe(nombre):
    spark.sql(
        f"INSERT INTO curso.escritores_lab10 VALUES "
        f"('99000001-1', 'Escritor {nombre} SpA', 'MICRO')"
    )
    print(nombre, "escribio")

hilos = [threading.Thread(target=escribe, args=(n,)) for n in ("uno", "dos")]
for h in hilos:
    h.start()
for h in hilos:
    h.join()

print("los dos terminaron")
```

**En consola** los dos hilos escriben y a ninguno le falla.

```
dos escribio
uno escribio
los dos terminaron
```

**Cambia en tu corrida** el orden en que terminan los dos hilos.

> **A mano, con dos pestañas.** Duplica el cuaderno (clic derecho sobre `lab-10.ipynb`,
> **Duplicate**) y abre `lab-10-Copy1.ipynb` en otra pestaña del navegador. Cada cuaderno
> tiene su propio kernel, así que son dos escritores. En una celda nueva de cada pestaña
> escribe el `INSERT` con un nombre distinto y ejecútalas una tras otra. Las dos dicen
> `Listo. La sentencia se ejecutó.` y la tabla queda con dos filas más de las que
> muestran las celdas siguientes.
>
> ```sql
> INSERT INTO curso.escritores_lab10 VALUES
>     ('99000001-1', 'Escritor pestaña uno SpA', 'MICRO')
> ```

---

**Celda 1.2**

**Se escribe**

```sql
SELECT count(*) AS filas FROM curso.escritores_lab10
```

**En consola**

```
| filas |
| 6     |
1 fila.
```

**Cambia en tu corrida** nada.

---

**Celda 1.3**

**Se escribe**

```sql
SELECT snapshot_id, committed_at, operation
FROM curso.escritores_lab10.snapshots
ORDER BY committed_at
```

**En consola** la página inicial más una por cada hilo, todas `append`.

```
| snapshot_id         | committed_at            | operation |
| 7355731461086440536 | 2026-09-25 18:05:23.416 | append    |
| 6046838079518803208 | 2026-09-25 18:09:09.544 | append    |
| 5186261370086278124 | 2026-09-25 18:09:09.858 | append    |
3 filas.
```

**Cambia en tu corrida** los identificadores y las fechas.

## Paso 2. Los dos corrigen la misma fila

**Celda 2.1**

**Se escribe** (ya viene escrita).

```python
import threading

def corrige(nombre, segmento):
    try:
        spark.sql(
            f"UPDATE curso.escritores_lab10 SET segmento = '{segmento}' "
            f"WHERE rut = '77746521-K'"
        )
        print(nombre, "corrigio a", segmento)
    except Exception as error:
        lineas = str(error).splitlines()
        print(nombre, "NO pudo:", lineas[0][:90])
        causa = [l.strip() for l in lineas if "ValidationException" in l]
        if causa:
            print(causa[0])

hilos = [
    threading.Thread(target=corrige, args=("uno", "GRANDE")),
    threading.Thread(target=corrige, args=("dos", "PEQUENA")),
]
for h in hilos:
    h.start()
for h in hilos:
    h.join()

print("los dos terminaron")
```

**En consola** a un hilo le resulta y al otro le sale el error, con la línea de la causa.

```
uno corrigio a GRANDE
26/09/25 18:09:12 ERROR ReplaceDataExec: Data source write support IcebergBatchWrite(table=spark_catalog.curso.escritores_lab10, format=PARQUET) is aborting.
26/09/25 18:09:12 ERROR ReplaceDataExec: Data source write support IcebergBatchWrite(table=spark_catalog.curso.escritores_lab10, format=PARQUET) aborted.
dos NO pudo: An error occurred while calling o39.sql.
Caused by: org.apache.iceberg.exceptions.ValidationException: Found conflicting files that can contain records matching ref(name="rut") == "77746521-K": [hdfs://namenode:8020/warehouse/iceberg/curso.db/escritores_lab10/data/00003-11-b5262010-d20e-4613-bd26-2794f5407040-00001.parquet]
los dos terminaron
```

**Cambia en tu corrida** cuál de los dos gana, las horas y el nombre del archivo.

---

**Celda 2.2**

**Se escribe**

```sql
SELECT * FROM curso.escritores_lab10 WHERE rut = '77746521-K'
```

**En consola** una fila, con el segmento del que ganó.

```
| rut        | razon_social          | segmento |
| 77746521-K | Pehuen Logistica EIRL | GRANDE   |
1 fila.
```

**Cambia en tu corrida** el segmento, `GRANDE` si ganó el hilo uno y `PEQUENA` si ganó el dos.

---

**Celda 2.3**

**Se escribe**

```sql
SELECT made_current_at, snapshot_id, is_current_ancestor
FROM curso.escritores_lab10.history
ORDER BY made_current_at
```

**En consola** las tres páginas del paso 1 más **una sola** del paso 2, todas con
`is_current_ancestor` en `True`.

```
| made_current_at         | snapshot_id         | is_current_ancestor |
| 2026-09-25 18:05:23.416 | 7355731461086440536 | True                |
| 2026-09-25 18:09:09.544 | 6046838079518803208 | True                |
| 2026-09-25 18:09:09.858 | 5186261370086278124 | True                |
| 2026-09-25 18:09:12.000 | 1568745537035200151 | True                |
4 filas.
```

**Cambia en tu corrida** los identificadores y las fechas.

## Paso 3. Concurrencia optimista

**Se escribe** nada.

**En consola** nada.

**Cambia en tu corrida** nada.
