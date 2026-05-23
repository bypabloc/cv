# Fase A — shared.core re-exporta pydantic

> shared.core es el portador unico de pydantic para todo el backend. Re-exporta
> `BaseModel`, `Field`, `EmailStr`, `field_validator`, `model_validator` y
> `ConfigDict`. Absorbe `pydantic[email]` (antes en contact_form).

## Contexto / Problema

- `serverless/lambda/shared/core/__init__.py` exporta `Settings`,
  `ApplicationError`, etc., pero NO re-exporta nada de pydantic.
- 5 services importan `from pydantic import ...` en `core/models/*.py`.
- `pydantic[email]` se declara solo en `contact_form/pyproject.toml`
  (EXCEPTION D-3 actual). Mover a shared.core implica que TODAS las Lambdas
  cargan `email-validator` (~150 KB), trade-off aceptado.

## Solucion

1. Editar `shared/core/pyproject.toml`:
   - Cambiar `pydantic>=2.5,<3.0` por `pydantic[email]>=2.5,<3.0` en
     `[project.dependencies]`.
2. Editar `shared/core/__init__.py`:
   - Agregar `from pydantic import BaseModel, ConfigDict, Field,
     EmailStr, field_validator, model_validator`.
   - Extender `__all__` con esos simbolos.
3. NO modificar nada en `services/` en esta fase (la migracion va en Fase E).

## Archivos afectados

### Modificar

- `serverless/lambda/shared/core/pyproject.toml` — cambia `pydantic` por `pydantic[email]`.
  - Verificar: `python devtools/run.py serverless lint-deps` pasa.
- `serverless/lambda/shared/core/__init__.py` — agrega re-exports.
  - Verificar: `python -c "from shared.core import BaseModel, Field, EmailStr, field_validator"` desde `serverless/lambda/`.

## Criterios de aceptacion

- **AC-A1**: Given la fase A aplicada, When importo `from shared.core import
  BaseModel, Field, EmailStr, field_validator, model_validator, ConfigDict`,
  Then la importacion exitosa.
- **AC-A2**: Given el `pyproject.toml` de shared.core, When inspecciono
  `[project.dependencies]`, Then aparece `pydantic[email]>=2.5,<3.0` (no
  `pydantic` pelado).
- **AC-A3**: Given los 5 lambdas, When ejecuto `serverless lint-deps`, Then
  exit 0 (no hay duplicacion: pydantic vive solo en shared.core).

## Verificacion

```bash
# Sintaxis
python -m compileall -q serverless/lambda/shared/core

# Dedup pasa (lambdas no declaran pydantic ni pydantic[email] directo)
python devtools/run.py serverless lint-deps

# Unit tests de shared
python devtools/run.py serverless tests --type=unit --shared
```

## Commit

```text
feat(shared/core): re-exporta pydantic con extra email-validator

- shared/core/pyproject.toml: cambia pydantic por pydantic[email]>=2.5,<3.0
- shared/core/__init__.py: re-exporta BaseModel, ConfigDict, Field,
  EmailStr, field_validator, model_validator
- Cubre el rol de portador unico de pydantic para el backend serverless
- contact_form retira pydantic[email] de su pyproject.toml en Fase E
```
