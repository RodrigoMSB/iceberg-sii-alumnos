"""Permite ejecutar el generador como 'python -m datagen'."""

import sys

from .cli import main

if __name__ == "__main__":
    sys.exit(main())
