# Laboratorio 07. Mudarse sin cerrar el negocio

Cada celda lleva `%%sql` en la primera línea y una sola sentencia por celda.

## Paso 0. La tabla Hive de partida

**Celda 0.1**

**Se escribe**

```sql
USE mi_espacio
```

**En consola** `Listo. La sentencia se ejecutó.`

**Cambia en tu corrida** nada.

---

**Celda 0.2**

**Se escribe**

```sql
DROP TABLE IF EXISTS documentos_hive
```

**En consola** `Listo. La sentencia se ejecutó.`

**Cambia en tu corrida** nada.

---

**Celda 0.3**

**Se escribe**

```sql
DROP TABLE IF EXISTS documentos_hive_backup_
```

**En consola** `Listo. La sentencia se ejecutó.`

**Cambia en tu corrida** nada.

---

**Celda 0.4**

**Se escribe**

```sql
CREATE TABLE documentos_hive (
    rut_emisor     STRING,
    tipo_dte       INT,
    folio          BIGINT,
    fecha_emision  DATE,
    monto_neto     DECIMAL(18,2),
    monto_iva      DECIMAL(18,2),
    monto_total    DECIMAL(18,2),
    estado_sii     STRING
) STORED AS PARQUET
```

**En consola** `Listo. La sentencia se ejecutó.`

**Cambia en tu corrida** nada.

---

**Celda 0.5**

**Se escribe**

```sql
INSERT INTO documentos_hive
SELECT rut_emisor, tipo_dte, folio, fecha_emision,
       monto_neto, monto_iva, monto_total, estado_sii
FROM curso.dte_2024
```

**En consola** `Listo. La sentencia se ejecutó.`

**Cambia en tu corrida** nada.

---

**Celda 0.6**

**Se escribe**

```sql
DESCRIBE TABLE EXTENDED documentos_hive
```

**En consola**

```
| col_name                     | data_type                                                            | comment |
| rut_emisor                   | string                                                               | None    |
| tipo_dte                     | int                                                                  | None    |
| folio                        | bigint                                                               | None    |
| fecha_emision                | date                                                                 | None    |
| monto_neto                   | decimal(18,2)                                                        | None    |
| monto_iva                    | decimal(18,2)                                                        | None    |
| monto_total                  | decimal(18,2)                                                        | None    |
| estado_sii                   | string                                                               | None    |
|                              |                                                                      |         |
| # Detailed Table Information |                                                                      |         |
| Database                     | mi_espacio                                                           |         |
| Table                        | documentos_hive                                                      |         |
| Owner                        | root                                                                 |         |
| Created Time                 | Fri Sep 25 18:07:55 UTC 2026                                         |         |
| Last Access                  | UNKNOWN                                                              |         |
| Created By                   | Spark 3.3.4                                                          |         |
| Type                         | MANAGED                                                              |         |
| Provider                     | hive                                                                 |         |
| Table Properties             | [transient_lastDdlTime=1790359675]                                   |         |
| Location                     | hdfs://namenode:8020/warehouse/iceberg/mi_espacio.db/documentos_hive |         |
| Serde Library                | org.apache.hadoop.hive.ql.io.parquet.serde.ParquetHiveSerDe          |         |
| InputFormat                  | org.apache.hadoop.hive.ql.io.parquet.MapredParquetInputFormat        |         |
| OutputFormat                 | org.apache.hadoop.hive.ql.io.parquet.MapredParquetOutputFormat       |         |
| Storage Properties           | [serialization.format=1]                                             |         |
| Partition Provider           | Catalog                                                              |         |
25 filas.
```

**Cambia en tu corrida** la hora de creación y el número de la línea `transient_lastDdlTime`.

## Paso 1. Levantar el inventario

**Celda 1.1**

**Se escribe**

```sql
SELECT count(*)         AS documentos,
       sum(monto_total) AS total_general
FROM documentos_hive
```

**En consola**

```
| documentos | total_general   |
| 30000      | 291293351462.71 |
1 fila.
```

**Cambia en tu corrida** nada.

---

**Celda 1.2**

**Se escribe**

