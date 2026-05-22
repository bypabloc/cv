# 07 — Fase 5: integracion del CLI

> [Anterior: 06](06-fase-4-run-local.md) | [README](README.md) | [Siguiente: 08](08-fase-6-eliminar-sam.md)

Reconecta el CLI a los modulos nuevos (`provisioner`, `infra_provision`,
`local_runtime`, `state`). Es la fase que NO se paraleliza: toca
`main.py` / `flags.py` / `help.py`, los tres archivos de la grilla de
comandos. Depende de las Fases 1-4.

## Objetivo

1. `lambda_controller.py` — `cmd_deploy_lambda` y `cmd_run` usan
   `provisioner` + `state` + `local_runtime` en vez de SAM. Se elimina
   `cmd_sam_generate`.
2. `main.py` — `COMMAND_REGISTRY`: quitar `sam-generate`, renombrar
   `deploy-infra` a `provision-infra`, agregar `destroy` y `status`.
3. `flags.py` — quitar flags de SAM (`guided`, `debug`), agregar
   `runtime-mode`, `yes` (para `destroy`).
4. `help.py` — actualizar los textos.

## Archivos afectados

### Modificar

- `devtools/serverless/lambda_controller.py` — el cambio mas grande:
  - `cmd_deploy_lambda`: `render` -> `package` (build.zip) ->
    `state.diff` -> `provision` -> `state.save`. Sin `sam`.
  - `cmd_run`: `--stage=local` -> `local_runtime.run_local`; resto
    sigue en `_invoke_remote` (ya era AWS CLI).
  - ELIMINAR `cmd_sam_generate` y `_regenerate_sam`.
  - ELIMINAR los `_ensure_tool('sam', ...)`.
  - AGREGAR `cmd_destroy` (borra un lambda o todos + infra de un stage)
    y `cmd_status` (estado local vs `describe-*`).
- `devtools/serverless/main.py` — `COMMAND_REGISTRY`:
  - quitar `'sam-generate'`.
  - `'deploy-infra'` -> `'provision-infra'` apuntando a
    `infra_provision.cmd_provision_infra`.
  - agregar `'destroy'` -> `cmd_destroy`.
  - agregar `'status'` -> `cmd_status`.
  - actualizar el import de `infra_deploy` a `infra_provision`.
