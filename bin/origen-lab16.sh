#!/usr/bin/env bash
#
# Deja en pie el origen relacional del laboratorio 16.
#
#   bin/41-cargar-origen-lab16.sh           # crea o repone el origen
#   bin/41-cargar-origen-lab16.sh --estado  # solo mira, no toca nada
#
# El laboratorio 16 simula una migracion desde una base relacional. El "origen"
# es una base PostgreSQL que vive en el mismo contenedor que el Metastore,
# iceberg-postgres, en una database aparte llamada 'origen'. Ni el Metastore ni Hue
# se tocan.
#
# POR QUE ESTO ES UN SCRIPT Y NO ESTA EN EL COMPOSE
#
# pg_hba.conf y las databases viven dentro del volumen pgdata, no en el
# repositorio. Si el volumen se rehace, se va con el todo esto, igual que se va
# el warehouse y hay que volver a correr 40-cargar-datos-curso.py. Este script
# es a este origen lo que aquel es a la database 'curso': la forma versionada de
# reponerlo. Es idempotente, se puede correr las veces que haga falta.
#
# POR QUE EL USUARIO 'lector' NO LLEVA CLAVE
#
# El alumno abre el origen con una vista JDBC escrita en una celda de su
# cuaderno, y esa celda termina en PASOS.md y en el repositorio. Una clave ahi
# es una credencial versionada. En vez de eso, PostgreSQL confia en 'lector'
# cuando viene de la red del laboratorio y SOLO para la database 'origen'; la
# celda lleva password ''. La regla va ANTES de la general, porque pg_hba se lee
# de arriba hacia abajo y la primera que calza manda.
#
# 'lector' es de solo lectura sobre una sola tabla de datos sinteticos, y la red
# del laboratorio no esta expuesta fuera del servidor.

source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/_comun.sh"

CONTENEDOR="iceberg-postgres"
SUPERUSUARIO="hive"
BASE="origen"
MARCA="# lab 16: lector confia desde la red del laboratorio, sin clave"

exigir_docker
contenedor_vivo "${CONTENEDOR}" || morir \
  "el contenedor ${CONTENEDOR} no esta corriendo." \
  "cd bin/ambiente.sh arriba"

psql_super() { docker exec -i "${CONTENEDOR}" psql -U "${SUPERUSUARIO}" "$@"; }

estado() {
  titulo "Origen del laboratorio 16"
  if ! psql_super -d postgres -tAc "SELECT 1 FROM pg_database WHERE datname = '${BASE}'" | grep -q 1; then
    aviso "la database '${BASE}' no existe"
    return 1
  fi
  local filas marca
  filas="$(psql_super -d "${BASE}" -tAc "SELECT count(*) FROM contribuyentes" 2>/dev/null || echo "?")"
  marca="$(psql_super -d "${BASE}" -tAc "SELECT max(actualizado_en) FROM contribuyentes" 2>/dev/null || echo "?")"
  ok "database '${BASE}' con ${filas} contribuyentes"
  info "marca de agua: ${marca}"
  if docker exec "${CONTENEDOR}" grep -q "${MARCA}" /var/lib/postgresql/data/pg_hba.conf 2>/dev/null; then
    ok "pg_hba confia en 'lector' desde la red del laboratorio"
  else
    aviso "pg_hba NO tiene la regla de 'lector'"
    return 1
  fi
}

if [ "${1:-}" = "--estado" ]; then
  estado
  exit $?
fi

titulo "Reponiendo el origen del laboratorio 16"

# --- La database y la tabla --------------------------------------------------
psql_super -d postgres -tAc "SELECT 1 FROM pg_database WHERE datname = '${BASE}'" | grep -q 1 \
  || { psql_super -d postgres -c "CREATE DATABASE ${BASE}" >/dev/null; ok "database '${BASE}' creada"; }

psql_super -d "${BASE}" -v ON_ERROR_STOP=1 >/dev/null <<'SQL'
CREATE TABLE IF NOT EXISTS contribuyentes (
    rut             TEXT PRIMARY KEY,
    razon_social    TEXT NOT NULL,
    segmento        TEXT NOT NULL,
    actualizado_en  TIMESTAMP NOT NULL
);

