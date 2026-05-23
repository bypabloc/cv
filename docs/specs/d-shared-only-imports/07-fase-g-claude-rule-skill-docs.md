# Fase G — Rule + skill + docs en .claude/

> Materializa lo aprendido en este plan como artefactos permanentes en
> `.claude/`: una rule de proyecto, una skill invocable y documentacion
> conceptual. Asi el estandar "todo via shared" se aplica a Lambdas nuevos
> y a refactors de los existentes, sin tener que releer este plan (que se
> elimina al mergear).

## Contexto / Problema

El plan completo se elimina al mergear (es efimero, ver
`.claude/rules/plan-format.md`). Si no extraemos las decisiones a un
artefacto permanente:

1. La proxima vez que se cree un Lambda, alguien volvera a importar
   `from pydantic` directo "porque funcionaba antes" — sin que CI alerte.
2. Un dev nuevo no sabra que `shared.core` re-exporta pydantic.
3. La regla "cero `import boto3` en `core/`" sobrevive solo via
   `lint-deps`, pero la *intencion* y el catalogo de portadores estan en
   `docs/specs/` (que ya no existe).

La rule existente `.claude/rules/lambda-controller.md` documenta el patron
`operation+action` + controller/service + manifest, pero NO menciona el
contrato shared-only.

## Solucion

Tres artefactos en un solo commit:

### G.1 — Rule nueva: `.claude/rules/lambda-shared-imports.md`

Rule de proyecto, autoritativa, citada desde `lambda-controller.md`.
Estructura corta (<250 lineas) con:

- Activacion (cuando aplica).
- Reglas duras SIEMPRE/NUNCA.
- Catalogo de portadores (tabla paquete -> shared portador -> ejemplo).
- Patron correcto (cheatsheet de imports).
- Patron incorrecto + correccion (antes/despues).
- Como agregar un nuevo paquete al backend (procedimiento).
- Como agregar un nuevo re-export al shared.
- Verificacion (`serverless lint-deps`).
- Anti-patrones (tabla).
- Referencias cruzadas.

Contenido nuclear:

```markdown
# Lambda shared-only imports

> Los services del backend serverless del portfolio (`serverless/lambda/services/*`)
> NO importan directamente paquetes externos. Toda dependencia externa
> (pydantic, sqlalchemy, alembic, psycopg, boto3, aws-lambda-powertools)
> viaja por `serverless/lambda/shared/**`. Cada subpaquete shared es el
> portador unico de su paquete.

## Activacion

Aplica SIEMPRE al editar, crear o refactorizar:
- Cualquier archivo `serverless/lambda/services/<X>/core/**/*.py`
- Cualquier `serverless/lambda/services/<X>/pyproject.toml`
- Los `__init__.py` de los subpaquetes `serverless/lambda/shared/<X>/`

## Reglas duras (SIEMPRE / NUNCA)

- **SIEMPRE** los services importan paquetes externos como
  `from shared.<subpaquete> import <simbolo>`.
- **SIEMPRE** los services declaran en `pyproject.toml` solo lo que NO
  aporta el cierre transitivo de shared (caso extremadamente raro).
- **SIEMPRE** que aparezca un import nuevo prohibido en `core/`, ese
  paquete se re-exporta primero desde el shared portador.
- **NUNCA** un archivo `core/**/*.py` contiene `from pydantic`,
  `from sqlalchemy`, `import boto3`, `from boto3`, `from alembic`,
  `import psycopg`, `from psycopg`, `from aws_lambda_powertools`,
  `import aws_lambda_powertools`, `import pydantic` o `from pydantic_settings`.
- **NUNCA** un service declara en su `pyproject.toml` deps que el cierre
  de shared ya aporta (regla D-3, validada por `serverless lint-deps`).
- **NUNCA** se duplica un cliente boto3 en `core/`: existe el wrapper en
  `shared.aws.<recurso>` o se agrega.

## Catalogo de portadores

| Paquete externo | Portador shared | Como se importa en services |
|-----------------|-----------------|------------------------------|
| `pydantic` (incluye extra `[email]`) | `shared.core` | `from shared.core import BaseModel, Field, EmailStr, field_validator, model_validator, ConfigDict` |
| `pydantic_settings` | `shared.core` (declarado, sin re-export hoy) | acceder via `shared.core.<algo>` o agregar re-export |
| `sqlalchemy` | `shared.db` | `from shared.db import select, func, pg_insert, Session, Base, db_session, get_engine` |
| `sqlalchemy.dialects.postgresql.insert` | `shared.db` | `from shared.db import pg_insert` (alias) |
| `alembic` | `shared.db` (uso interno; los services no la consumen — la Lambda db lo hace via `shared.db.run_migrate`) | n/a en services |
| `psycopg` | `shared.db` (uso interno via SQLAlchemy engine) | n/a en services |
| `boto3` (cliente generico) | `shared.aws` | no exponemos `boto3` crudo — usar el wrapper especifico |
| `boto3.dynamodb.types.TypeDeserializer/TypeSerializer` | `shared.aws` | `from shared.aws import TypeDeserializer, TypeSerializer` |
| SES (boto3.client('sesv2')) | `shared.aws.ses` | `from shared.aws import send_email` |
| DynamoDB Resource | `shared.aws.dynamodb` | `from shared.aws import get_resource, get_table` |
| SSM Parameter Store | `shared.aws.ssm` | `from shared.aws import get_parameter, get_secret` |
| `aws_lambda_powertools` | `shared.aws`, `shared.observability` | `from shared.observability import logger, metrics, tracer, MetricUnit` |
| HTTP responses + CORS + Turnstile | `shared.http` | `from shared.http import error_response, json_response, no_content_response, resolve_origin, verify_turnstile_token` |

## Patron correcto

```python
# services/contact_form/core/services/contact_service.py
from shared.aws import send_email
from shared.core import ApplicationError, settings
from shared.observability import MetricUnit, logger, metrics