```sql
SELECT date_format(fecha_emision, 'yyyy-MM') AS periodo,
       count(*)                             AS documentos,
       sum(monto_total)                     AS total_del_periodo
FROM documentos_hive
GROUP BY date_format(fecha_emision, 'yyyy-MM')
ORDER BY periodo
```

**En consola**

```
| periodo | documentos | total_del_periodo |
| 2024-01 | 2500       | 23381729910.07    |
| 2024-02 | 2500       | 24831948613.59    |
| 2024-03 | 2500       | 26699931432.64    |
| 2024-04 | 2500       | 23722997990.55    |
| 2024-05 | 2500       | 24328007216.84    |
| 2024-06 | 2500       | 24547341762.59    |
| 2024-07 | 2500       | 23621609483.83    |
| 2024-08 | 2500       | 23648615665.89    |
| 2024-09 | 2500       | 24136964210.51    |
| 2024-10 | 2500       | 23106058024.78    |
| 2024-11 | 2500       | 24722608269.83    |
| 2024-12 | 2500       | 24545538881.59    |
12 filas.
```

**Cambia en tu corrida** nada.

## Paso 2. Mirar sus límites

**Celda 2.1**

**Se escribe**

```sql
SELECT snapshot_id, committed_at, operation
FROM mi_espacio.documentos_hive.snapshots
ORDER BY committed_at
```

**En consola** `Spark rechazó la sentencia: spark_catalog requires a single-part namespace, but got [mi_espacio, documentos_hive]`.

```
Spark rechazó la sentencia:

spark_catalog requires a single-part namespace, but got [mi_espacio, documentos_hive]
```

**Cambia en tu corrida** nada.

---

**Celda 2.2**

**Se escribe**

```sql
CALL spark_catalog.system.rollback_to_snapshot('mi_espacio.documentos_hive', 1)
```