- `devtools/serverless/flags.py`:
  - quitar `'sam-generate'` de los comandos validos y de sus mapeos.
  - quitar `'guided'` y `'debug'` del set de flags.
  - agregar `'runtime-mode'` (choices `rie|direct`, default `rie`).
  - agregar `'yes'` (bool, confirmacion no interactiva de `destroy`).
  - agregar comandos `'provision-infra'`, `'destroy'`, `'status'` con
    sus flags permitidas.
  - actualizar `_LOCAL_STAGE_DESC` / comentarios que mencionan SAM
    ([flags.py:17-23](../../../devtools/serverless/flags.py#L17-L23)).
- `devtools/serverless/help.py` — textos de ayuda de cada comando, quitar
  toda mencion a SAM.

## Comandos del CLI tras la fase

```text
serverless init
serverless clean
serverless lint | lint-fix | format | typecheck
serverless tests --type=unit|integration|coverage [--lambda|--shared]
serverless run --lambda=<x> --stage=local|dev|stage|prod [--event=...] [--runtime-mode=rie|direct]
serverless deploy --lambda=<x> --stage=dev|stage|prod [--aws-profile=...] [--dry-run]
serverless provision-infra --stage=dev|stage|prod [--aws-profile=...] [--dry-run]
serverless destroy --stage=dev|stage|prod [--lambda=<x>] --yes [--aws-profile=...]
serverless status --stage=dev|stage|prod [--lambda=<x>] [--aws-profile=...]
serverless setup-ssm | rotate-secret | verify-ses-dns | request-ses-prod
serverless metrics | alarms
serverless rate-limit ...
serverless help
```

`destroy` sin `--lambda` borra TODO el stage (los 4 lambdas + infra).
Con `--lambda` borra solo ese lambda.

## `cmd_deploy_lambda` — pseudocodigo

```python
def cmd_deploy_lambda(flags):
    _ensure_tool('uv', ...)            # ya NO _ensure_tool('sam', ...)
    resolved = _require_lambda_controller(flags)
    stage = flags['stage']
    region = resolved.manifest.get('region', 'us-east-1')
    profile = flags.get('aws_profile')

    rendered = provisioner.render(resolved.manifest, stage=stage)
    previous = state.load_state(rendered.name, stage)

    with packaged_lambda(resolved.root, runtime=rendered.runtime) as pkg:
        build_dir, closure, deps = pkg
        zip_path = packaging.zip_build_dir(build_dir)
        new_code_hash = state.code_hash(resolved.root / 'core')
        new_config_hash = state.config_hash(asdict(rendered))
        action = state.diff(previous, new_config_hash, new_code_hash)

        if flags.get('dry_run'):
            print(f'[dry-run] accion: {action.name}')
            return 0

        new_state = provisioner.provision(
            rendered, action=action, zip_path=zip_path,
            previous=previous, profile=profile, region=region,
        )
    state.save_state(new_state)
    print(f'OK  {rendered.function_name} -> {action.name}')
    return 0
```

## Criterios de aceptacion

- **AC-5.1**: When `serverless help`, Then se listan `provision-infra`,
  `destroy`, `status` y NO aparece `sam-generate`.
- **AC-5.2**: Given `serverless deploy --lambda=<x> --stage=dev
  --dry-run`, When se ejecuta, Then imprime la accion del diff
  (`CREATE`/`UPDATE_*`/`NOOP`) sin tocar AWS.
- **AC-5.3**: Given `serverless destroy --stage=dev` sin `--yes`, When
  se ejecuta, Then NO borra nada y pide confirmacion.
- **AC-5.4**: Given `serverless destroy --stage=dev --yes`, When se
  ejecuta, Then borra los 4 lambdas + infra y limpia el `.state`.
- **AC-5.5**: Given `serverless status --stage=dev`, When se ejecuta,
  Then reporta, por scope, si el estado local coincide con AWS.
- **AC-5.6**: When se busca `sam` en `devtools/serverless/flags.py`,
  `main.py`, `help.py`, `lambda_controller.py`, Then no hay resultados.
- **AC-5.7**: Given un flag invalido para un comando (ej. `--guided`),
  When se ejecuta, Then el CLI lo rechaza con un error claro.

## Tests requeridos

`devtools/tests/unit/src/serverless/test_flags.py` (ampliar el existente):

- `test_flags_rejects_removed_sam_generate_command` [AC-5.1]
- `test_flags_rejects_guided_flag` [AC-5.7]
- `test_flags_destroy_requires_yes_or_prompts` [AC-5.3]
- `test_flags_runtime_mode_choices`

`devtools/tests/unit/src/serverless/test_lambda_controller.py` (nuevo o ampliar):

- `test_cmd_deploy_dry_run_prints_action` [AC-5.2] — `provisioner` y
  `packaging` mockeados.
- `test_cmd_destroy_without_yes_does_not_delete` [AC-5.3]
- `test_cmd_destroy_with_yes_calls_deprovision` [AC-5.4]
- `test_cmd_status_compares_local_vs_aws` [AC-5.5]

## Verificacion incremental con comandos devtools

Esta fase conecta el CLI nuevo: `deploy`, `destroy`, `status`,
`provision-infra` y `run` ya operan sin SAM. Es la primera fase donde el
flujo completo es ejecutable end-to-end.

### Sin AWS (OBLIGATORIO en esta fase)

```bash
python devtools/run.py serverless help               # grilla nueva, sin sam-generate
python devtools/run.py serverless tests --type=unit   # suite completa verde
python devtools/run.py serverless deploy --lambda=contact-form --stage=dev --dry-run
python devtools/run.py serverless provision-infra --stage=dev --dry-run
python devtools/run.py serverless run --lambda=contact-form --stage=local \
  --event=events/create.json --runtime-mode=direct
python devtools/run.py serverless destroy --stage=dev      # sin --yes: NO borra, pide confirmacion
```

### Con AWS dev (OBLIGATORIO en esta fase si hay acceso a la cuenta)

Esta fase NO difiere la verificacion E2E a la Fase 8: el flujo completo
debe ejecutarse aqui. La Fase 8 solo lo re-corre como cierre.

```bash
export AWS_PROFILE=tfs-dev
# 1. destruir lo que dejo CloudFormation (ver 08-fase-6)
# 2. aprovisionar infra
python devtools/run.py serverless provision-infra --stage=dev --aws-profile=tfs-dev
# 3. deployar los 4 lambdas (CREATE)
for L in contact-form tracking-pixel stream-processor db; do
  python devtools/run.py serverless deploy --lambda=$L --stage=dev --aws-profile=tfs-dev
done
# 4. invocar cada uno
python devtools/run.py serverless run --lambda=contact-form --stage=dev \
  --event=events/create.json --aws-profile=tfs-dev
# 5. idempotencia: re-deploy sin cambios -> NOOP
python devtools/run.py serverless deploy --lambda=contact-form --stage=dev --aws-profile=tfs-dev
# 6. status: estado local vs AWS
python devtools/run.py serverless status --stage=dev --aws-profile=tfs-dev
# 7. ciclo destruir/recrear
python devtools/run.py serverless destroy --stage=dev --yes --aws-profile=tfs-dev
python devtools/run.py serverless provision-infra --stage=dev --aws-profile=tfs-dev
```

Regla de cierre: los comandos sin AWS son obligatorios y deben pasar
todos. El bloque con AWS se ejecuta si hay acceso a dev; si no, se
documenta el resultado pendiente en el PR y se corre en la Fase 8. NO se
declara la fase lista mientras un comando sin AWS falle.

## Verificacion (Definition of Done de la fase)

```bash
devtools/.venv/bin/python -m pytest devtools/tests/unit/src/serverless/ -v
python devtools/run.py docker lint --module=devtools
devtools/.venv/bin/python -m mypy devtools/serverless/
python devtools/run.py serverless help          # lista comandos nuevos
rg "\bsam\b" devtools/serverless/                # 0 resultados
# comandos devtools sin AWS (ver bloque incremental arriba):
python devtools/run.py serverless deploy --lambda=contact-form --stage=dev --dry-run
python devtools/run.py serverless provision-infra --stage=dev --dry-run
python devtools/run.py serverless tests --type=unit
```

- [ ] AC-5.1..AC-5.7 cubiertos
- [ ] La suite completa `devtools/tests/unit/src/serverless/` verde
- [ ] `serverless help` muestra la grilla nueva
- [ ] Cero menciones a `sam` en `devtools/serverless/`
- [ ] Ruff + mypy sin errores
- [ ] Comandos sin AWS (`deploy --dry-run`, `provision-infra --dry-run`,
      `run-local`, `destroy` sin `--yes`) pasan todos
- [ ] Flujo E2E con AWS dev verificado (o documentado pendiente en el PR)

---

[Anterior: 06](06-fase-4-run-local.md) | [README](README.md) | [Siguiente: 08](08-fase-6-eliminar-sam.md)