def send_owner_email(payload: ContactPayload) -> str:
    response = send_email(
        from_address=settings.ses_from_address,
        to_addresses=payload.recipients,
        subject=payload.subject,
        text_body=payload.text,
        html_body=payload.html,
    )
    metrics.add_metric(
        name='ContactEmailSent', unit=MetricUnit.Count, value=1,
    )
    return response['MessageId']
```

## Patron incorrecto + correccion

```python
# MAL — services/contact_form/core/services/contact_service.py
import boto3
from aws_lambda_powertools.metrics import MetricUnit
from pydantic import BaseModel

# BIEN
from shared.aws import send_email
from shared.core import BaseModel
from shared.observability import MetricUnit
```

## Como agregar un paquete externo nuevo al backend

1. Decidir el shared portador (aws, core, db, http, observability,
   dynamodb, cache, rate_limit). Si no encaja en ninguno, crear el
   subpaquete shared antes (con `pyproject.toml` propio).
2. Declarar el paquete en `[project.dependencies]` del portador.
3. Re-exportar los simbolos necesarios desde el `__init__.py` del
   portador.
4. Actualizar la tabla "Catalogo de portadores" de esta rule.
5. Si otro shared depende del nuevo, agregar `internal-deps` en su
   `pyproject.toml`.
6. Tests unit del re-export en `shared/tests/unit/shared/<X>/`.
7. `serverless lint-deps` debe pasar.

## Como migrar un service que importa un paquete prohibido

1. Verificar que el paquete tiene portador shared (tabla arriba). Si no,
   primero el paso "agregar paquete externo".
2. Reemplazar el import en `core/`:
   `from <paquete> import X` -> `from shared.<portador> import X`.
3. Si el service declara el paquete en su `pyproject.toml`, retirarlo
   (excepto que sea un caso EXCEPTION D-3 documentado y aprobado).
4. `serverless tests --type=unit --lambda=<X>` verde.
5. `serverless lint-deps --lambda=<X>` exit 0.

## Verificacion

```bash
python devtools/run.py serverless lint-deps                  # global
python devtools/run.py serverless lint-deps --lambda=<X>     # uno
python devtools/run.py serverless tests --type=unit          # suite
```

## Anti-patrones

| Anti-patron | Por que | Correccion |
|-------------|---------|------------|
| `from pydantic import BaseModel` en `core/models/<X>.py` | Bypassa el portador shared | `from shared.core import BaseModel` |
| `import boto3` + `boto3.client(...)` en `core/services/` | Duplica clientes, sin singleton, sin testing centralizado | Usar/agregar wrapper en `shared.aws.<recurso>` |
| Declarar `pydantic[email]` en el `pyproject.toml` del service | Duplica con shared.core, lint-deps falla | Retirar del service; shared.core lo aporta |
| `from boto3.dynamodb.types import TypeDeserializer` | Import directo a boto3 | `from shared.aws import TypeDeserializer` |
| Mockear el cliente boto3 directo en tests del service | Acopla el test al detalle de impl | Mockear `shared.aws.send_email` (o el wrapper que aplique) |
| Crear un re-export en shared sin tests | El cierre transitivo se rompe sin alerta | Agregar test unit del re-export |

## Referencias cruzadas

- `.claude/rules/lambda-controller.md` — formato de Lambdas (operation+action)
- `.claude/docs/lambda-shared-imports/` — explicacion conceptual + ejemplos
- `serverless/lambda/shared/<X>/__init__.py` — fuente de verdad de los re-exports
- `devtools/serverless/import_validator.py` — implementacion del check
```

