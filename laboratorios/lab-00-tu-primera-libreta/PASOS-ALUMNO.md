# Laboratorio 00. Tu primera libreta

Cada celda lleva `%%sql` en la primera línea y una sola sentencia por celda.

## Paso 0. Entrar y mirar alrededor

**Celda 0.1**

**Se escribe**

```sql
SELECT current_database() AS estoy_en
```

**En consola**

```
| estoy_en |
| default  |
1 fila.
```

## Paso 1. Ver qué hay, y ponerte en tu espacio

**Celda 1.1**

**Se escribe**

```sql
SHOW DATABASES
```

**En consola**

```
| namespace  |
| curso      |
| default    |
| mi_espacio |
3 filas.
```

**Cambia en tu corrida** nada.

---

**Celda 1.2**

**Se escribe**

```sql
USE mi_espacio
```

**En consola**

```
Listo. La sentencia se ejecutó.
```

**Cambia en tu corrida** nada.

---

**Celda 1.3**

**Se escribe**

```sql
SELECT current_database() AS estoy_en
```

**En consola**

```
| estoy_en   |
| mi_espacio |
1 fila.
```

**Cambia en tu corrida** nada.

## Paso 2. Crear tu primera tabla

**Celda 2.1**

**Se escribe**

```sql
DROP TABLE IF EXISTS contribuyentes_lab00
```

**En consola**

```
Listo. La sentencia se ejecutó.
```

**Cambia en tu corrida** nada.

---

**Celda 2.2**

**Se escribe**

```sql
CREATE TABLE contribuyentes_lab00 (
    rut           STRING,
    razon_social  STRING,
    segmento      STRING,
    anio_inicio   INT
) USING iceberg
```

**En consola**

```
Listo. La sentencia se ejecutó.
```

**Cambia en tu corrida** nada.

## Paso 3. Escribir tres filas

**Celda 3.1**

**Se escribe**

```sql
INSERT INTO contribuyentes_lab00 VALUES
    ('77884562-8', 'Araucaria Ferreteria SpA', 'PEQUENA', 2018),
    ('78800840-6', 'Copihue Maquinarias EIRL', 'MEDIANA', 2021),
    ('76171162-8', 'Huemul Alimentos EIRL',    'GRANDE',  2011)
```

**En consola**

```
Listo. La sentencia se ejecutó.
```

**Cambia en tu corrida** nada.

## Paso 4. Leerlas

**Celda 4.1**

**Se escribe**

```sql
SELECT * FROM contribuyentes_lab00
```

**En consola**

```
| rut        | razon_social             | segmento | anio_inicio |
| 77884562-8 | Araucaria Ferreteria SpA | PEQUENA  | 2018        |
| 78800840-6 | Copihue Maquinarias EIRL | MEDIANA  | 2021        |
| 76171162-8 | Huemul Alimentos EIRL    | GRANDE   | 2011        |
3 filas.
```

**Cambia en tu corrida** nada.