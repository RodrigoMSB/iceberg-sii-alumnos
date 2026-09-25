# Apache Iceberg — el laboratorio del curso, en tu máquina

Este repositorio trae **el ambiente completo y los dieciocho laboratorios** del curso,
para que los repitas por tu cuenta, a tu ritmo y las veces que quieras.

No necesitas servidores ni cuentas en ninguna parte: todo corre en tu propio computador,
dentro de Docker, y se apaga cuando terminas.

---

## 1. Lo que necesitas

| | Mínimo | Recomendado |
|---|---|---|
| **Docker Desktop** | instalado y corriendo | — |
| **Memoria libre** | 8 GB | 12 GB |
| **Disco libre** | **unos 10 GB** | 15 GB si vas a hacer el laboratorio 17 |
| **Procesador** | Intel o ARM | cualquiera de los dos sirve |

El ambiente se probó en un Mac con procesador Apple. En un Mac Intel o en Windows con WSL2
debería funcionar, pero no se probó.

### Cuánta memoria le das a Docker

Docker Desktop reparte la memoria de tu máquina, y por omisión a veces deja poca. El
ambiente pide **8 GB** para andar cómodo.

En Docker Desktop, entra a **Settings → Resources** y sube **Memory** a 8 GB o más. Si tu
máquina tiene 16 GB, deja 8; si tiene 8 GB, deja 6 y cierra lo demás mientras trabajas.

### En Windows: primero WSL2

Docker Desktop en Windows necesita **WSL2**, que es el Linux que Windows trae adentro.

1. Abre **PowerShell como administrador** y corre:

   ```powershell
   wsl --install
   ```

2. Reinicia el computador cuando te lo pida.
3. Instala **Docker Desktop** desde su sitio. En la instalación, deja marcada la opción
   **Use WSL 2 based engine**.
4. Abre Docker Desktop y espera a que el ícono de la ballena deje de moverse.
5. **Trabaja dentro de WSL**, no en `C:\`. Abre la aplicación **Ubuntu** y clona el
   repositorio ahí. Si lo clonas en `C:\` todo anda mucho más lento, porque Docker tiene
   que cruzar dos sistemas de archivos en cada lectura.

---

## 2. Levantar el ambiente

```bash
git clone <la dirección que te pasaron> iceberg-sii-alumnos
cd iceberg-sii-alumnos

cp .env.example .env        # y cambia el token por uno tuyo
bin/ambiente.sh arriba
```

**La primera vez demora unos 9 minutos, y es normal.** No se colgó: está construyendo las
tres imágenes del ambiente, y una de ellas baja Spark, que son unos 300 MB. Vas a ver pasar
líneas de Docker todo ese rato; si tu conexión es lenta puede tomar algo más.

**Las veces siguientes levanta en menos de un minuto**, porque las imágenes ya están
construidas y no se vuelven a bajar.

### Cómo sabes que quedó listo

El propio comando te espera y te avisa. Cuando termina imprime:

```
  OK   el ambiente esta arriba

  Abre JupyterLab en:  http://localhost:8888/