### G.2 — Skill nueva: `.claude/skills/lambda-shared-imports/SKILL.md`

Skill invocable con `/lambda-shared-imports`. Frontmatter en ingles (la
rule sigue activacion automatica para edicion de los paths; la skill es
para invocacion manual cuando el dev pide "donde vive boto3" o "que
shared porta tal paquete").

```yaml
---
name: lambda-shared-imports
description: >
  Catalog of which shared subpackage carries each external package
  (pydantic, sqlalchemy, boto3, aws-lambda-powertools, ...) in the
  serverless backend. Use when the user says "donde vive pydantic",
  "como importar boto3 en el lambda", "portador shared", "shared-only
  imports", "shared only", "como agregar paquete shared", "where does
  pydantic live", "where to import boto3", "shared subpackage", or asks
  about the import contract of the serverless services.
user-invocable: true
allowed-tools: Read, Glob, Grep
argument-hint: "opcional: nombre del paquete externo a buscar"
---
```

Cuerpo: cheatsheet + procedimiento para agregar paquete + ejemplos de
migracion. Replica el contenido de la rule pero con tono de "guia rapida".

### G.3 — Docs conceptual: `.claude/docs/lambda-shared-imports/`

Tres archivos cortos (<300 lineas c/u), navegables:

- `README.md` — indice + tabla de paquetes -> portadores.
- `01-portadores-shared.md` — un parrafo por subpaquete shared explicando
  que paquetes externos absorbe y por que (con la firma del `__init__.py`).
- `02-migracion-y-extension.md` — procedimientos: agregar paquete nuevo,
  agregar re-export, migrar un service que importa directo.

### G.4 — Actualizar `lambda-controller.md`

Editar `.claude/rules/lambda-controller.md` para agregar 1 bullet en
"Reglas criticas":

```diff
+ - **SIEMPRE** los `core/**/*.py` del service importan paquetes externos
+   solo via `shared.*` (ver `.claude/rules/lambda-shared-imports.md` para
+   el catalogo de portadores y procedimientos).
```

Y en la tabla "Referencias cruzadas":

```diff
+ - shared-only imports: `.claude/rules/lambda-shared-imports.md` + skill
+   `lambda-shared-imports` + `.claude/docs/lambda-shared-imports/`
```

### G.5 — Actualizar `CLAUDE.md` (raiz)

Agregar fila a la tabla "Arbol de conocimiento":

```diff
+ | Shared-only imports | `.claude/rules/lambda-shared-imports.md` o skill `lambda-shared-imports` | Antes de tocar imports en `serverless/lambda/services/*/core/*` o agregar un paquete externo al backend |
```

Y a la tabla "Skills disponibles":

```diff
+ | `lambda-shared-imports` | Catalogo de portadores shared para los paquetes externos del backend (pydantic, sqlalchemy, boto3, aws-lambda-powertools); como agregar/migrar |
```

## Archivos afectados

### Crear

- `.claude/rules/lambda-shared-imports.md`
  - Verificar: validacion `claude --permission-mode bypassPermissions
    --disallowedTools "WebSearch" "WebFetch" --strict-mcp-config
    --mcp-config '{"mcpServers":{}}' --output-format json -p "<prompt
    espanol>"` con 5 angulos (ver `.claude/rules/claude-config-testing.md`).
- `.claude/skills/lambda-shared-imports/SKILL.md`
  - Verificar: idem (skill invocable + matching keywords).
- `.claude/docs/lambda-shared-imports/README.md`
- `.claude/docs/lambda-shared-imports/01-portadores-shared.md`
- `.claude/docs/lambda-shared-imports/02-migracion-y-extension.md`

### Modificar

- `.claude/rules/lambda-controller.md` — bullet + ref cruzada.
- `CLAUDE.md` — entradas en "Arbol de conocimiento" y "Skills disponibles".

## Validacion de configuracion Claude

Como exige `.claude/rules/claude-config-testing.md`, despues de crear la
rule y la skill, ejecutar 5 prompts en espanol que cubran:

1. Pregunta general: "donde vive pydantic en el backend serverless del portfolio".
2. Pregunta tecnica: "como hago para que un nuevo lambda use boto3 sin
   importarlo directo".
3. Codigo de error / sintoma: "serverless lint-deps me dice imports
   prohibidos, que hago".
4. Negativo: "como configurar tailwind en astro" (NO debe disparar la rule).
5. Terminologia trampa: "como uso EmailStr en un controller del backend".

Para cada uno, verificar `num_turns > 1` (la skill/rule se invoco) y que
el `result` cite los archivos correctos. Documentar resultados en el body
del commit.

## Criterios de aceptacion

- **AC-G1**: Given los archivos creados, When `ls .claude/rules/
  lambda-shared-imports.md`, Then existe; idem para skill y docs.
- **AC-G2**: Given los 5 prompts de validacion, When se ejecutan con
  `claude -p`, Then `num_turns > 1` en al menos 4 de los 5 (los 4
  positivos invocan la rule/skill; el negativo NO).
- **AC-G3**: Given `CLAUDE.md`, When inspecciono la tabla "Arbol de
  conocimiento", Then aparece la fila "Shared-only imports".
- **AC-G4**: Given `.claude/rules/lambda-controller.md`, When inspecciono
  "Reglas criticas", Then aparece el bullet de imports via shared con
  ref a la rule nueva.

## Verificacion

```bash
# Sintaxis Markdown / sin links rotos
ls .claude/rules/lambda-shared-imports.md
ls .claude/skills/lambda-shared-imports/SKILL.md
ls .claude/docs/lambda-shared-imports/

# Validacion Claude (1 prompt; los demas en el commit body)
claude --permission-mode bypassPermissions \
  --disallowedTools "WebSearch" "WebFetch" \
  --strict-mcp-config --mcp-config '{"mcpServers":{}}' \
  --output-format json \
  -p "donde vive pydantic en el backend serverless del portfolio" \
  2>&1 | tail -40
```

## Commit

```text
docs(claude): rule + skill + docs para shared-only imports en lambdas

- .claude/rules/lambda-shared-imports.md (rule autoritativa): catalogo
  de portadores shared, patrones correctos/incorrectos, anti-patrones,
  procedimientos para agregar paquete externo y migrar service
- .claude/skills/lambda-shared-imports/SKILL.md: skill invocable con
  /lambda-shared-imports; description en ingles con keywords es/en;
  user-invocable, allowed-tools Read/Glob/Grep
- .claude/docs/lambda-shared-imports/: 3 docs (README, portadores,
  migracion-y-extension)
- .claude/rules/lambda-controller.md: agrega bullet de imports via shared
  + ref cruzada a la rule nueva
- CLAUDE.md: agrega entradas en arbol de conocimiento y skills
- Validado con 5 prompts en espanol (num_turns > 1 en los 4 positivos,
  el negativo no dispara la skill); documentado en este commit body
```
