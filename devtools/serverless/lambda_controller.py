"""Comandos para lambdas que siguen el formato lambda-controller.

Estos comandos operan sobre cualquier lambda resuelto por `--lambda` o
`--path` (directorio con `manifest.yaml`). devtools provisiona cada
Lambda con AWS CLI directo: `deploy` traduce el manifiesto a llamadas
AWS via `provisioner.py`, decide create / update / no-op con el estado
local (`state.py`), y `run --stage=local` lo ejecuta con el Runtime
Interface Emulator o importando el handler (`local_runtime.py`).

Los comandos `destroy` y `status` operan sobre el estado local: borran
los recursos de un stage o comparan el estado guardado vs AWS.

El comando `tests` corre las suites unit/integration/coverage de los
lambdas y de la libreria comun `shared/`.
"""

from __future__ import annotations

from dataclasses import asdict
from dataclasses import replace
import json
from pathlib import Path
import shutil
import subprocess
from typing import Any

from shared.console import CYAN
from shared.console import GREEN
from shared.console import YELLOW
from shared.console import _c
from shared.console import _err

from serverless import local_runtime
from serverless import provisioner
from serverless import state as state_mod
from serverless.aws_cli import AwsError
from serverless.local_runtime import RuntimeMode
from serverless.packaging import PackagingError
from serverless.packaging import packaged_lambda
from serverless.packaging import zip_build_dir
from serverless.resolve import ManifestError
from serverless.resolve import ResolvedLambda
from serverless.resolve import available_lambdas
from serverless.resolve import resolve_lambda
from serverless.vendoring import VendoringError


# Raiz del backend serverless del portfolio. La suite CENTRALIZADA de la
# libreria comun (`shared/`) vive en `serverless/lambda/shared/tests/` y
# corre con el `.venv` de `serverless/` (su `pyproject.toml` trae el
# grupo dev). Cada lambda, en cambio, corre sus tests con su `.venv`
# AISLADO (`venv.ensure_lambda_venv`).
_PORTFOLIO_SERVERLESS_ROOT = Path(__file__).resolve().parents[2] / 'serverless'

# Scopes que `destroy --stage` sin `--lambda` borra (los 4 lambdas).
_ALL_LAMBDA_SCOPES = (
    'contact-form',
    'tracking-pixel',
    'stream-processor',
    'db',
)


def _ensure_tool(tool: str, install_hint: str) -> None:
    """Verifica que `tool` esta en el PATH; aborta con hint si falta."""
    if shutil.which(tool) is None:
        _err(f'{tool} no esta instalado')
        print(_c(YELLOW, f'  {install_hint}'))
        raise SystemExit(1)


def _require_lambda_controller(flags: dict[str, Any]) -> ResolvedLambda:
    """Resuelve el lambda y exige que sea modo lambda-controller.

    Raises
    ------
    SystemExit
        Si no se paso `--lambda`/`--path`/`--module` (modo legacy no
        aplica aqui).
    """
    resolved = resolve_lambda(flags)
    if not resolved.is_lambda_controller:
        _err(
            'Este comando requiere --lambda=<nombre> o --path=<dir> de un '
            'lambda-controller (directorio con manifest.yaml).',
        )
        raise SystemExit(2)
    return resolved


def _run(cmd: list[str], *, cwd: Path) -> int:
    """Ejecuta un comando, imprime la invocacion, devuelve exit code."""
    print(_c(CYAN, f'$ cd {cwd} && {" ".join(cmd)}'))

    result = subprocess.run(cmd, cwd=cwd, check=False)  # noqa: S603
    return result.returncode


# ---------------------------------------------------------------------------
# run: ejecucion local (RIE / directo) | aws lambda invoke (stage deployado)
# ---------------------------------------------------------------------------


def cmd_run(flags: dict[str, Any]) -> int:
    """Ejecuta un lambda. El `--stage` decide el mecanismo.

    `--stage=local` -> ejecucion local con el Runtime Interface Emulator
    (`--runtime-mode=rie`, default) o importando el handler en el proceso
    (`--runtime-mode=direct`). `--stage=dev|stage|prod` -> `aws lambda
    invoke` contra la funcion `portfolio-<name>-<stage>` ya deployada.
    """
    stage = flags.get('stage', 'local')
    if stage == 'local':
        return _run_local(flags)
    return _invoke_remote(flags)


