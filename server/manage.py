#!/usr/bin/env python3
"""Stub manage.py.

Placeholder requerido por devtools/hooks/main.py para que el orquestador
no falle al verificar la existencia de ``server/manage.py``.

Este portfolio NO usa Django. La capa server/ existe SOLO como compat
con la arquitectura del template fuente (mvp-template-full-stack). Si en
el futuro se agrega un backend, este archivo se reemplaza por el
manage.py real de Django.
"""
import sys

if __name__ == '__main__':
    print('portfolio: no hay backend Django. Este archivo es un stub.', file=sys.stderr)
    sys.exit(0)
