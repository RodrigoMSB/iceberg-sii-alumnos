#!/usr/bin/env bash
#
# Mueve el origen del laboratorio 16, como lo haria el sistema de la DGT.
#
#   bin/mover-origen-lab16.sh          # tres cambios y dos altas
#   bin/mover-origen-lab16.sh --reset  # deja el origen como estaba
#   bin/mover-origen-lab16.sh --estado # solo mira
#
# Lo corres TU, a mitad del laboratorio, en el paso 3, entre la carga inicial y
# la deteccion de cambios. El cuaderno no toca el origen: su usuario 'lector'
# solo tiene SELECT. Ese es justamente el punto del paso 3, que el origen se
# mueve por su cuenta mientras la carga inicial ya esta hecha.
#
# QUE CAMBIA, Y POR QUE ASI
#
# Tres contribuyentes cambian de segmento y dos son nuevos. Los cinco quedan con
# una 'actualizado_en' posterior a la marca de agua de la carga inicial, que es
# lo unico que el alumno tiene para descubrirlos. Es la forma mas comun de
# deteccion de cambios en una migracion real y la que el laboratorio ensena.
#
# La fecha es fija, 2026-09-15 12:00:00, y no 'now()'. Si fuera la hora de la
# corrida, la salida del paso 4 seria distinta en cada dictado y la guia no
# podria declarar lo que el alumno va a ver.

source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/_comun.sh"

CONTENEDOR="iceberg-postgres"
BASE="origen"
CUANDO="2026-09-15 12:00:00"

exigir_docker
contenedor_vivo "${CONTENEDOR}" || morir \
  "el contenedor ${CONTENEDOR} no esta corriendo." \
  "cd bin/ambiente.sh arriba"

psql_origen() { docker exec -i "${CONTENEDOR}" psql -U hive -d "${BASE}" "$@"; }

estado() {
  titulo "Origen del laboratorio 16"
  local filas marca nuevos
  filas="$(psql_origen -tAc 'SELECT count(*) FROM contribuyentes')"
  marca="$(psql_origen -tAc 'SELECT max(actualizado_en) FROM contribuyentes')"
  nuevos="$(psql_origen -tAc "SELECT count(*) FROM contribuyentes WHERE actualizado_en > TIMESTAMP '2026-09-01 09:35:00'")"
  info "contribuyentes: ${filas}"
  info "marca de agua:  ${marca}"
  if [ "${nuevos}" = "0" ]; then
    ok "sin cambios posteriores a la carga inicial"
  else
    aviso "${nuevos} filas cambiadas o nuevas despues de la carga inicial"
  fi
}

case "${1:-}" in
  --estado)
    estado
    exit 0
    ;;

  --reset)
    titulo "Dejando el origen como estaba"
    psql_origen -v ON_ERROR_STOP=1 >/dev/null <<SQL
DELETE FROM contribuyentes WHERE rut IN ('77129445-1', '78440174-7');
UPDATE contribuyentes SET segmento = 'MICRO',   actualizado_en = TIMESTAMP '2026-09-01 08:00:00' WHERE rut = '76000262-3';
UPDATE contribuyentes SET segmento = 'MEDIANA', actualizado_en = TIMESTAMP '2026-09-01 08:10:00' WHERE rut = '76002248-9';
UPDATE contribuyentes SET segmento = 'GRANDE',  actualizado_en = TIMESTAMP '2026-09-01 08:35:00' WHERE rut = '76005135-7';
SQL
    ok "revertido"
    echo
    estado
    exit 0
    ;;

  "")
    ;;

  *)
    morir "no conozco la opcion '${1}'." "Uso: $0 [--reset|--estado]"
    ;;
esac

titulo "Moviendo el origen, como lo haria el sistema de la DGT"

psql_origen -v ON_ERROR_STOP=1 >/dev/null <<SQL
-- Tres que cambian de segmento. Crecieron, o los reclasificaron.
UPDATE contribuyentes SET segmento = 'PEQUENA', actualizado_en = TIMESTAMP '${CUANDO}' WHERE rut = '76000262-3';
UPDATE contribuyentes SET segmento = 'GRANDE',  actualizado_en = TIMESTAMP '${CUANDO}' WHERE rut = '76002248-9';
UPDATE contribuyentes SET segmento = 'MEDIANA', actualizado_en = TIMESTAMP '${CUANDO}' WHERE rut = '76005135-7';

-- Dos altas. Contribuyentes que no existian cuando se hizo la carga inicial.
INSERT INTO contribuyentes (rut, razon_social, segmento, actualizado_en) VALUES
 ('77129445-1', 'Lenga Transportes SpA',  'MICRO',   TIMESTAMP '${CUANDO}'),
 ('78440174-7', 'Copihue Alimentos EIRL', 'PEQUENA', TIMESTAMP '${CUANDO}')
ON CONFLICT (rut) DO UPDATE
   SET razon_social   = EXCLUDED.razon_social,
       segmento       = EXCLUDED.segmento,
       actualizado_en = EXCLUDED.actualizado_en;
SQL

ok "tres contribuyentes modificados y dos nuevos"
echo
estado
echo
info "ahora el alumno puede correr el paso 4"
