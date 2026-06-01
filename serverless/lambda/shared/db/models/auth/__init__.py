"""Subpaquete `auth/`: schema relacional del dominio auth (11 tablas).

Vaciado a proposito: sin re-exports (no-barrel). Los consumidores
importan del modulo concreto (`from shared.db.models.<dom>.<mod>
import <Clase>`). Lo enforza el conformance `serverless lint-deps`.
Ver `.claude/rules/lambda-shared-imports.md`.
"""