-- Veinte contribuyentes. Los RUT son emisores reales del universo del curso,
-- sacados de curso.dte_2024, asi que cumplen el modulo 11 y las razones
-- sociales son las mismas que el alumno ya vio en otros laboratorios.
TRUNCATE contribuyentes;
INSERT INTO contribuyentes (rut, razon_social, segmento, actualizado_en) VALUES
 ('76000262-3','Boldo Importadora EIRL',    'MICRO',  '2026-09-01 08:00:00'),
 ('76000503-7','Calafate Ferreteria EIRL',  'PEQUENA','2026-09-01 08:05:00'),
 ('76002248-9','Andes Consultores SpA',     'MEDIANA','2026-09-01 08:10:00'),
 ('76002652-2','Calafate Constructora S.A.','GRANDE', '2026-09-01 08:15:00'),
 ('76002830-4','Huemul Alimentos Ltda.',    'MICRO',  '2026-09-01 08:20:00'),
 ('76004358-3','Ulmo Constructora Ltda.',   'PEQUENA','2026-09-01 08:25:00'),
 ('76005022-9','Andes Distribuidora EIRL',  'MEDIANA','2026-09-01 08:30:00'),
 ('76005135-7','Huemul Servicios SpA',      'GRANDE', '2026-09-01 08:35:00'),
 ('76005575-1','Copihue Consultores EIRL',  'MICRO',  '2026-09-01 08:40:00'),
 ('76005701-0','Maiten Constructora Ltda.', 'PEQUENA','2026-09-01 08:45:00'),
 ('76006049-6','Canelo Constructora S.A.',  'MEDIANA','2026-09-01 08:50:00'),
 ('76007969-3','Maiten Alimentos EIRL',     'GRANDE', '2026-09-01 08:55:00'),
 ('76008296-1','Quillay Maquinarias Ltda.', 'MICRO',  '2026-09-01 09:00:00'),
 ('76008516-2','Boldo Logistica SpA',       'PEQUENA','2026-09-01 09:05:00'),
 ('76010063-3','Calafate Ferreteria EIRL',  'MEDIANA','2026-09-01 09:10:00'),
 ('76010099-4','Rauli Transportes EIRL',    'GRANDE', '2026-09-01 09:15:00'),
 ('76011940-7','Canelo Servicios EIRL',     'MICRO',  '2026-09-01 09:20:00'),
 ('76014257-3','Maiten Automotriz SpA',     'PEQUENA','2026-09-01 09:25:00'),
 ('76015893-3','Lenga Consultores Ltda.',   'MEDIANA','2026-09-01 09:30:00'),
 ('76016523-9','Andes Maquinarias EIRL',    'GRANDE', '2026-09-01 09:35:00');
SQL
ok "veinte contribuyentes cargados"

# --- El usuario de solo lectura, sin clave -----------------------------------
psql_super -d "${BASE}" -v ON_ERROR_STOP=1 >/dev/null <<'SQL'
DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'lector') THEN
    CREATE ROLE lector LOGIN;
  END IF;
END
$$;
SQL
psql_super -d "${BASE}" -v ON_ERROR_STOP=1 >/dev/null <<SQL
GRANT CONNECT ON DATABASE ${BASE} TO lector;
GRANT USAGE ON SCHEMA public TO lector;
GRANT SELECT ON contribuyentes TO lector;
REVOKE INSERT, UPDATE, DELETE, TRUNCATE ON contribuyentes FROM lector;
SQL
ok "usuario 'lector' con SELECT y nada mas"

# --- La regla de pg_hba, antes que la general --------------------------------
if docker exec "${CONTENEDOR}" grep -q "${MARCA}" /var/lib/postgresql/data/pg_hba.conf; then
  info "pg_hba ya tenia la regla"
else
  docker exec -i "${CONTENEDOR}" sh -s <<SHELL
set -e
HBA=/var/lib/postgresql/data/pg_hba.conf
cp "\$HBA" "\$HBA.antes-lab16"
{
  echo "${MARCA}"
  echo "host    ${BASE}    lector    all    trust"
  cat "\$HBA"
} > "\$HBA.nuevo"
mv "\$HBA.nuevo" "\$HBA"
chown postgres:postgres "\$HBA"; chmod 600 "\$HBA"
SHELL
  ok "regla agregada, con respaldo en pg_hba.conf.antes-lab16"
fi

# Recarga por SIGHUP: no corta las conexiones vivas del Metastore ni de Hue.
psql_super -d postgres -tAc "SELECT pg_reload_conf()" >/dev/null
ok "configuracion recargada, sin reiniciar PostgreSQL"

echo
estado