**En consola** `Spark rechazó la sentencia: An error occurred while calling o38.sql. : org.apache.iceberg.exceptions.ValidationException: mi_espacio.documentos_hive is not org.apache.iceberg.spark.source.SparkTable at org.apache.iceberg.exceptions.ValidationException.check(ValidationException.java:49) at org.apache.iceberg.spark.procedures.BaseProcedure.loadSparkTable(BaseProcedure.java:141) at org.apache.iceberg.spark.procedures.BaseProcedure.execute(BaseProcedure.java:101) at org.apache.iceberg.spark.procedures.BaseProcedure.modifyIcebergTable(BaseProcedure.java:85) at org.apache.iceberg.spark.procedures.RollbackToSnapshotProcedure.call(RollbackToSnapshotProcedure.java:83) at org.apache.spark.sql.execution.datasources.v2.CallExec.run(CallExec.scala:34) at org.apache.spark.sql.execution.datasources.v2.V2CommandExec.result$lzycompute(V2CommandExec.scala:43) at org.apache.spark.sql.execution.datasources.v2.V2CommandExec.result(V2CommandExec.scala:43) at org.apache.spark.sql.execution.datasources.v2.V2CommandExec.executeCollect(V2CommandExec.scala:49) at org.apache.spark.sql.execution.QueryExecution$$anonfun$eagerlyExecuteCommands$1.$anonfun$applyOrElse$1(QueryExecution.scala:98) at org.apache.spark.sql.execution.SQLExecution$.$anonfun$withNewExecutionId$6(SQLExecution.scala:109) at org.apache.spark.sql.execution.SQLExecution$.withSQLConfPropagated(SQLExecution.scala:169) at org.apache.spark.sql.execution.SQLExecution$.$anonfun$withNewExecutionId$1(SQLExecution.scala:95) at org.apache.spark.sql.SparkSession.withActive(SparkSession.scala:779) at org.apache.spark.sql.execution.SQLExecution$.withNewExecutionId(SQLExecution.scala:64) at org.apache.spark.sql.execution.QueryExecution$$anonfun$eagerlyExecuteCommands$1.applyOrElse(QueryExecution.scala:98) at org.apache.spark.sql.execution.QueryExecution$$anonfun$eagerlyExecuteCommands$1.applyOrElse(QueryExecution.scala:94) at org.apache.spark.sql.catalyst.trees.TreeNode.$anonfun$transformDownWithPruning$1(TreeNode.scala:584) at org.apache.spark.sql.catalyst.trees.CurrentOrigin$.withOrigin(TreeNode.scala:176) at org.apache.spark.sql.catalyst.trees.TreeNode.transformDownWithPruning(TreeNode.scala:584) at org.apache.spark.sql.catalyst.plans.logical.LogicalPlan.org$apache$spark$sql$catalyst$plans$logical$AnalysisHelper$$super$transformDownWithPruning(LogicalPlan.scala:30) at org.apache.spark.sql.catalyst.plans.logical.AnalysisHelper.transformDownWithPruning(AnalysisHelper.scala:267) at org.apache.spark.sql.catalyst.plans.logical.AnalysisHelper.transformDownWithPruning$(AnalysisHelper.scala:263) at org.apache.spark.sql.catalyst.plans.logical.LogicalPlan.transformDownWithPruning(LogicalPlan.scala:30) at org.apache.spark.sql.catalyst.plans.logical.LogicalPlan.transformDownWithPruning(LogicalPlan.scala:30) at org.apache.spark.sql.catalyst.trees.TreeNode.transformDown(TreeNode.scala:560) at org.apache.spark.sql.execution.QueryExecution.eagerlyExecuteCommands(QueryExecution.scala:94) at org.apache.spark.sql.execution.QueryExecution.commandExecuted$lzycompute(QueryExecution.scala:81) at org.apache.spark.sql.execution.QueryExecution.commandExecuted(QueryExecution.scala:79) at org.apache.spark.sql.Dataset.<init>(Dataset.scala:219) at org.apache.spark.sql.Dataset$.$anonfun$ofRows$2(Dataset.scala:99) at org.apache.spark.sql.SparkSession.withActive(SparkSession.scala:779) at org.apache.spark.sql.Dataset$.ofRows(Dataset.scala:96) at org.apache.spark.sql.SparkSession.$anonfun$sql$1(SparkSession.scala:622) at org.apache.spark.sql.SparkSession.withActive(SparkSession.scala:779) at org.apache.spark.sql.SparkSession.sql(SparkSession.scala:617) at java.base/jdk.internal.reflect.NativeMethodAccessorImpl.invoke0(Native Method) at java.base/jdk.internal.reflect.NativeMethodAccessorImpl.invoke(NativeMethodAccessorImpl.java:62) at java.base/jdk.internal.reflect.DelegatingMethodAccessorImpl.invoke(DelegatingMethodAccessorImpl.java:43) at java.base/java.lang.reflect.Method.invoke(Method.java:566) at py4j.reflection.MethodInvoker.invoke(MethodInvoker.java:244) at py4j.reflection.ReflectionEngine.invoke(ReflectionEngine.java:357) at py4j.Gateway.invoke(Gateway.java:282) at py4j.commands.AbstractCommand.invokeMethod(AbstractCommand.java:132) at py4j.commands.CallCommand.execute(CallCommand.java:79) at py4j.ClientServerConnection.waitForCommands(ClientServerConnection.java:182) at py4j.ClientServerConnection.run(ClientServerConnection.java:106) at java.base/java.lang.Thread.run(Thread.java:829)`.

