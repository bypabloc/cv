# Fase C — devtools/serverless/change_detector.py

> Dado un sha base + sha head, devuelve la lista de lambdas cuyo
> deploy hay que disparar. Considera cambios directos
> (`services/<X>/core/**`) + cambios en `shared/**` propagados via el
> cierre transitivo de `internal-deps`.

## Contexto / Problema

El workflow `deploy-backend.yml` debe redeployar SOLO los lambdas
afectados (decision 3 del plan). Hoy no hay nada que diga "el cambio
X afecta a estos lambdas".

Reglas:

1. `serverless/lambda/services/<X>/**` cambia -> redeploy `<X>`.
2. `serverless/lambda/services/<X>/pyproject.toml` cambia -> redeploy `<X>`.
3. `serverless/lambda/shared/<Y>/**` cambia -> redeploy TODOS los
   lambdas cuyo cierre transitivo incluye `shared.<Y>`. La logica
   ya existe en `devtools/serverless/shared_resolver.py`.

Excepciones (cambios que NO disparan deploy):

- `serverless/lambda/services/<X>/tests/**` — tests no van al zip.
- `serverless/lambda/services/<X>/events/**` — eventos de invocacion
  local, no van al zip.
- `serverless/lambda/services/<X>/build/**` — artefacto efimero
  (gitignored, pero por si acaso).
- `serverless/lambda/services/db/core/seeds/data/**` — los seeds
  cambian con frecuencia (cada vez que se modifica el CV en YAML),
  pero el deploy del Lambda `db` no necesita re-correrse. El operador
  re-corre el seed manualmente con `serverless run --lambda=db
  --event=seed.json` cuando lo decida.
- `serverless/lambda/shared/tests/**` — tests de shared.

## Solucion

Crear `devtools/serverless/change_detector.py`:

```python
"""@module devtools.serverless.change_detector — detecta lambdas afectados.

Dado un diff entre dos shas, devuelve la lista de lambdas cuyo deploy
hay que disparar. Considera:
- Cambios directos en services/<X>/core/ -> redeploy X.
- Cambios en shared/<Y>/ -> redeploy todos los lambdas cuyo cierre
  transitivo incluye shared.<Y> (via shared_resolver).

Excluye paths que no afectan al artefacto desplegado (tests/, events/,
seeds/data/).
"""

from __future__ import annotations

import subprocess
from collections.abc import Iterable
from pathlib import Path

from serverless.resolve import available_lambdas
from serverless.shared_resolver import resolve_lambda_shared


# Paths dentro de services/<X>/ que NO disparan redeploy.
_EXCLUDED_SERVICE_SUBPATHS = ('tests/', 'events/', 'build/', 'core/seeds/data/')

# Paths dentro de shared/ que NO disparan redeploy.
_EXCLUDED_SHARED_SUBPATHS = ('tests/',)


def _git_diff_files(base_sha: str, head_sha: str) -> list[str]:
    """Devuelve los archivos modificados entre base_sha y head_sha."""
    result = subprocess.run(
        ['git', 'diff', '--name-only', f'{base_sha}..{head_sha}'],
        capture_output=True, text=True, check=True,
    )
    return [line for line in result.stdout.splitlines() if line]


def _is_service_change(path: str) -> str | None:
    """Si el path es un cambio de un service que dispara redeploy,
    devuelve el nombre del service. Si no, None."""
    parts = path.split('/')
    if len(parts) < 4:
        return None
    if parts[0] != 'serverless' or parts[1] != 'lambda':
        return None
    if parts[2] != 'services':
        return None
    service_name = parts[3]
    rest = '/'.join(parts[4:])
    if any(rest.startswith(excluded) for excluded in _EXCLUDED_SERVICE_SUBPATHS):
        return None
    return service_name


def _is_shared_change(path: str) -> str | None:
    """Si el path es un cambio en un subpaquete shared que dispara
    redeploy de los consumers, devuelve el nombre del subpaquete.
    Si no, None."""
    parts = path.split('/')
    if len(parts) < 4:
        return None
    if parts[:3] != ['serverless', 'lambda', 'shared']:
        return None
    subpackage = parts[3]
    rest = '/'.join(parts[4:])
    if any(rest.startswith(excluded) for excluded in _EXCLUDED_SHARED_SUBPATHS):
        return None
    return subpackage


def _consumers_of_shared(subpackage: str, lambdas_root: Path) -> set[str]:
    """Devuelve los lambdas cuyo cierre transitivo incluye `shared.<subpackage>`."""
    consumers: set[str] = set()
    for lambda_name in available_lambdas():
        lambda_root = lambdas_root / lambda_name
        closure = resolve_lambda_shared(lambda_root)
        if subpackage in closure:
            consumers.add(lambda_name)
    return consumers


def detect_affected_lambdas(
    base_sha: str,
    head_sha: str,
    lambdas_root: Path,
) -> set[str]:
    """Devuelve el conjunto de lambdas que deben redeployarse.

    Parameters
    ----------
    base_sha : str
        SHA base de la comparacion (ej. el sha del ultimo deploy de prod).
    head_sha : str
        SHA al que se quiere deployar.
    lambdas_root : Path
        `serverless/lambda/services/`.

    Returns
    -------
    set[str]
        Nombres de los lambdas afectados.
    """
    files = _git_diff_files(base_sha, head_sha)
    affected: set[str] = set()

    for path in files:
        service = _is_service_change(path)
        if service is not None:
            affected.add(service)
            continue
        shared = _is_shared_change(path)
        if shared is not None:
            affected.update(_consumers_of_shared(shared, lambdas_root))

    return affected
```