def _run_local(flags: dict[str, Any]) -> int:
    """Ejecuta el lambda en local sin SAM (RIE o modo directo)."""
    resolved = _require_lambda_controller(flags)

    mode_raw = str(flags.get('runtime_mode', 'rie'))
    try:
        mode = RuntimeMode(mode_raw)
    except ValueError:
        _err(f'--runtime-mode invalido: {mode_raw!r}. Validos: rie | direct.')
        return 1

    event = flags.get('event')
    event_path: Path | None = None
    if event:
        event_path = (resolved.root / event).resolve()

    try:
        return local_runtime.run_local(
            resolved,
            event_path=event_path,
            mode=mode,
        )
    except VendoringError as exc:
        _err(str(exc))
        return 1


# ---------------------------------------------------------------------------
# deploy: provisioner + estado local (sin SAM)
# ---------------------------------------------------------------------------


def cmd_deploy_lambda(flags: dict[str, Any]) -> int:
    """Deploya un lambda-controller a un stage con AWS CLI directo.

    devtools renderiza el manifiesto (`provisioner.render`), arma el
    artefacto (`build.zip`) con uv, decide la accion comparando el estado
    local (`state.diff`) y provisiona los recursos AWS necesarios.

    Antes del provisioner, sincroniza los secretos del catalogo
    (`resources/secrets/`) desde `docker/env/server/.{stage}` a SSM
    Parameter Store (--skip-sync para saltarlo).
    """
    _ensure_tool(
        'uv', 'Instalar: curl -LsSf https://astral.sh/uv/install.sh | sh'
    )
    resolved = _require_lambda_controller(flags)
    stage = flags.get('stage', 'dev')

    if stage == 'local':
        _err('Stage `local` no se deploya — usa `run --stage=local`')
        return 1

    region = str(resolved.manifest.get('region', 'us-east-1'))
    profile = flags.get('aws_profile')
    profile_str = str(profile) if profile else None

    if not flags.get('skip_sync'):
        sync_rc = _sync_secrets_before_deploy(
            resolved=resolved,
            stage=stage,
            profile=profile_str,
            region=region,
        )
        if sync_rc != 0:
            return sync_rc

    rendered = provisioner.render(resolved.manifest, stage=stage)
    previous = state_mod.load_state(rendered.name, stage)

    runtime = str(resolved.manifest['runtime'])
    try:
        with packaged_lambda(resolved.root, runtime=runtime) as packaged:
            _, closure, all_deps = packaged
            print(
                _c(
                    CYAN,
                    f'Artefacto: shared/{{{", ".join(sorted(closure))}}} '
                    f'+ {len(all_deps)} deps',
                ),
            )
            zip_path = zip_build_dir(resolved.root)
            # El hash se calcula sobre el build/ (que ya incluye core/ +
            # shared/ vendorizado), no solo sobre core/. Asi cambios en
            # subpaquetes de shared/ disparan re-deploy. El build dir es
            # determinista — packaging.py respeta el orden de los archivos
            # del cierre de shared.
            from serverless.packaging import build_dir as _build_dir

            new_code_hash = state_mod.code_hash(_build_dir(resolved.root))
            new_config_hash = state_mod.config_hash(
                provisioner.rendered_config(rendered),
            )
            action = state_mod.diff(previous, new_config_hash, new_code_hash)

            if flags.get('dry_run'):
                print(_c(YELLOW, f'[dry-run] accion: {action.name}'))
                return 0

            print(
                _c(
                    YELLOW, f'Deploy de {rendered.function_name}: {action.name}'
                ),
            )
            try:
                new_state = provisioner.provision(
                    rendered,
                    action=action,
                    zip_path=zip_path,
                    previous=previous,
                    profile=profile_str,
                    region=region,
                )
            except AwsError as exc:
                _err(f'Deploy fallo: {exc}')
                partial = getattr(exc, 'partial_state', None)
                if partial is not None:
                    # Se marca como parcial (config_hash sentinel) para que
                    # el siguiente `deploy` re-ejecute el CREATE: registra
                    # los recursos creados sin dar el deploy por completo.
                    state_mod.save_state(
                        replace(
                            partial,
                            config_hash=state_mod.PARTIAL_MARKER,
                            code_hash='',
                        ),
                    )
                    print(
                        _c(
                            YELLOW,
                            '  estado parcial guardado — re-ejecuta `deploy` '
                            'para completar (idempotente)',
                        ),
                    )
                return 1
    except PackagingError as exc:
        _err(str(exc))
        return 1

    state_mod.save_state(replace(new_state, code_hash=new_code_hash))
    print(_c(GREEN, f'OK  {rendered.function_name} -> {action.name}'))
    return 0


