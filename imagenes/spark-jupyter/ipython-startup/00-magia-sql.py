"""
Arranque de IPython: deja lista la magia %%sql en cada kernel.

Se limita a importar el modulo, que es quien registra la magia. Los archivos de
esta carpeta se EJECUTAN en el espacio de variables del alumno, no se importan;
por eso aca no se define nada; si no, el alumno veria en %whos los nombres
internos de la implementacion.
"""

import sys as _sys

if "/opt/lab/python" not in _sys.path:
    _sys.path.insert(0, "/opt/lab/python")

try:
    import magia_sql as _magia_sql  # registra %%sql al importarse
except Exception as _error:  # noqa: BLE001 - un fallo aca no puede matar el kernel
    print(f"AVISO: no se pudo cargar la magia %%sql ({_error}).")
    print("       Las celdas de Python siguen funcionando con spark.sql(...).")

del _sys
for _nombre in ("_magia_sql", "_error", "_nombre"):
    globals().pop(_nombre, None)
