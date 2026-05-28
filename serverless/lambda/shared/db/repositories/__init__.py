"""Subpaquete `repositories/`: helpers de queries por dominio.

Cada dominio (auth, cv, ...) tiene su modulo aqui. Los services del
Lambda consumen estos helpers (NO importan `sqlalchemy` directo —
contrato `lambda-shared-imports`).
"""