def _sync_secrets_before_deploy(
    *,
    resolved: ResolvedLambda,
    stage: str,
    profile: str | None,
    region: str,
) -> int:
    """Sincroniza el catalogo de secretos del stage desde el .env a SSM.

    Solo sincroniza los secretos que el lambda USA (uses.secrets del
    manifest). Asi cada deploy publica solo lo necesario. Hermetico: el
    valor nunca aparece en stdout/stderr.
    """
    from serverless.secrets_catalog import Catalog
    from serverless.secrets_catalog import CatalogError
    from serverless.secrets_sync import SyncAction
    from serverless.secrets_sync import SyncError
    from serverless.secrets_sync import sync_secrets_to_ssm

    used_secrets = (resolved.manifest.get('uses') or {}).get('secrets') or []
    if not used_secrets:
        return 0

    server_env_dir = (
        _PORTFOLIO_SERVERLESS_ROOT.parent / 'docker' / 'env' / 'server'
    )
    env_file = server_env_dir / f'.{stage}'
    example_file = server_env_dir / '.example'
    if not env_file.exists() and not example_file.exists():
        _err(
            f'docker/env/server/.{stage} no existe y tampoco hay '
            'docker/env/server/.example para resolver via os.environ.',
        )
        return 1

    try:
        catalog = Catalog.load()
        # `example_file` habilita el fallback: si `env_file` no existe
        # (modo CI), las keys se resuelven desde `os.environ` usando el
        # `.example` como schema canonico. GitHub Actions inyecta cada
        # key como Environment Secret.
        results = sync_secrets_to_ssm(
            stage=stage,
            env_file=env_file,
            catalog=catalog,
            example_file=example_file,
            profile=profile,
            region=region,
            only=tuple(used_secrets),
        )
    except (CatalogError, SyncError) as exc:
        _err(f'secrets-sync fallo: {exc}')
        return 1

    push = sum(1 for r in results if r.action == SyncAction.PUSH)
    skip = sum(1 for r in results if r.action == SyncAction.SKIP)
    miss = sum(1 for r in results if r.action == SyncAction.MISSING)

    print(_c(CYAN, f'[secrets-sync] catalogo: {len(results)} entradas'))
    for r in results:
        # NUNCA el valor. Solo nombre, accion, path, hash truncado.
        marker = (
            GREEN
            if r.action == SyncAction.SKIP
            else YELLOW
            if r.action == SyncAction.PUSH
            else CYAN
        )
        print(
            f'  {_c(marker, r.action.value):<6} {r.name:<25} '
            f'{r.path:<45} hash={r.hash_short}',
        )
    print(_c(GREEN, f'  -> {push} PUSH, {skip} SKIP, {miss} MISSING'))
    return 0


# ---------------------------------------------------------------------------
# destroy: borra los recursos de un stage (lambda(s) + infra)
# ---------------------------------------------------------------------------


def cmd_destroy(flags: dict[str, Any]) -> int:
    """Borra los recursos de un stage. Operacion DESTRUCTIVA.

    Sin `--lambda`: borra los 4 lambdas + la infra del stage. Con
    `--lambda=<x>`: borra solo ese lambda. Requiere `--yes` (confirmacion
    no interactiva); sin `--yes` NO borra nada.
    """
    stage = flags.get('stage', 'dev')
    if stage == 'local':
        _err('Stage `local` no tiene recursos AWS que destruir.')
        return 1

    region = 'us-east-1'
    profile = flags.get('aws_profile')
    profile_str = str(profile) if profile else None
    lambda_name = flags.get('lambda')

    if not flags.get('yes'):
        target = (
            f'el lambda {lambda_name!r}'
            if lambda_name
            else f'TODOS los lambdas + infra del stage {stage!r}'
        )
        _err(f'destroy es destructivo: borraria {target}.')
        print(_c(YELLOW, '  Agrega --yes para confirmar.'))
        return 2

    if lambda_name:
        resolved = _require_lambda_controller(flags)
        scopes = [provisioner.render(resolved.manifest, stage=stage).name]
    else:
        scopes = list(_ALL_LAMBDA_SCOPES)

    rc = 0
    for scope in scopes:
        st = state_mod.load_state(scope, stage)
        if st is None:
            print(_c(YELLOW, f'[skip] {scope}-{stage}: sin estado local'))
            continue
        print(_c(YELLOW, f'Destruyendo {scope}-{stage}...'))
        try:
            provisioner.deprovision(st, profile=profile_str, region=region)
        except AwsError as exc:
            _err(f'destroy de {scope} fallo: {exc}')
            rc = 1

    if not lambda_name:
        # destroy completo: tambien borra la infra y limpia el estado.
        from serverless.infra_provision import deprovision_infra

        print(_c(YELLOW, f'Destruyendo infra del stage {stage}...'))
        try:
            deprovision_infra(stage=stage, profile=profile_str, region=region)
        except AwsError as exc:
            _err(f'destroy de infra fallo: {exc}')
            rc = 1
        removed = state_mod.clear_state(stage)
        print(_c(GREEN, f'OK  estado local limpiado ({len(removed)} archivos)'))

    return rc