### Output como JSON (para consumir desde GitHub Actions)

Wrap CLI en `devtools/serverless/main.py`:

```python
def cmd_detect_changes(flags: dict) -> int:
    """Comando: serverless detect-changes --base=<sha> --head=<sha>.

    Imprime JSON {"affected": [...]} con los lambdas a redeployar.
    """
    base = flags.get('base')
    head = flags.get('head', 'HEAD')
    if not base:
        print('ERROR: --base=<sha> requerido', file=sys.stderr)
        return 1

    from serverless.change_detector import detect_affected_lambdas

    lambdas_root = (
        Path(__file__).resolve().parents[2] / 'serverless' / 'lambda' / 'services'
    )
    affected = detect_affected_lambdas(base, head, lambdas_root)
    print(json.dumps({'affected': sorted(affected)}))
    return 0
```

Uso desde el workflow:

```yaml
- name: Detect affected lambdas
  id: detect
  run: |
    base="${{ github.event.before }}"
    head="${{ github.sha }}"
    output=$(python devtools/run.py serverless detect-changes \
      --base="$base" --head="$head")
    echo "matrix=$output" >> "$GITHUB_OUTPUT"

- name: Deploy lambdas (matrix)
  if: fromJSON(steps.detect.outputs.matrix).affected[0] != null
  strategy:
    matrix:
      lambda: ${{ fromJSON(steps.detect.outputs.matrix).affected }}
  ...
```

### Tests

`devtools/tests/unit/src/serverless/change_detector.py`:

- `test_detect_service_change_returns_service_name`
- `test_detect_service_change_ignores_tests_subpath`
- `test_detect_service_change_ignores_events_subpath`
- `test_detect_service_change_ignores_seeds_data_subpath`
- `test_detect_shared_change_returns_subpackage`
- `test_detect_shared_change_ignores_tests_subpath`
- `test_consumers_of_shared_returns_all_lambdas_using_db` (usa el shared
  real con shared_resolver)
- `test_consumers_of_shared_returns_empty_for_unused_subpackage`
- `test_detect_affected_lambdas_combines_direct_and_transitive`
- `test_detect_affected_lambdas_returns_empty_when_no_relevant_changes`
- `test_cmd_detect_changes_emits_json_payload`
- `test_cmd_detect_changes_fails_without_base_flag`

Los tests que invocan `git diff` mockean `subprocess.run` para
controlar la lista de archivos modificados.

## Archivos afectados

### Crear

- `devtools/serverless/change_detector.py` — modulo nuevo.
- `devtools/tests/unit/src/serverless/change_detector.py` — 12 tests.

### Modificar

- `devtools/serverless/main.py` — agrega `cmd_detect_changes` y la
  ruta CLI `detect-changes`.
- `devtools/serverless/flags.py` — agrega flags `--base` y `--head`.

## Criterios de aceptacion

- **AC-C1**: Given un diff que solo toca `serverless/lambda/services/cv/core/services/foo.py`,
  When `detect_affected_lambdas`, Then `{'cv'}`.
- **AC-C2**: Given un diff que solo toca `serverless/lambda/services/cv/tests/test_foo.py`,
  Then `set()` (tests no disparan deploy).
- **AC-C3**: Given un diff que solo toca `serverless/lambda/shared/db/__init__.py`,
  Then `{'cv', 'db', 'stream_processor'}` (los 3 lambdas que usan shared.db
  segun `internal-deps`).
- **AC-C4**: Given un diff que toca services/cv/ + services/db/core/seeds/data/foo.yaml,
  Then `{'cv'}` (los seeds no disparan deploy de db).
- **AC-C5**: Given un diff con cambios mezclados (shared.core + services/contact_form/),
  Then todos los lambdas (porque shared.core es base de todos) ∪
  `{'contact_form'}`.

## Verificacion

```bash
python -m compileall -q devtools/serverless/change_detector.py
python devtools/run.py test_runner --module=devtools --type=unit -- -k change_detector

# Smoke con git real
python devtools/run.py serverless detect-changes \
  --base=$(git rev-parse HEAD~10) --head=HEAD
```

## Commit

```text
feat(devtools/serverless): change_detector helper detecta lambdas afectados

- change_detector.py: detect_affected_lambdas(base_sha, head_sha,
  lambdas_root) devuelve el set de lambdas a redeployar basado en
  git diff + cierre transitivo de shared (shared_resolver)
- Excluye paths que no afectan el zip: tests/, events/, build/,
  core/seeds/data/ del lambda db
- Comando CLI: serverless detect-changes --base=<sha> --head=<sha>
  imprime JSON {affected: [...]} para que GitHub Actions lo
  consuma como matrix
- 12 tests unit con subprocess mockeado: cambios directos, cambios
  en shared, excepciones (tests/events/seeds), combinaciones
- Habilita el workflow deploy-backend.yml de la Fase E"
```