```
Spark rechazó la sentencia:

An error occurred while calling o39.sql.
: org.apache.iceberg.exceptions.ValidationException: mi_espacio.documentos_hive is not org.apache.iceberg.spark.source.SparkTable
	at org.apache.iceberg.exceptions.ValidationException.check(ValidationException.java:49)
	at org.apache.iceberg.spark.procedures.BaseProcedure.loadSparkTable(BaseProcedure.java:141)
	at org.apache.iceberg.spark.procedures.BaseProcedure.execute(BaseProcedure.java:101)
	at org.apache.iceberg.spark.procedures.BaseProcedure.modifyIcebergTable(BaseProcedure.java:85)
	at org.apache.iceberg.spark.procedures.RollbackToSnapshotProcedure.call(RollbackToSnapshotProcedure.java:83)
	at org.apache.spark.sql.execution.datasources.v2.CallExec.run(CallExec.scala:34)
	at org.apache.spark.sql.execution.datasources.v2.V2CommandExec.result$lzycompute(V2CommandExec.scala:43)
	at org.apache.spark.sql.execution.datasources.v2.V2CommandExec.result(V2CommandExec.scala:43)
	at org.apache.spark.sql.execution.datasources.v2.V2CommandExec.executeCollect(V2CommandExec.scala:49)
	at org.apache.spark.sql.execution.QueryExecution$$anonfun$eagerlyExecuteCommands$1.$anonfun$applyOrElse$1(QueryExecution.scala:98)
	at org.apache.spark.sql.execution.SQLExecution$.$anonfun$withNewExecutionId$6(SQLExecution.scala:109)
	at org.apache.spark.sql.execution.SQLExecution$.withSQLConfPropagated(SQLExecution.scala:169)
	at org.apache.spark.sql.execution.SQLExecution$.$anonfun$withNewExecutionId$1(SQLExecution.scala:95)
	at org.apache.spark.sql.SparkSession.withActive(SparkSession.scala:779)
	at org.apache.spark.sql.execution.SQLExecution$.withNewExecutionId(SQLExecution.scala:64)
	at org.apache.spark.sql.execution.QueryExecution$$anonfun$eagerlyExecuteCommands$1.applyOrElse(QueryExecution.scala:98)
	at org.apache.spark.sql.execution.QueryExecution$$anonfun$eagerlyExecuteCommands$1.applyOrElse(QueryExecution.scala:94)
	at org.apache.spark.sql.catalyst.trees.TreeNode.$anonfun$transformDownWithPruning$1(TreeNode.scala:584)
	at org.apache.spark.sql.catalyst.trees.CurrentOrigin$.withOrigin(TreeNode.scala:176)
	at org.apache.spark.sql.catalyst.trees.TreeNode.transformDownWithPruning(TreeNode.scala:584)
	at org.apache.spark.sql.catalyst.plans.logical.LogicalPlan.org$apache$spark$sql$catalyst$plans$logical$AnalysisHelper$$super$transformDownWithPruning(LogicalPlan.scala:30)
	at org.apache.spark.sql.catalyst.plans.logical.AnalysisHelper.transformDownWithPruning(AnalysisHelper.scala:267)
	at org.apache.spark.sql.catalyst.plans.logical.AnalysisHelper.transformDownWithPruning$(AnalysisHelper.scala:263)
	at org.apache.spark.sql.catalyst.plans.logical.LogicalPlan.transformDownWithPruning(LogicalPlan.scala:30)
	at org.apache.spark.sql.catalyst.plans.logical.LogicalPlan.transformDownWithPruning(LogicalPlan.scala:30)
	at org.apache.spark.sql.catalyst.trees.TreeNode.transformDown(TreeNode.scala:560)
	at org.apache.spark.sql.execution.QueryExecution.eagerlyExecuteCommands(QueryExecution.scala:94)
	at org.apache.spark.sql.execution.QueryExecution.commandExecuted$lzycompute(QueryExecution.scala:81)
	at org.apache.spark.sql.execution.QueryExecution.commandExecuted(QueryExecution.scala:79)
	at org.apache.spark.sql.Dataset.<init>(Dataset.scala:219)
	at org.apache.spark.sql.Dataset$.$anonfun$ofRows$2(Dataset.scala:99)
	at org.apache.spark.sql.SparkSession.withActive(SparkSession.scala:779)
	at org.apache.spark.sql.Dataset$.ofRows(Dataset.scala:96)
	at org.apache.spark.sql.SparkSession.$anonfun$sql$1(SparkSession.scala:622)
	at org.apache.spark.sql.SparkSession.withActive(SparkSession.scala:779)
	at org.apache.spark.sql.SparkSession.sql(SparkSession.scala:617)
	at java.base/jdk.internal.reflect.NativeMethodAccessorImpl.invoke0(Native Method)
	at java.base/jdk.internal.reflect.NativeMethodAccessorImpl.invoke(NativeMethodAccessorImpl.java:62)
	at java.base/jdk.internal.reflect.DelegatingMethodAccessorImpl.invoke(DelegatingMethodAccessorImpl.java:43)
	at java.base/java.lang.reflect.Method.invoke(Method.java:566)
	at py4j.reflection.MethodInvoker.invoke(MethodInvoker.java:244)
	at py4j.reflection.ReflectionEngine.invoke(ReflectionEngine.java:357)
	at py4j.Gateway.invoke(Gateway.java:282)
	at py4j.commands.AbstractCommand.invokeMethod(AbstractCommand.java:132)
	at py4j.commands.CallCommand.execute(CallCommand.java:79)
	at py4j.ClientServerConnection.waitForCommands(ClientServerConnection.java:182)
	at py4j.ClientServerConnection.run(ClientServerConnection.java:106)
	at java.base/java.lang.Thread.run(Thread.java:829)
```