# ---------------------------------------------------------------------------
# status: estado local vs AWS
# ---------------------------------------------------------------------------


def cmd_status(flags: dict[str, Any]) -> int:
    """Compara el estado local con AWS, por scope.

    Sin `--lambda`: reporta los 4 lambdas. Con `--lambda=<x>`: solo ese.
    Para cada scope informa si hay estado local y si la funcion existe en
    AWS (`aws lambda get-function`).
    """
    from serverless.aws_cli import aws_resource_exists

    stage = flags.get('stage', 'dev')
    profile = flags.get('aws_profile')
    profile_str = str(profile) if profile else None
    lambda_name = flags.get('lambda')

    if lambda_name:
        resolved = _require_lambda_controller(flags)
        scopes = [provisioner.render(resolved.manifest, stage=stage).name]
    else:
        scopes = list(_ALL_LAMBDA_SCOPES)

    print(_c(CYAN, f'Estado del backend serverless (stage {stage}):'))
    for scope in scopes:
        st = state_mod.load_state(scope, stage)
        function_name = f'portfolio-{scope}-{stage}'
        in_aws = aws_resource_exists(
            'lambda',
            ['get-function', '--function-name', function_name],
            profile=profile_str,
        )
        if st is None and not in_aws:
            mark = _c(YELLOW, 'sin deployar')
        elif st is not None and in_aws:
            mark = _c(GREEN, 'OK (local + AWS)')
        elif st is None:
            mark = _c(YELLOW, 'en AWS pero sin estado local (drift)')
        else:
            mark = _c(YELLOW, 'estado local pero ausente en AWS (drift)')
        print(f'  {scope:<20} {mark}')
    return 0


# ---------------------------------------------------------------------------
# _invoke_remote: aws lambda invoke contra un stage deployado
# ---------------------------------------------------------------------------


def _invoke_remote(flags: dict[str, Any]) -> int:
    """Invoca el lambda YA deployado en un stage (aws lambda invoke)."""
    _ensure_tool(
        'aws',
        'Instalar: brew install awscli  o  pip install awscli',
    )
    resolved = _require_lambda_controller(flags)
    stage = flags.get('stage', 'dev')

    # El FunctionName fisico lleva el prefijo `portfolio-` y el sufijo de
    # stage (ver provisioner.render).
    rendered = provisioner.render(resolved.manifest, stage=stage)
    function_name = rendered.function_name
    region = str(resolved.manifest.get('region', 'us-east-1'))

    args = [
        'aws',
        'lambda',
        'invoke',
        '--function-name',
        function_name,
        '--region',
        region,
        '--cli-binary-format',
        'raw-in-base64-out',
    ]
    aws_profile = flags.get('aws_profile')
    if aws_profile:
        args += ['--profile', str(aws_profile)]

    event = flags.get('event')
    if event:
        event_path = (resolved.root / event).resolve()
        if not event_path.is_file():
            _err(f'Event JSON no existe: {event_path}')
            return 1
        args.extend(['--payload', f'file://{event_path}'])

    out_path = resolved.root / '.invoke' / 'invoke-response.json'
    out_path.parent.mkdir(parents=True, exist_ok=True)
    args.append(str(out_path))

    rc = _run(args, cwd=resolved.root)
    if rc == 0 and out_path.is_file():
        print(_c(GREEN, f'Respuesta de {function_name}:'))
        try:
            payload = json.loads(out_path.read_text(encoding='utf-8'))
            print(json.dumps(payload, indent=2, default=str))
        except (json.JSONDecodeError, OSError):
            print(out_path.read_text(encoding='utf-8'))
    return rc


