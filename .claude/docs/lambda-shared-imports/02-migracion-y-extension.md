# Migracion y extension

> Procedimientos paso a paso para (1) migrar un service que importa
> directamente un paquete externo, (2) agregar un paquete externo
> nuevo al backend, (3) agregar un re-export en un shared existente.

## 1. Migrar un service con imports prohibidos

### Cuando aplica

`serverless lint-deps --lambda=<X>` reporta:

```text
FAIL  X: 1 import(s) prohibido(s) directo(s) en core/:
  - core/services/foo.py:5 -> from pydantic import ...
    paquete prohibido: 'pydantic'. Importa desde shared.*
```

### Pasos

1. **Identificar el portador shared** en
   [01-portadores-shared.md](01-portadores-shared.md). Tabla resumen.

2. **Reemplazar el import** en el archivo del service:

   ```diff
   - from pydantic import BaseModel, Field
   + from shared.core import BaseModel, Field
   ```

3. **Si el service declara el paquete en su `pyproject.toml`,
   retirarlo**:

   ```diff
   - dependencies = [
   -   "pydantic[email]>=2.5,<3.0",
   - ]
   + dependencies = []
   ```

   (El cierre transitivo de shared ya lo aporta.)

4. **Re-sincronizar el `.venv` del lambda**:

   ```bash
   python devtools/run.py serverless tests --type=unit --lambda=<X>
   ```

   El comando `tests` corre `ensure_lambda_venv` que reinstala
   las deps del cierre transitivo de shared en el venv aislado.

5. **Validar los dos checks**:

   ```bash
   python devtools/run.py serverless lint-deps --lambda=<X>
   ```

   Debe imprimir:
   ```text
   OK  <X>: sin deps duplicadas con shared/.
   OK  <X>: cero imports prohibidos en core/.
   ```

### Ejemplo: contact_form (mayo 2026)

```diff
# pyproject.toml
- dependencies = ["pydantic[email]>=2.5,<3.0"]
+ dependencies = []

# core/models/contact.py
- from pydantic import BaseModel, EmailStr, Field, field_validator
+ from shared.core import BaseModel, EmailStr, Field, field_validator

# core/services/contact_service.py
- import boto3
- from aws_lambda_powertools.metrics import MetricUnit
- from shared.observability.logger import logger
- from shared.observability.metrics import metrics
+ from shared.aws import send_email
+ from shared.observability import MetricUnit, logger, metrics

- def _ses_client() -> Any:
-     return boto3.client('sesv2', region_name=os.environ.get('AWS_SES_REGION', 'us-east-1'))
-
- response = _ses_client().send_email(
-     FromEmailAddress=..., Destination=..., ReplyToAddresses=..., Content=...
- )
+ response = send_email(
+     from_address=..., to_addresses=..., subject=...,
+     text_body=..., html_body=..., reply_to=...,
+ )
```

## 2. Agregar un paquete externo nuevo al backend

### Cuando aplica

Un Lambda nuevo necesita una libreria que ningun shared aporta hoy
(ej. `requests`, `httpx-cache`, `polars`).

### Pasos

1. **Decidir el shared portador**: ¿el paquete encaja en aws, core, db,
   http, observability, dynamodb, cache, rate_limit, lambda_kit? Si NO
   encaja en ninguno, crear un subpaquete shared nuevo (raro pero
   permitido).

2. **Declarar el paquete en `[project.dependencies]` del portador**:

   ```toml
   # serverless/lambda/shared/http/pyproject.toml
   dependencies = [
     "httpx>=0.27.0,<1.0",
     "httpx-cache>=0.13,<1.0",  # NUEVO
   ]
   ```

3. **Crear el modulo / re-export** en el portador:

   ```python
   # serverless/lambda/shared/http/cache.py
   from httpx_cache import Client as CachedClient

   __all__ = ['CachedClient']
   ```

   ```python
   # serverless/lambda/shared/http/__init__.py
   from shared.http.cache import CachedClient
   ```

4. **Test unit del re-export**:

   ```python
   # serverless/lambda/shared/tests/unit/shared/http/test_cached_client_reexport.py
   from httpx_cache import Client as HttpxCacheClient
   from shared.http import CachedClient


   def test_cached_client_is_httpx_cache_class() -> None:
       assert CachedClient is HttpxCacheClient
   ```

5. **Actualizar las tablas** en
   [01-portadores-shared.md](01-portadores-shared.md) y
   `.claude/rules/lambda-shared-imports.md`.

6. **Si otro shared depende del nuevo**: agregar a `[tool.shared]
   internal-deps` del consumer (ej. `shared.cache` declara
   `internal-deps = ["http"]`).

7. **Si el `serverless/pyproject.toml` (entorno centralizado de los
   tests de shared) lo necesita**: agregarlo a su
   `[project.dependencies]` y correr `uv sync` desde la raiz del
   serverless.

8. **Verificar**: `python devtools/run.py serverless lint-deps` debe
   pasar para los 5 lambdas.

## 3. Agregar un re-export en un shared existente

Caso comun: un service necesita un simbolo nuevo (ej. `update` de
SQLAlchemy) y el subpaquete portador ya tiene el paquete declarado en
sus deps, solo falta re-exportarlo.

### Pasos

1. Editar el `__init__.py` del portador:

   ```diff
   # serverless/lambda/shared/db/__init__.py
   - from sqlalchemy import func, select
   + from sqlalchemy import func, select, update
   ```

2. Agregar el simbolo a `__all__` (ordenado alfabeticamente):

   ```diff
   __all__ = [
       'Base',
       ...
       'select',
   +   'update',
   ]
   ```

3. Test unit del re-export:

   ```python
   # serverless/lambda/shared/tests/unit/shared/db/test_sqlalchemy_reexport.py
   def test_update_is_sqlalchemy_update() -> None:
       import sqlalchemy
       from shared.db import update
       assert update is sqlalchemy.update
   ```

4. Actualizar la tabla de portadores en
   [01-portadores-shared.md](01-portadores-shared.md).

5. Verificar: `serverless tests --type=unit --shared` verde,
   `serverless lint-deps` verde.

## Anti-patrones

| Anti-patron | Por que | Correccion |
|-------------|---------|------------|
| Migrar el service ANTES de re-exportar el simbolo en shared | El service no compila | Re-exportar primero (Fase A-D del plan), luego migrar (Fase E) |
| Agregar un re-export sin test | El cierre transitivo se rompe sin alerta | Test unit `test_<paquete>_reexport.py` |
| Olvidar agregar el simbolo a `__all__` | El re-export no se expone publicamente | Agregar (ordenado alfabeticamente) |
| Editar tests del service para que mockeen el paquete externo crudo | Acopla al detalle de impl interno del helper shared | Mockear el helper shared (ej. `shared.aws._client` o `shared.aws.send_email`) |
| Declarar el paquete en el `pyproject.toml` del service tras la migracion | Duplica con shared, lint-deps falla | Retirar — el cierre transitivo lo aporta |
| Crear un subpaquete shared nuevo solo para re-exportar un simbolo | Sobrediseno | Re-exportar desde un subpaquete existente que tenga sentido tematico |

## Navegacion

- [Volver al README](README.md)
- [Portadores shared (catalogo)](01-portadores-shared.md)
- Regla autoritativa: `.claude/rules/lambda-shared-imports.md`