**Cambia en tu corrida** nada.

## Paso 3. Migrar

**Celda 3.1**

**Se escribe**

```sql
CALL spark_catalog.system.migrate('mi_espacio.documentos_hive')
```

**En consola**

```
| migrated_files_count |
| 1                    |
1 fila.
```

**Cambia en tu corrida** nada.

---

**Celda 3.2**

**Se escribe**

```sql
DESCRIBE TABLE EXTENDED documentos_hive
```

**En consola**

```
| col_name                     | data_type                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          | comment |
| rut_emisor                   | string                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                             |         |
| tipo_dte                     | int                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                |         |
| folio                        | bigint                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                             |         |
| fecha_emision                | date                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                               |         |
| monto_neto                   | decimal(18,2)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      |         |
| monto_iva                    | decimal(18,2)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      |         |
| monto_total                  | decimal(18,2)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      |         |
| estado_sii                   | string                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                             |         |
|                              |                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    |         |
| # Partitioning               |                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    |         |
| Not partitioned              |                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    |         |
|                              |                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    |         |
| # Metadata Columns           |                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    |         |
| _spec_id                     | int                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                |         |
| _partition                   | struct<>                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                           |         |
| _file                        | string                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                             |         |
| _pos                         | bigint                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                             |         |
| _deleted                     | boolean                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            |         |
|                              |                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    |         |
| # Detailed Table Information |                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    |         |
| Name                         | spark_catalog.mi_espacio.documentos_hive                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                           |         |
| Location                     | hdfs://namenode:8020/warehouse/iceberg/mi_espacio.db/documentos_hive                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                               |         |
| Provider                     | iceberg                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            |         |
| Table Properties             | [current-snapshot-id=7041860744555628170,format=iceberg/parquet,format-version=1,migrated=true,schema.name-mapping.default=[ {\n  "field-id" : 1,\n  "names" : [ "rut_emisor" ]\n}, {\n  "field-id" : 2,\n  "names" : [ "tipo_dte" ]\n}, {\n  "field-id" : 3,\n  "names" : [ "folio" ]\n}, {\n  "field-id" : 4,\n  "names" : [ "fecha_emision" ]\n}, {\n  "field-id" : 5,\n  "names" : [ "monto_neto" ]\n}, {\n  "field-id" : 6,\n  "names" : [ "monto_iva" ]\n}, {\n  "field-id" : 7,\n  "names" : [ "monto_total" ]\n}, {\n  "field-id" : 8,\n  "names" : [ "estado_sii" ]\n} ]] |         |
24 filas.
```

**Cambia en tu corrida** nada.

## Paso 4. Verificar

**Celda 4.1**

**Se escribe**

```sql
SELECT count(*)         AS documentos,
       sum(monto_total) AS total_general
FROM documentos_hive
```

**En consola**

```
| documentos | total_general   |
| 30000      | 291293351462.71 |
1 fila.
```

**Cambia en tu corrida** nada.

---

**Celda 4.2**

**Se escribe**

```sql
SELECT date_format(fecha_emision, 'yyyy-MM') AS periodo,
       count(*)                             AS documentos,
       sum(monto_total)                     AS total_del_periodo
FROM documentos_hive
GROUP BY date_format(fecha_emision, 'yyyy-MM')
ORDER BY periodo
```

**En consola**