# ---------------------------------------------------------------------------
# Tests dinamicos (lambda-controller con tests/unit y tests/integration)
# ---------------------------------------------------------------------------


def _resolve_pytest_python(resolved: ResolvedLambda) -> str:
    """Resuelve el interprete Python para correr los tests del lambda.

    Cada lambda tiene su `.venv` AISLADO (el workspace uv compartido se
    elimino, plan serverless-lambda-independence). `venv.ensure_lambda_venv`
    lo prepara con `uv sync` (deps del lambda + grupo dev) y `uv pip
    install` de las deps externas del cierre de `shared/` que el lambda
    usa — asi el `.venv` refleja EXACTAMENTE lo que el lambda necesita,
    fiel a la realidad de AWS.

    Si `uv` no esta disponible cae a `python3` del PATH (fallback; puede
    no tener las deps — los tests fallarian con ImportError, lo que es un
    diagnostico claro).
    """
    from serverless.venv import VenvError
    from serverless.venv import ensure_lambda_venv

    try:
        return str(ensure_lambda_venv(resolved.root))
    except VenvError as exc:
        _err(f'No se pudo preparar el .venv del lambda: {exc}')
        print(_c(YELLOW, '  [WARN] cae a python3 del PATH'))
        return 'python3'


# El directorio del backend serverless y la libreria comun.
_SERVERLESS_DIR = Path(__file__).resolve().parents[2] / 'serverless'
_SHARED_DIR = _SERVERLESS_DIR / 'lambda' / 'shared'


def _pytest_extra(flags: dict[str, Any]) -> list[str]:
    """Flags pytest comunes (verbose / quiet) derivados de los flags CLI."""
    extra: list[str] = []
    if flags.get('verbose') or flags.get('v'):
        extra.append('-v')
    if flags.get('quiet'):
        extra.append('-q')
    return extra


def _run_lambda_tests(
    resolved: ResolvedLambda, test_type: str, flags: dict[str, Any]
) -> int:
    """Corre los tests de un lambda-controller para el `--type` indicado.

    `unit` / `integration` corren `tests/<type>`. `coverage` corre
    `tests/unit` con `--cov=core` + `--cov-fail-under`.
    """
    subdir = 'unit' if test_type == 'coverage' else test_type
    tests_dir = resolved.root / 'tests' / subdir
    if not tests_dir.is_dir():
        if test_type == 'integration':
            print(
                _c(YELLOW, f'[skip] {resolved.root.name}: sin tests/{subdir}')
            )
            return 0
        _err(f'No existe {tests_dir}')
        print(
            f'  Un lambda-controller debe traer tests/{subdir}/ '
            f'(ver el formato lambda-controller).',
        )
        return 1

    python = _resolve_pytest_python(resolved)
    args = [python, '-m', 'pytest', f'tests/{subdir}', '-o', 'addopts=']
    args.extend(_pytest_extra(flags))
    if test_type == 'coverage':
        threshold = flags.get('coverage_threshold', 80)
        # --cov-config apunta al pyproject del PROPIO lambda: su
        # [tool.coverage.run] omite core/shared/ (la libreria comun
        # vendorizada) para que el coverage mida solo su codigo. Cada
        # lambda tiene su config de tooling (plan
        # serverless-lambda-independence).
        cov_config = resolved.root / 'pyproject.toml'
        args.extend(
            [
                '--cov=core',
                f'--cov-config={cov_config}',
                '--cov-report=term-missing',
                f'--cov-fail-under={threshold}',
            ]
        )

    # Vendoriza serverless/lambda/shared/ en core/shared/ para que los tests
    # resuelvan `import shared...` igual que en el artefacto desplegado.
    from serverless.vendoring import vendored_shared

    try:
        with vendored_shared(resolved.root):
            return _run(args, cwd=resolved.root)
    except VendoringError as exc:
        _err(str(exc))
        return 1


