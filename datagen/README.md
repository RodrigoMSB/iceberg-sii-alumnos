# datagen — generador de datos tributarios del universo DGT

Genera los datos sintéticos que alimentan los ocho laboratorios del curso.

> La **DGT** es una administración tributaria **ficticia**. Los RUT son sintéticos
> (rango 76.000.000–79.999.999, válidos por módulo 11), las razones sociales están
> inventadas y ningún dato proviene del SII ni de ningún organismo real.

---

## Uso

```bash
python -m datagen --escala curso --salida datos/
```

| Opción | Valores | Por defecto | Qué hace |
|---|---|---|---|
| `--escala` | `dev`, `curso` | `dev` | `dev` ≈ 100 mil DTEs (segundos); `curso` ≈ 2 millones |
| `--salida` | ruta | `datos/` | Directorio de salida |
| `--semilla` | entero | `20260813` | Misma semilla ⇒ bytes idénticos |
| `--pais` | `chile` | `chile` | Perfil de país |
| `--silencioso` | — | — | No imprime el resumen |
| `--bodega` | — | — | Genera **solo** la bodega del laboratorio 17 y nada más |

Instalación:

```bash
python -m venv .venv && .venv/bin/pip install -e "datagen[dev]"
```

Dependencias: **pyarrow** y biblioteca estándar. Sin pandas, sin generadores de
datos falsos de terceros.

---

## Qué genera

```
datos/
├── manifiesto.json                       # ground truth de la corrida
├── contribuyentes/                       # el padrón
├── dte/
│   ├── lote_historico/anio_mes=2024-01/  # esquema v1, 2024-01 .. 2025-12
│   └── lote_reciente/anio_mes=2026-01/   # esquema v2 (+2 columnas), 2026-01 .. 2026-05
├── f29/                                  # declaraciones con rectificatorias
└── recepcion_diaria/anio_mes=2026-06/    # cientos de archivos chicos
```

Cifras de la escala `curso` (semilla por defecto):

| Dataset | Filas | Archivos |
|---|---:|---:|
| contribuyentes | 10.000 | 1 |
| dte/lote_historico | 1.400.000 | 24 |
| dte/lote_reciente | 400.000 | 5 |
| f29 | 235.597 | 1 |
| recepcion_diaria | 201.000 | 500 |

Tarda **~1 min 20 s** y ocupa **~660 MB**.

---

## La bodega del laboratorio 17

```bash
python -m datagen --bodega --salida datos-bodega/
```

Diez años, de **2015 a 2024**, **un millón de documentos por año**, con el esquema v1 de
siempre. Diez millones de filas en 120 archivos, ~3,1 GB, unos 75 minutos.

**No es el universo DGT y no pretende serlo.** No escribe `manifiesto.json`, no genera
F29 ni recepción diaria, y **se niega a escribir en una carpeta que ya tenga un
manifiesto**, para que nadie la deje caer encima de `datos/`.

Tiene su **propio flujo de azar**, `semilla + 505`, por la misma razón que cada dataset
tiene el suyo: pedirla no corre la secuencia de ningún otro y por lo tanto **no cambia ni
un byte** de lo que ya genera el curso. Eso se comprueba regenerando con las opciones por
omisión y comparando contra lo que hay.

Ampliar `PERIODOS_HISTORICO` para conseguir lo mismo **no** era una opción: esa tupla la
consumen los DTE, el F29 y el manifiesto, y el azar de los DTE es un solo flujo que se
recorre en orden, así que agregar períodos habría cambiado todas las filas de 2024 y
2025 —y con ellas las siete trampas y los números que están commiteados en los
laboratorios.

El padrón sí sale del flujo de siempre, a propósito: con la misma semilla da los mismos
contribuyentes, así que los RUT de la bodega son los del universo DGT.

Las tablas se crean con `bin/42-crear-bodega-10-anios.sh`.

### Decisiones de tipos que los labs dan por sentadas

- **Montos en `decimal(18,2)`**, nunca `float`: los laboratorios comparan igualdad
  exacta de sumas, y en punto flotante eso es una lotería.
- **Fechas como `date` / `timestamp`**, nunca texto. `fecha_emision` es una fecha y
  `fecha_recepcion` un instante, porque la distancia entre ambas es justamente lo
  que estudia el capítulo 5.
