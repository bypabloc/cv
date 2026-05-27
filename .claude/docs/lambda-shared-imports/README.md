# Lambda shared-only imports

> Documentacion conceptual del contrato shared-only del backend serverless
> del portfolio. Para la regla autoritativa ver
> `.claude/rules/lambda-shared-imports.md`; para la guia rapida invocable
> ver la skill `lambda-shared-imports`.

## Premisa

Los archivos `serverless/lambda/services/<X>/core/**/*.py` NO importan
directamente paquetes externos. Toda dependencia externa (pydantic,
sqlalchemy, alembic, psycopg, boto3, aws-lambda-powertools) viaja por
`serverless/lambda/shared/**`. Cada subpaquete shared es el portador
unico de su paquete y lo re-exporta.

Beneficios:

- **Cero duplicacion**: pydantic / boto3 / SQLAlchemy se declaran UNA
  sola vez (en el shared portador). Los services no los declaran.
- **API estable hacia los services**: cuando una version mayor del
  paquete externo cambia un nombre, se actualiza el re-export del
  shared. Los services no se tocan.
- **Singleton predecible**: shared.aws.ses tiene UN cliente boto3;
  shared.aws.dynamodb tiene UN resource. Los services consumen el
  mismo.
- **Testing centralizado**: mocks del paquete externo viven en
  `shared/tests/` (cuando aplica). El service mockea el portador.
- **Enforcement automatico**: `serverless lint-deps` corre dos checks
  (dedup D-3 + imports prohibidos) — la regresion se detecta en CI.

## Cuando aplicarlo

- Crear un Lambda nuevo siguiendo `lambda-controller`.
- Refactorizar un Lambda existente.
- Agregar un paquete externo nuevo al backend.
- Agregar una nueva action / model / service a un Lambda.

## Tabla de contenidos

| Documento | Cuando leer |
|-----------|-------------|
| [01-portadores-shared.md](01-portadores-shared.md) | Catalogo completo de subpaquetes shared y que paquetes externos absorben |
| [02-migracion-y-extension.md](02-migracion-y-extension.md) | Procedimiento para migrar un service existente o agregar paquete nuevo |

## Reglas criticas

- **SIEMPRE** importar desde `shared.<portador>` en `core/`.
- **SIEMPRE** agregar el simbolo a `__all__` del shared cuando se
  re-exporta.
- **SIEMPRE** test unit del re-export en
  `shared/tests/unit/shared/<X>/test_<paquete>_reexport.py`.
- **NUNCA** `from pydantic`, `from sqlalchemy`, `import boto3`, `from
  aws_lambda_powertools` en `core/**/*.py`.
- **NUNCA** declarar en el `pyproject.toml` del service un paquete
  que el cierre transitivo de shared ya aporta.

## Navegacion

- Regla autoritativa: `.claude/rules/lambda-shared-imports.md`
- Skill: `.claude/skills/lambda-shared-imports/SKILL.md`
- Implementacion del check: `devtools/serverless/import_validator.py`
- Implementacion del dedup: `devtools/serverless/dep_validator.py`
- Formato general de Lambdas: `.claude/rules/lambda-controller.md`
