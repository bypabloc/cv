---
description: "Estandares de desarrollo Python 3.14 para devtools/ y .git-hooks/: estilo, estructura de archivos, type hints, testing y complejidad"
globs: "**/*.py"
---

# Python Development Standards

> El unico Python del portfolio vive en `devtools/` (CLI orquestador) y
> `.git-hooks/` (quality gates autocontenidos). El proyecto NO tiene backend:
> es un monorepo Astro estatico. Estas reglas aplican a esos dos arboles.

## Estilo

- Python 3.14 estricto (target-version `py314` en Ruff). Excepciones de bootstrap (`devtools/run.py`, `.git-hooks/*.py`) pinneadas a `py313` via `per-file-target-version` para preservar sintaxis con parentesis en `except`.
- Ruff como linter y formatter. `devtools/` lleva su propio `ruff.toml` autocontenido (CLI + bootstrap py313): sin base compartida, declara reglas, ignores y formatter completos. Ruff lo autodetecta cuando el cwd es la raiz del modulo.
- line-length 80, indent 4, line-ending lf, single quotes (`flake8-quotes` + formatter), trailing commas habilitadas (no auto-agregadas — ver nota abajo).
- Type hints requeridos en todas las funciones publicas (`ANN`).
- NO usar `from __future__ import annotations` (PEP 649: Python 3.14 tiene lazy annotations nativo).
- Usar union syntax moderna: `str | None` en vez de `Optional[str]`.
- Type parameter syntax (PEP 695): `def first[T](items: list[T]) -> T:`.

### Conflictos formatter vs linter (ignorados intencionalmente)

Estas reglas estan en `ignore` porque chocan con el comportamiento del formatter:

- `E501` (line too long): el formatter ya gestiona el corte de lineas
- `E203` (whitespace before `:`): el formatter ya respeta PEP 8
- `COM812` (missing trailing comma): conflicto con formatter — ver nota abajo
- `COM819` (prohibited trailing comma): companion de COM812
- `ISC001` (implicit string concat single-line): el formatter prefiere doble
- `Q001` (multiline-quotes): el formatter prefiere comillas dobles en multilinea

### Comillas: convencion semantica

- **Single quotes (`'...'`)** para strings tecnicos: keys de dicts, valores de codigo, identificadores, paths, choices.
- **Double quotes (`"..."`)** aceptables solo para texto legible por humanos: mensajes de error de usuario, mensajes de log, contenido para UI.
- **Triple double quotes (`"""..."""`)** para docstrings y strings multilinea.

```python
# Correcto: distincion semantica clara
record['status'] = 'pending'
config = {'host': 'localhost', 'port': 9970}
logger.error("No se pudo conectar al provider, reintentando")
raise ValueError("El monto debe ser positivo")

# Incorrecto: comilla doble en string tecnico
record["status"] = "pending"
```

Ver `"..."` en el codigo deberia indicar "este string lo veria un humano".

### Trailing commas (motivacion: minimizar git diff)

La regla NO es estetica. Al agregar un item nuevo, solo aparece **una** linea
modificada en el diff (la nueva), no dos (la nueva mas la coma agregada en la
anterior).

`COM812` esta en `ignore` (conflicto con formatter), pero el formatter respeta
trailing commas existentes y `skip-magic-trailing-comma = false` permite que
una trailing comma fuerce el wrap a multilinea. Resultado: las trailing commas
se preservan al formatear, y el dev las agrega manualmente al escribir.

```python
# Correcto: agregar 'd' modifica solo 1 linea en el diff
my_dict = {
    'a': 1,
    'b': 2,
    'c': 3,
}

# Incorrecto: agregar 'd' modifica 2 lineas
my_dict = {
    'a': 1,
    'b': 2,
    'c': 3
}
```

### Tipado como auto-documentacion

Los desarrolladores leen mas codigo del que escriben. La firma tipada de una
funcion es la primera fuente de informacion para entender que hace, sin tener
que leer el body o el docstring.

```python
# Mal: hay que leer el cuerpo para saber que retorna
def fib(n):
    a, b = 0, 1
    while a < n:
        yield a
        a, b = b, a + b

# Bien: la firma sola dice "iterador de int sobre n int"
def fib(n: int) -> Iterator[int]:
    a, b = 0, 1
    while a < n:
        yield a
        a, b = b, a + b
```

Ruff `ANN` rules hacen enforce de annotations en funciones publicas.

## Estructura de archivos (OBLIGATORIO)

- Un archivo por clase/funcion principal, agrupados en carpetas por tipo
- Archivos NO deben superar 300-500 lineas como maximo
- Usar `__init__.py` para re-exportar los nombres publicos del modulo
- `__init__.py` solo contiene imports y re-exports, NUNCA logica

### Patron correcto (un archivo por responsabilidad)

Cada script de `devtools/` es un paquete con un dominio acotado. Cuando un
modulo supera ~300 lineas se parte por dominio logico (ver `docker/`, `scan/`,
`test_runner/` en el repo como ejemplo de referencia):

```
devtools/<script>/
├── __init__.py          # re-exports de los nombres publicos
├── main.py              # entry point: def main(flags: dict)
├── flags.py             # parsing + validacion de flags
├── <dominio_1>.py       # un archivo por dominio logico
├── <dominio_2>.py
└── README.md            # documentacion del script
```

### Patron incorrecto (archivos monoliticos)

```
devtools/<script>/
├── main.py       # parsing + validacion + toda la logica en un solo archivo
└── README.md
```

### Reglas de division

- Si un archivo supera 300 lineas, dividirlo inmediatamente
- Un archivo por dominio logico (no mezclar parsing de flags con ejecucion)
- `flags.py` solo parsing/validacion; `main.py` solo orquestacion