- **`anio_mes` es columna de partición** (directorios `anio_mes=2024-01`), como en
  una tabla Hive real: es de ahí que el capítulo 7 migra el histórico. Cómo se
  particiona la tabla Iceberg de destino sigue siendo decisión del alumno.

---

## Las trampas pedagógicas

Los datos **no son aleatorios**: cada anomalía está sembrada para que un laboratorio
tenga un problema real que resolver.

| ID | Trampa | Tasa | Alimenta |
|---|---|---:|---|
| **T-1** | DTEs tardíos: recepción hasta 45 días después de la emisión | 4 % | M5 — particionar por emisión o recepción duele distinto |
| **T-2** | Folios duplicados: el mismo `(rut, tipo, folio)` enviado dos veces | 0,5 % | M4 — el INSERT ingenuo duplica; nace el MERGE |
| **T-3** | Rectificatorias F29: cadenas de 2 a 4 versiones | 8 % | M4 — upsert por llave natural |
| **T-4** | Notas de crédito que anulan facturas de periodos ya cerrados | 2 % | M6 — solo se responde con time travel |
| **T-5** | Montos corruptos: IVA que no cuadra, total que no suma, negativos indebidos | 0,3 % | M6 — el WAP tiene que atrapar algo |
| **T-6** | Evolución de esquema: el lote reciente agrega 2 columnas | estructural | M5 — schema evolution con datos de dos épocas |
| **T-7** | Archivos chicos: 500 Parquet en `recepcion_diaria` | estructural | M8 — compactación con mejora medible |

Las tasas son **exactas, no estadísticas**: el generador calcula el conteo objetivo
sobre el plan de generación antes de escribir una sola fila. Por eso las guías pueden
afirmar *"hay 1.000 folios duplicados: encuéntralos"* y el test del laboratorio puede
validarlo.

### Interacción conocida entre T-1 y T-2

Los duplicados de T-2 copian filas existentes. Si la fila copiada era tardía (T-1), su
copia también lo es, así que el conteo de T-1 se hace **sobre las filas finales
escritas**, no sobre las planificadas. El manifiesto describe los datos que quedaron
en disco, no la intención original.

---

## El manifiesto

`datos/manifiesto.json` es el **ground truth** de la corrida. Sin él las trampas
serían folclore: las guías afirman números y los tests los validan contra este
archivo.

Contiene:

- semilla, escala, país, tasa de impuesto y periodos de cada lote;
- conteo de filas y archivos por dataset;
- suma total de `monto_total` (la que verifica el CA-7 desde Spark);
- **por cada trampa**: conteo exacto, tasa real y los **identificadores concretos** —
  los folios duplicados de T-2, los pares NC→factura de T-4, las filas corruptas de
  T-5 con su motivo, las cadenas de rectificatorias de T-3.

No lleva fecha de generación: una marca de tiempo rompería el determinismo del árbol.

---

## Determinismo

Misma semilla y misma escala ⇒ **bytes idénticos**. Está verificado en
`tests/test_determinismo.py`, que genera dos veces y compara el sha256 de cada
archivo, con un control negativo que exige que otra semilla produzca datos distintos.

Nada de azar sin sembrar: no se consulta el reloj en ningún punto de la generación.

---

## Tests

```bash
cd datagen && pytest tests/ -q
```

| Archivo | Verifica |
|---|---|
| `test_rut.py` | Módulo 11 sobre todos los contribuyentes y muestreo de DTEs |
| `test_determinismo.py` | Dos corridas, bytes idénticos, y el control negativo |
| `test_manifiesto.py` | Recuento independiente contra lo declarado; tipos decimal/date |
| `test_trampas.py` | Cada trampa T-1..T-7 localizada en los datos reales |
| `test_referencias.py` | Notas que apuntan a documentos existentes; correlativos consecutivos |
| `test_sin_rastros.py` | El repositorio no contiene firmas de herramientas de asistencia |

Los tests corren siempre en escala `dev`.

---

## Agregar un país

El generador no sabe nada de Chile: se lo pregunta al perfil (`datagen/perfiles/`).
Para agregar `peru` habría que escribir un perfil con RUC de 11 dígitos y su propio
dígito verificador, comprobantes SUNAT, IGV 18 %, PDT 621 y distritos peruanos.
Las siete trampas son independientes del país y se reutilizan tal cual.

El detalle de lo que exige un perfil está en `datagen/perfiles/base.py`. **El perfil
`peru` no está implementado** en esta entrega: solo la abstracción que lo permitiría.