def _run_shared_tests(
    test_type: str, flags: dict[str, Any], *, subpackage: str | None
) -> int:
    """Corre los tests de la libreria comun (`serverless/lambda/shared/tests/`).

    El cwd es `serverless/lambda/` (NO `shared/`): asi el directorio que
    pytest agrega al `sys.path` es `lambda/`, `import shared...` resuelve
    y el subpaquete `shared/http/` no tapa el `http` del stdlib.

    `subpackage` filtra a un subpaquete (`core`, `aws`, `http`, `cache`,
    `db`, `dynamodb`, `rate_limit`): corre `tests/unit/shared/<subpackage>/`
    y acota el `--cov` a ese subpaquete. Si el subpaquete no tiene subdir
    de tests, cae a `-k <subpackage>` (el `--cov` sigue midiendo todo).
    """
    tests_root = _SHARED_DIR / 'tests'
    type_dir = tests_root / ('unit' if test_type == 'coverage' else test_type)
    if not type_dir.is_dir():
        if test_type == 'integration':
            print(_c(YELLOW, '[skip] shared: sin tests de integration'))
            return 0
        _err(f'No existe {type_dir}')
        return 1

    target = 'unit' if test_type == 'coverage' else test_type
    # La suite centralizada de shared/ corre con el `.venv` de
    # `serverless/`: `venv.ensure_shared_venv` lo sincroniza (uv sync del
    # grupo dev del `serverless/pyproject.toml`).
    from serverless.venv import VenvError
    from serverless.venv import ensure_shared_venv

    try:
        python = str(ensure_shared_venv(_PORTFOLIO_SERVERLESS_ROOT))
    except VenvError as exc:
        _err(f'No se pudo preparar el .venv de shared/: {exc}')
        print(_c(YELLOW, '  [WARN] cae a python3 del PATH'))
        python = 'python3'
    # cwd = serverless/lambda/, target relativo: shared/tests/<type>.
    test_path = f'shared/tests/{target}'
    args = [python, '-m', 'pytest', test_path, '-o', 'addopts=']
    args.extend(_pytest_extra(flags))

    # Por defecto el coverage mide toda la libreria comun; con --shared=X
    # se acota al subpaquete (mide solo lo que los tests filtrados cubren).
    cov_target = 'shared'
    filtered_by_dir = False
    if subpackage:
        subpkg_dir = type_dir / 'shared' / subpackage
        if subpkg_dir.is_dir():
            args[3] = f'{test_path}/shared/{subpackage}'
            cov_target = f'shared/{subpackage}'
            filtered_by_dir = True
        else:
            args.extend(['-k', subpackage])

    if test_type == 'coverage':
        threshold = flags.get('coverage_threshold', 80)
        cov_config = _SERVERLESS_DIR / 'pyproject.toml'
        args.extend(
            [
                f'--cov={cov_target}',
                f'--cov-config={cov_config}',
                '--cov-report=term-missing',
                f'--cov-fail-under={threshold}',
            ]
        )
        if subpackage and not filtered_by_dir:
            # subpaquete filtrado por -k (no por dir): el --cov igual mide
            # toda la libreria, no se puede acotar mas sin el subdir.
            print(
                _c(
                    YELLOW,
                    f'[nota] --shared={subpackage} sin subdir propio: '
                    'el coverage mide toda la libreria comun.',
                )
            )

    return _run(args, cwd=_SHARED_DIR.parent)


def cmd_tests(flags: dict[str, Any]) -> int:
    """Corre tests del backend: `--type` + target.

    `--type=unit|integration|coverage` (obligatorio, validado en flags).
    Target, por precedencia:
      - `--lambda=<nombre>` / `--path=<dir>`: tests de ese lambda.
      - `--shared` / `--shared=<subpaquete>`: tests de la libreria comun.
      - sin target: corre TODO (los 4 lambdas + shared).
    """
    test_type = flags.get('type', 'unit')

    has_lambda_target = bool(
        flags.get('lambda') or flags.get('path') or flags.get('module')
    )
    shared_target = flags.get('shared')

    if has_lambda_target:
        resolved = _require_lambda_controller(flags)
        return _run_lambda_tests(resolved, test_type, flags)

    if shared_target is not None:
        # --shared (bool True) = toda la libreria; --shared=aws = subpaquete.
        subpackage = shared_target if isinstance(shared_target, str) else None
        return _run_shared_tests(test_type, flags, subpackage=subpackage)

    # Sin target: corre todo (los 4 lambdas + shared).
    rc = 0
    for name in available_lambdas():
        print(_c(CYAN, f'== tests {test_type} :: {name} =='))
        resolved = resolve_lambda({'lambda': name})
        rc = _run_lambda_tests(resolved, test_type, flags) or rc
    print(_c(CYAN, f'== tests {test_type} :: shared =='))
    return _run_shared_tests(test_type, flags, subpackage=None) or rc