## Funciones puras y keyword-only args (patron recomendado)

- Preferir funciones sobre clases (a menos que se necesite estado complejo)
- Usar `*` para forzar keyword-only arguments en funciones con varios params
- Una funcion = una responsabilidad clara
- Retornar valores serializables (dict, list, primitivos), no objetos opacos
- Lanzar excepciones custom para errores de usuario (exit code 1)

```python
def build_targets(
    *,
    modules: list[str],
    env: str,
    dry_run: bool = False,
) -> list[str]:
    """Resuelve los targets Docker a construir para los modulos pedidos."""
    targets = [f'portfolio-{m}-{env}' for m in modules]
    if dry_run:
        logger.info('Targets resueltos (dry-run): %s', targets)
    return targets
```

## Excepciones custom (patron recomendado)

```python
# devtools/shared/exceptions.py
class DevtoolsError(Exception):
    """Error de usuario en un script de devtools (exit code 1)."""

    def __init__(self, message: str = '', extra: dict | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.extra = extra or {}


class InvalidFlagError(DevtoolsError): ...
class TargetNotFoundError(DevtoolsError): ...
```

- NUNCA usar `except:` o `except Exception:` sin re-raise
- Usar `raise ... from e` para preservar cadena de excepciones
- Manejar en la capa de entry point (`main.py`), no en helpers profundos

## Logging

- NUNCA f-strings en llamadas a logging (rompe lazy evaluation)
- Usar logging estructurado con contexto

```python
# Correcto
logger.info('Target built', extra={'target': target_name})
logger.warning('Attempt %d failed: %s', attempt, error)

# Incorrecto
logger.info(f'Target built: {target_name}')
```

`print()` esta permitido SOLO como salida de CLI (`T20` ignorado en
`devtools/`). Para info de ejecucion interna usar `logging`.

## Estructura de scripts

- Incluir `if __name__ == "__main__":` en scripts ejecutables
- Usar `logging` module para info de ejecucion interna
- Exit codes: 0 (ok), 1 (error de usuario), 2 (error interno)

## APIs externas

- Retry con backoff exponencial para llamadas a APIs
- Timeout explicito en todas las requests (default: 30s)
- Validar respuestas antes de procesar
- Nunca hardcodear API keys — usar `.env` o variables de entorno

## Testing

- Framework: pytest
- Coverage minimo: 80% per-file (enforced en pre-push)
- Patron AAA en el cuerpo + **BDD-style en el docstring** (Given/When/Then)
- Un concepto de assertion por test (multiples `assert` ok si validan lo mismo)
- Nomenclatura metodos: `test_<unit>_<scenario>_<expected>`
- `@pytest.mark.parametrize` para multiples escenarios de input
- Tests en `devtools/tests/` (espejan la estructura de `devtools/`)
- Ejecutar: `python devtools/run.py test_runner --module=devtools --type=unit`

### BDD-style obligatorio en el docstring

Mantener AAA como estructura del cuerpo. El docstring describe el
comportamiento en formato Given/When/Then — facilita lectura sin contexto
IA y traza el test al criterio de aceptacion humano.

```python
def test_build_targets_when_dry_run_returns_resolved_names():
    """
    Given una lista de modulos y env='local',
    When se invoca build_targets con dry_run=True,
    Then retorna los nombres de container con prefijo portfolio-.
    """
    # Arrange
    modules = ['hub', 'generic']

    # Act
    targets = build_targets(modules=modules, env='local', dry_run=True)

    # Assert
    assert targets == ['portfolio-hub-local', 'portfolio-generic-local']
```

### Asserts EXACTOS, no rangos (enforced en pre-commit)

El hook `weak_assertion` (`.git-hooks/weak_assertion_detector.py`) rechaza
asserts vagos en archivos de test staged. Reglas:

```python
# Rechazado:
assert x > 0
assert result is not None
assert isinstance(result, dict)
assert len(items) >= 1

# Aceptado:
assert x == 42
assert result == {'status': 'ok'}
assert items == [item1, item2]
```

Si necesitas range/type assertions justificadas, usar `# noqa: WEAK-ASSERT`
inline (con razon en comentario).

### Que mockear vs que no

- MOCKEAR: APIs HTTP externas, file storage, subprocess hacia Docker, time/datetime
- NO MOCKEAR: parsing de flags propio, transformaciones puras, helpers dentro del scope del test

### Property-based testing (Hypothesis)

Para algoritmos puros (parsing de flags, resolucion de paths, transformaciones)
se puede preferir `hypothesis` sobre tests parametrizados manuales. Deriva
los tests de los type hints.

```python
from hypothesis import given, strategies as st


@given(env=st.sampled_from(['local', 'dev', 'test', 'prod']))
def test_container_name_includes_env(env: str) -> None:
    """
    Property: el nombre del container siempre termina con el env pedido,
    para cualquier env valido.
    """
    name = container_name(module='hub', env=env)
    assert name.endswith(f'-{env}')
```

## Complejidad

- Max complejidad ciclomatica por funcion: 10 (enforced via Ruff C90)
- Max argumentos posicionales: 5 (usar dataclasses/TypedDict para mas)
- Max lineas por funcion: ~50 (soft limit)
- No anidar try/except — extraer a funciones separadas

## Dependencias

- Devtools: `devtools/pyproject.toml` (ruff, GitPython, httpx, pytest) + `devtools/uv.lock`
- `>=` aceptable para tooling de devtools (no es codigo de produccion)
- Gestionar via uv: `uv add <pkg>` para agregar, `uv lock --upgrade-package <pkg>` para actualizar uno solo, `uv sync --frozen` para reproducir; `python devtools/run.py upgrade_deps --dry-run` para ver el cuadro completo de upgrades disponibles
</content>
</invoke>
