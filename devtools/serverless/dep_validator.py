"""Validador de dependencias duplicadas entre un lambda y `shared/`.

Regla de dedup D-3 del plan `serverless-lambda-independence`: si una
dependencia le llega a un lambda por el cierre transitivo de `shared/`,
su `pyproject.toml` NO debe declararla. Sin enforcement, la duplicacion
vuelve a aparecer sin que nada lo detecte.

Este modulo escanea el `pyproject.toml` de un lambda, resuelve el cierre
de `shared/` (via `shared_resolver`) y reporta las deps declaradas que
ya aporta `shared/`.

La comparacion es por NOMBRE CANONICO (PEP 503: minusculas, `_`/`.` ->
`-`, sin extras ni version): `psycopg[binary]` y `psycopg` son la misma
lib; `aws-lambda-powertools[all]` y `aws_lambda_powertools` tambien.

devtools corre en Python 3.14 (`devtools/.venv`); `tomllib` es stdlib.
"""

from __future__ import annotations

from dataclasses import dataclass
from dataclasses import field
from pathlib import Path
import re
import tomllib

from serverless.shared_resolver import resolve_lambda_shared


class DepValidatorError(RuntimeError):
    """Error al validar las dependencias de un lambda (exit code 1)."""


# Separadores de un spec de dependencia PEP 508: el nombre termina donde
# empieza un extra `[`, una version `<>=~!`, un marker `;` o un espacio.
_NAME_END = re.compile(r'[\[<>=!~;\s]')

# Extras de un spec PEP 508: lo que va entre corchetes, ej. `[binary]`.
_EXTRAS = re.compile(r'\[([^\]]*)\]')


def canonical_name(spec: str) -> str:
    """Devuelve el nombre canonico (PEP 503) de un spec de dependencia.

    Toma el nombre del spec (descartando extras, version y markers) y lo
    normaliza: minusculas y `_`/`.` -> `-`.

    Parameters
    ----------
    spec : str
        Spec de dependencia PEP 508, ej. `psycopg[binary]>=3.2,<4.0`.

    Returns
    -------
    str
        Nombre canonico, ej. `psycopg`.

    Examples
    --------
    >>> canonical_name('psycopg[binary]>=3.2,<4.0')
    'psycopg'
    >>> canonical_name('aws_lambda_powertools[all]>=3.0')
    'aws-lambda-powertools'
    >>> canonical_name('pydantic')
    'pydantic'
    """
    match = _NAME_END.search(spec)
    name = spec[: match.start()] if match else spec
    return re.sub(r'[_.]+', '-', name.strip().lower())


def spec_extras(spec: str) -> frozenset[str]:
    """Devuelve el conjunto de extras declarados en un spec PEP 508.

    Parameters
    ----------
    spec : str
        Spec de dependencia, ej. `pydantic[email]>=2.5`.

    Returns
    -------
    frozenset[str]
        Los extras, ej. `{'email'}`. Vacio si el spec no declara extras.

    Examples
    --------
    >>> sorted(spec_extras('pydantic[email]>=2.5'))
    ['email']
    >>> sorted(spec_extras('aws-lambda-powertools[all,tracer]>=3.0'))
    ['all', 'tracer']
    >>> sorted(spec_extras('pydantic'))
    []
    """
    match = _EXTRAS.search(spec)
    if not match:
        return frozenset()
    return frozenset(
        e.strip().lower() for e in match.group(1).split(',') if e.strip()
    )


@dataclass
class DepValidationResult:
    """Resultado de validar las deps de un lambda contra `shared/`.

    Attributes
    ----------
    lambda_name : str
        Nombre del lambda validado.
    duplicated : list[str]
        Nombres canonicos de las deps que el lambda declara Y que ya
        aporta el cierre de `shared/`. Vacio si no hay duplicacion.
    providers : dict[str, list[str]]
        Por cada dep duplicada, los subpaquetes de `shared/` del cierre
        que la aportan.
    """

    lambda_name: str
    duplicated: list[str] = field(default_factory=list)
    providers: dict[str, list[str]] = field(default_factory=dict)

    @property
    def is_valid(self) -> bool:
        """True si el lambda no duplica ninguna dep de `shared/`."""
        return not self.duplicated


def _lambda_declared_deps(lambda_root: Path) -> list[str]:
    """Lee `[project.dependencies]` del `pyproject.toml` del lambda.

    Raises
    ------
    DepValidatorError
        Si el lambda no tiene `pyproject.toml` o esta malformado.
    """
    manifest = lambda_root / 'pyproject.toml'
    if not manifest.is_file():
        raise DepValidatorError(
            f'El lambda {lambda_root} no tiene pyproject.toml.',
        )
    try:
        data = tomllib.loads(manifest.read_text(encoding='utf-8'))
    except tomllib.TOMLDecodeError as exc:
        raise DepValidatorError(
            f'pyproject.toml invalido en {lambda_root}: {exc}',
        ) from exc
    return list(data.get('project', {}).get('dependencies', []))