```

Si quieres mirarlo en cualquier momento:

```bash
bin/ambiente.sh estado
```

Los seis servicios tienen que decir `healthy`. Si alguno dice `starting`, dale un minuto
más; si dice `unhealthy`, mira qué pasó con `docker logs <nombre del servicio>`.

### Los datos, una sola vez

```bash
bin/cargar-datos.sh
```

Genera los dos millones de documentos tributarios sintéticos del curso y los deja
cargados. **Se hace una sola vez**: después quedan guardados aunque apagues el ambiente.

Demora **unos dos minutos**, más lo que tome compilar el programa Scala del laboratorio
09 la primera vez, que baja sbt y sus dependencias y se puede ir a cinco o diez minutos
más. Eso también queda hecho para siempre.

Son los mismos datos del curso, con la misma semilla, así que **los números que te van a
salir son los mismos que salieron en clase**.

---

## 3. Abrir Jupyter y por dónde empezar

Abre **http://localhost:8888/** y escribe el token que pusiste en tu `.env`.

Vas a ver una carpeta `laboratorios/`, con uno por cada laboratorio del curso. Dentro de
cada uno hay tres cosas:

| | Qué es |
|---|---|
| `practica/lab-NN.ipynb` | **el que trabajas**: las celdas vienen vacías y tú escribes |
| `solucion/lab-NN.ipynb` | el mismo, resuelto y ejecutado, con las salidas |
| `PASOS-ALUMNO.md` | lo que escribe en cada celda y lo que debe salir |

**Hazlos en orden, del 00 al 17.** Cada laboratorio es autocontenido —su paso 0 crea y
carga lo suyo— así que no se rompe nada si repites uno o te saltas otro, pero el orden es
el que va construyendo las ideas.

| Lab | Nombre | De qué se trata |
|---|---|---|
| 00 | Tu primera libreta | El entorno y las primeras tablas |
| 01 | La tabla que recuerda | Viaje en el tiempo y reversión |
| 02 | Cómo está hecha la libreta | La arquitectura por dentro, y dos motores · **necesita `--sql`** |
| 03 | El folio que llegó dos veces | Escribir, corregir y fusionar |
| 04 | Buscar sin dar vuelta el almacén | Particionamiento y su evolución |
| 05 | La columna que no existía | Evolución de esquema |
| 06 | Publicar solo si cuadra | Ramas, auditoría y etiquetas |
| 07 | Mudarse sin cerrar el negocio | Migración desde Hive · **necesita `--sql`** |
| 08 | Dejar la libreta ordenada | Mantención y optimización |
| 09 | La libreta desde Scala | Iceberg sin Spark, desde un programa propio |
| 10 | Dos escritores al mismo tiempo | Concurrencia y conflicto |
| 11 | El disco lleno | Lo que ocupan las páginas viejas |
| 12 | El panel del administrador | Ocho consultas de salud |
| 13 | Ordenar sin particionar | Orden por rango |
| 14 | Qué cambió desde ayer | Lectura incremental |
| 15 | El caso Contraloría | El examen: reconstruir la historia de un dato |
| 16 | Simulación de migración | Carga inicial, marca de agua y validación |
| 17 | Diez años de verdad | Diez millones de filas, con el reloj a la vista · **ver §5** |

---

## 4. Los laboratorios 02 y 07 necesitan un servicio más

Esos dos consultan la misma tabla desde **un segundo motor**, para mostrar que la tabla no
le pertenece a ninguno. Ese segundo motor son Hue y el Spark Thrift Server, que suman
cerca de 2 GB de memoria y por eso no se levantan siempre.

```bash
bin/ambiente.sh arriba --sql
```

Hue queda en **http://localhost:8889/**. La primera vez que entras te pide crear un
usuario: pon el que quieras, es tuyo y local.

Cuando termines esos dos laboratorios puedes volver al ambiente liviano con
`bin/ambiente.sh abajo` y después `bin/ambiente.sh arriba`.

> **Si tu Mac tiene procesador Apple**, Hue va a andar lento: es el único servicio del
> ambiente que no tiene versión para ARM y corre emulado. Arranca en uno o dos minutos en
> vez de veinte segundos. El resto del ambiente es nativo y va a toda velocidad.

---

## 5. El laboratorio 17, aparte

El 17 trabaja con **diez millones de documentos y diez años de historia**, para que se
note la diferencia entre un diseño bueno y uno malo. Esos datos no vienen cargados porque
demoran y ocupan:

```bash
bin/crear-bodega.sh             # unos 8 minutos, deja cerca de 500 MB en el ambiente
bin/reponer-fragmentada.sh      # unos 10 minutos, para el paso 4
```

Si no piensas hacer el 17, no los corras y te ahorras el disco y la espera.

---

## 6. Repetir un laboratorio

Casi todos empiezan con un `DROP TABLE IF EXISTS`, así que **basta con volver a correr el
cuaderno desde arriba**. Si prefieres partir limpio:

```bash
bin/reiniciar-lab.sh 03      # borra las tablas del laboratorio 03
bin/reiniciar-lab.sh todos   # borra todas las tablas tuyas
```

Cuatro necesitan además otra cosa:

| Lab | Antes de repetirlo |
|---|---|
| **07** | **obligatorio**: `bin/reiniciar-lab.sh 07` |
| 10 | `bin/reiniciar-lab.sh 10` repone la tabla compartida |
| 16 | `bin/mover-origen-lab16.sh --reset` deja el origen como al principio |
| 17 | `bin/reponer-fragmentada.sh` vuelve a fragmentar la tabla del paso 4 |

> **El 07 es el único que no se puede repetir solo volviendo a correr el cuaderno.**
> Empieza creando una tabla Hive, y Hive se niega a crear una tabla donde ya hay una
> carpeta: `DROP TABLE` borra la tabla del catálogo pero deja sus archivos. Si lo intentas
> sin reiniciar, la celda 0.4 falla con *the associated location already exists* y de ahí
> en adelante no funciona nada. `bin/reiniciar-lab.sh 07` borra la tabla y también su
> carpeta, en ese orden.

**El laboratorio 16 tiene un paso a mitad de camino.** Entre el paso 2 y el paso 4 hay que
mover el origen, que en clase lo hacía el instructor. Aquí lo haces tú, desde una terminal,
cuando el cuaderno te lo diga:

```bash
bin/mover-origen-lab16.sh
```

---

## 7. Apagar sin perder nada

```bash
bin/ambiente.sh abajo
```

Apaga los servicios y **no borra nada**: tus tablas, los datos del curso y lo que hayas
guardado quedan ahí. Al volver a levantar está todo como lo dejaste.

Es lo que conviene hacer al terminar de trabajar, porque el ambiente apagado no consume
memoria.

---

## 8. Borrar todo y partir de cero

```bash
bin/ambiente.sh borrar-todo
```

> ## ⚠️ ESTO BORRA TODO Y NO HAY VUELTA ATRÁS
>
> **Se pierden, sin poder recuperarlos:**
>
> - **todas las tablas que creaste** en tu base `mi_espacio`
> - **las tablas de referencia** de la base `curso`
> - **la base `origen`** del laboratorio 16
> - **todo lo que hayas guardado** en la carpeta `trabajo/` de Jupyter
>
> **No se pierden** los cuadernos del repositorio: esos viven en `laboratorios/` y se
> vuelven a copiar solos.
>
> Después de borrar hay que volver a levantar el ambiente y **volver a correr
> `bin/cargar-datos.sh`**, que demora unos minutos.

El comando te pide escribir `borrar todo` antes de hacer nada. Si escribes cualquier otra
cosa, no borra.

---

## 9. Cuando algo no anda

| Lo que ves | Qué hacer |
|---|---|
| `Cannot connect to the Docker daemon` | Docker Desktop no está abierto. Ábrelo y espera |
| Un servicio queda en `unhealthy` | `docker logs <servicio>` y mira la última línea |
| Jupyter pide clave y la tuya no sirve | es el `JUPYTER_TOKEN` de tu `.env`, sin comillas |
| El kernel se muere al correr una celda | te faltó memoria: sube la de Docker Desktop a 8 GB |
| Una consulta dice que la tabla no existe | te faltó correr `bin/cargar-datos.sh` |
| El puerto 8888 está ocupado | cambia `JUPYTER_PORT` en tu `.env` y vuelve a levantar |

### Cosas del ambiente que conviene saber

- **El nombre de la tabla va con las tres partes** cuando consultas las vistas del
  sistema: `mi_espacio.mi_tabla.snapshots`, aunque ya hayas hecho `USE`.
- **`TIMESTAMP AS OF` exige la marca completa**, con milisegundos.
- **Cada motor recuerda la tabla que ya leyó** durante unos treinta segundos. Si escribes
  desde Hue y el cuaderno sigue mostrando lo viejo, `REFRESH TABLE mi_tabla` lo resuelve.

---

## 10. Qué hay en este repositorio

```
laboratorios/        los dieciocho, con práctica, solución y los pasos escritos
bin/                 los comandos de arriba
conf/                configuración de Spark, Hive y HDFS
imagenes/            las tres imágenes de Docker que se construyen
datagen/             el generador de los datos sintéticos
cliente-scala/       el programa Scala del laboratorio 09, con su código fuente
docker-compose.yml   los servicios del ambiente
```

Las versiones son las mismas del curso y **no se cambian**: Spark 3.3.4, Iceberg 1.3.0,
Hive Metastore 3.1.3 y Hadoop 3.3.6. Lo que escribas aquí funciona igual en la plataforma
donde vas a trabajar.

---

## 11. Los datos no son reales

Los dos millones de documentos son **sintéticos**, generados para el curso. Los RUT están
en un rango inventado, las razones sociales no existen y ninguna cifra corresponde a un
contribuyente real ni a ningún organismo.