```
| periodo | documentos | total_del_periodo |
| 2024-01 | 2500       | 23381729910.07    |
| 2024-02 | 2500       | 24831948613.59    |
| 2024-03 | 2500       | 26699931432.64    |
| 2024-04 | 2500       | 23722997990.55    |
| 2024-05 | 2500       | 24328007216.84    |
| 2024-06 | 2500       | 24547341762.59    |
| 2024-07 | 2500       | 23621609483.83    |
| 2024-08 | 2500       | 23648615665.89    |
| 2024-09 | 2500       | 24136964210.51    |
| 2024-10 | 2500       | 23106058024.78    |
| 2024-11 | 2500       | 24722608269.83    |
| 2024-12 | 2500       | 24545538881.59    |
12 filas.
```

**Cambia en tu corrida** nada.

## Paso 5. Comprobar que ahora sí es Iceberg

**Celda 5.1**

**Se escribe**

```sql
SELECT snapshot_id, committed_at, operation
FROM mi_espacio.documentos_hive.snapshots
ORDER BY committed_at
```

**En consola**

```
| snapshot_id         | committed_at            | operation |
| 7041860744555628170 | 2026-09-25 18:08:02.285 | append    |
1 fila.
```

**Cambia en tu corrida** el identificador y la hora, siempre.

---

**Celda 5.2**

**Se escribe**

```sql
SELECT count(*)          AS archivos,
       sum(record_count) AS documentos
FROM mi_espacio.documentos_hive.files
```

**En consola**

```
| archivos | documentos |
| 1        | 30000      |
1 fila.
```

**Cambia en tu corrida** nada.

---

**Celda 5.3**

**Se escribe**

```sql
SHOW TABLES IN mi_espacio
```

**En consola**

```
| namespace  | tableName                | isTemporary |
| mi_espacio | contribuyentes_lab00     | False       |
| mi_espacio | contribuyentes_lab01     | False       |
| mi_espacio | contribuyentes_lab02     | False       |
| mi_espacio | documentos_hive          | False       |
| mi_espacio | documentos_hive_backup_  | False       |
| mi_espacio | documentos_lab03         | False       |
| mi_espacio | documentos_lab05         | False       |
| mi_espacio | documentos_por_mes       | False       |
| mi_espacio | documentos_sin_particion | False       |
| mi_espacio | recepcion_lab06          | False       |
10 filas.
```

## Paso 6. La capa de consulta

**Se escribe** (en Hue).

```sql-hue
SELECT date_format(fecha_emision, 'yyyy-MM') AS periodo,
       count(*)                              AS documentos,
       sum(monto_total)                      AS total_del_periodo
FROM mi_espacio.documentos_hive
GROUP BY date_format(fecha_emision, 'yyyy-MM')
ORDER BY periodo
```

**En consola** doce filas, **exactamente las mismas del paso 4**.

```
| periodo | documentos | total_del_periodo |
| 2024-01 | 2500       | 23381729910.07    |
| 2024-02 | 2500       | 24831948613.59    |
| 2024-03 | 2500       | 26699931432.64    |
| 2024-04 | 2500       | 23722997990.55    |
| 2024-05 | 2500       | 24328007216.84    |
| 2024-06 | 2500       | 24547341762.59    |
| 2024-07 | 2500       | 23621609483.83    |
| 2024-08 | 2500       | 23648615665.89    |
| 2024-09 | 2500       | 24136964210.51    |
| 2024-10 | 2500       | 23106058024.78    |
| 2024-11 | 2500       | 24722608269.83    |
| 2024-12 | 2500       | 24545538881.59    |
(12 filas)
```

**Cambia en tu corrida** nada.

---

**Se escribe** (en Hue).

```sql-hue
SELECT tipo_dte,
       count(*)         AS documentos,
       sum(monto_total) AS total
FROM mi_espacio.documentos_hive
GROUP BY tipo_dte
ORDER BY tipo_dte
```

**En consola**

```
| tipo_dte | documentos | total             |
| 33       | 12664      | 241123556352.49   |
| 34       | 2138       | 32447276599.00    |
| 39       | 11365      | 817555482.66      |
| 52       | 1766       | 30041653364.00    |
| 56       | 597        | 8524913042.87     |
| 61       | 1470       | -21661603378.31   |
(6 filas)
```

**Cambia en tu corrida** nada.