def validate_lambda_deps(lambda_root: Path) -> DepValidationResult:
    """Valida que el lambda no declare deps que ya aporta `shared/`.

    Escanea el `pyproject.toml` del lambda, resuelve el cierre de
    `shared/` y calcula la interseccion por nombre canonico.

    Parameters
    ----------
    lambda_root : Path
        Directorio raiz del lambda.

    Returns
    -------
    DepValidationResult
        `is_valid=True` si no hay duplicacion; `duplicated` lista las
        deps que sobran y `providers` indica que subpaquete de `shared/`
        las aporta.

    Raises
    ------
    DepValidatorError
        Si el lambda no tiene `pyproject.toml` o esta malformado.
    """
    lambda_name = lambda_root.name
    declared = _lambda_declared_deps(lambda_root)

    closure, shared_deps = resolve_lambda_shared(lambda_root)
    # Por cada nombre canonico, la union de extras que aporta shared/.
    shared_extras: dict[str, frozenset[str]] = {}
    for spec in shared_deps:
        name = canonical_name(spec)
        shared_extras[name] = shared_extras.get(
            name, frozenset()
        ) | spec_extras(spec)

    # Una dep del lambda es DUPLICADA solo si shared/ aporta el mismo
    # nombre Y un superset de sus extras: si el lambda pide un extra que
    # shared/ no da (ej. pydantic[email] vs pydantic), el lambda SI debe
    # declararla — no es duplicacion (regla D-3: declarar lo que el core/
    # usa y shared/ NO provee).
    duplicated = sorted(
        canonical_name(spec)
        for spec in declared
        if canonical_name(spec) in shared_extras
        and spec_extras(spec) <= shared_extras[canonical_name(spec)]
    )
    if not duplicated:
        return DepValidationResult(lambda_name=lambda_name)

    # Por cada dep duplicada, que subpaquetes del cierre la aportan.
    providers = _resolve_providers(duplicated, closure, lambda_root)
    return DepValidationResult(
        lambda_name=lambda_name,
        duplicated=duplicated,
        providers=providers,
    )


def _resolve_providers(
    duplicated: list[str],
    closure: set[str],
    lambda_root: Path,
) -> dict[str, list[str]]:
    """Mapea cada dep duplicada a los subpaquetes de `shared/` que la dan.

    Lee el `pyproject.toml` de cada subpaquete del cierre y busca cual
    declara la dep.
    """
    from serverless.shared_resolver import _read_manifest
    from serverless.shared_resolver import shared_root

    root = shared_root()
    providers: dict[str, list[str]] = {dep: [] for dep in duplicated}
    for subpackage in sorted(closure):
        external, _ = _read_manifest(subpackage, shared_dir=root)
        sub_canon = {canonical_name(spec) for spec in external}
        for dep in duplicated:
            if dep in sub_canon:
                providers[dep].append(subpackage)
    return providers


def format_report(result: DepValidationResult) -> str:
    """Formatea el resultado de la validacion en texto para la CLI."""
    if result.is_valid:
        return f'OK  {result.lambda_name}: sin deps duplicadas con shared/.'
    lines = [
        f'FAIL  {result.lambda_name}: declara {len(result.duplicated)} '
        f'dep(s) que ya aporta el cierre de shared/:',
    ]
    for dep in result.duplicated:
        givers = ', '.join(result.providers.get(dep, []))
        lines.append(
            f'  - {dep} (lo aporta shared/{{{givers}}}) — quitalo del '
            f'pyproject.toml del lambda (regla de dedup D-3).',
        )
    return '\n'.join(lines)


def cmd_lint_deps(flags: dict) -> int:
    """Comando `serverless lint-deps`: valida los 2 checks del contrato.

    1) Dedup D-3 (`validate_lambda_deps`): el `pyproject.toml` del lambda
       no declara deps que ya aporta el cierre transitivo de `shared/`.
    2) Imports shared-only (`scan_lambda_core`): los archivos
       `services/<X>/core/**/*.py` no importan directamente paquetes
       externos que tienen un portador shared (pydantic, sqlalchemy,
       boto3, aws_lambda_powertools, ...).

    Con `--lambda=<x>` / `--path=<dir>` valida ese lambda; sin target
    valida los 4 lambdas del backend. Exit 0 si ningun lambda viola
    ninguno de los 2 checks; 1 si alguno los viola.
    """
    from shared.console import GREEN
    from shared.console import RED
    from shared.console import _c

    from serverless.import_validator import format_import_report
    from serverless.import_validator import scan_lambda_core
    from serverless.resolve import available_lambdas
    from serverless.resolve import resolve_lambda

    has_target = bool(
        flags.get('lambda') or flags.get('path') or flags.get('module')
    )
    if has_target:
        roots = [resolve_lambda(flags).root]
    else:
        roots = [
            resolve_lambda({'lambda': n}).root for n in available_lambdas()
        ]

    rc = 0
    for root in roots:
        # Check 1: dedup D-3.
        try:
            result = validate_lambda_deps(root)
        except DepValidatorError as exc:
            print(_c(RED, str(exc)))
            rc = 1
            continue
        report = format_report(result)
        print(_c(GREEN, report) if result.is_valid else _c(RED, report))
        if not result.is_valid:
            rc = 1

        # Check 2: imports shared-only en core/.
        violations = scan_lambda_core(root)
        if violations:
            print(_c(RED, format_import_report(violations, root)))
            rc = 1
        else:
            print(
                _c(GREEN, f'OK  {root.name}: cero imports prohibidos en core/.')
            )
    return rc
