# 08 — Fase F: eliminacion de los sistemas viejos

[<- 07 modulo app](07-fase-modulo-app.md) | [Siguiente: 09 rule/skill ->](09-fase-rule-skill.md)

> SOLO se ejecuta cuando A-E estan verdes (los 3 modulos de `e2e` pasan). El
> orden importa: no borrar nada hasta que `e2e` cubra todo. AC-12.

## F.1 — Eliminar `devtools/api_e2e/`

```bash
git rm -r devtools/api_e2e/
git rm -r devtools/tests/unit/src/api_e2e/   # tests unit del harness viejo
```

Los tests unit que valgan (flags, config, reporter, runner) se REUBICAN
antes en `devtools/tests/unit/src/e2e/` (comando) +
`devtools/tests/unit/src/e2e_shared/` (shared portado) — ver fase 10. Esta
fase asume que esa reubicacion ya ocurrio en A/B/C.

## F.2 — Eliminar `tests/feature/`

```bash
git rm -r tests/feature/
```

Incluye specs TS, `package.json`, `playwright.config.ts`, `pnpm-lock.yaml`,
`tsconfig.json`, `node_modules` (gitignored), `helpers/`, `fixtures/`. TODO
su contenido funcional ya esta portado a `tests/{admin,app,shared}/`.

## F.3 — Eliminar el modulo `feature` de `test_runner`

| Archivo | Accion |
|---------|--------|
| `devtools/test_runner/feature.py` | `git rm` (todo el modulo Playwright) |
| `devtools/test_runner/flags.py` | quitar `feature` de `MODULE_TEST_TYPES`; rechazar `--module=feature`/`--type=feature` con mensaje de migracion (patron ya usado para `e2e`/`tests`): "usa `python devtools/run.py e2e --module=app`" |
| `devtools/test_runner/full_suites.py` | quitar el branch `if module == 'feature'` + el import `run_feature` |
| `devtools/test_runner/README.md` | quitar la doc de `--module=feature` |
| `devtools/tests/unit/src/test_runner/flags.py` | actualizar tests que esperaban `feature` valido -> ahora rechazado |

`server` feature (pytest -m feature en `devtools/shared/{commands,classification}.py`)
es OTRO concepto (tests del backend serverless en `serverless/.../tests/`),
NO el Playwright del portfolio. CONFIRMAR que no se rompe: el `feature` de
`commands.py`/`classification.py` apunta a `tests/feature/` del backend
(server), distinto de la carpeta `tests/feature/` raiz que borramos. Si
apunta a la raiz, ajustar. (Verificar en impl: el portfolio NO tiene
`server/tests/feature/`; ese codigo es heredado del template.)

## F.4 — Eliminar el container Docker `feature`

| Archivo | Accion |
|---------|--------|
| `docker/dockerfiles/local/feature/Dockerfile` | `git rm` |
| `docker/dockerfiles/test/feature/Dockerfile` | `git rm` |
| `docker/docker-compose/{local,dev,test,prod}.yml` | quitar el servicio `feature` (profile feature) |
| `docker/scripts/feature-entrypoint.sh` | `git rm` (reemplazado por el entrypoint `e2e`) |

> El servicio/dockerfile `e2e` (fase B) reemplaza al `feature`. Verificar
> que ningun otro servicio dependa de `feature`.

## F.5 — Actualizar el pre-push hook

`.git-hooks/pre-push` (lineas ~310-372) + `.git-hooks/config.json`:

- `step_feature_tests` -> renombrar a `step_e2e` (o mantener nombre, cambiar
  el comando): hoy corre `test_runner --module=feature --type=feature
  --env=local` levantando el stack Docker LOCAL. AHORA debe correr `e2e`
  contra dev (o saltar si no hay SSO/credenciales).
- DECISION (confirmar en impl): el pre-push corre contra DESPLEGADO (dev),
  que requiere SSO. Si el dev no tiene SSO activo localmente, el step hace
  skip `[OMITIDO]` (como hoy hace skip si no hay Docker). Alternativa: el
  pre-push solo corre `--module=app` (no requiere auth) y deja `api`/`admin`
  para el push manual / CI. **Preferir**: pre-push corre `e2e --module=app
  --env=dev` (rapido, sin auth); `api`/`admin` se corren manualmente antes
  del PR (son mas lentos y mutan dev). Documentar la eleccion en config.json.
- `config.json`: actualizar `feature_tests` -> `e2e_tests` con descripcion
  nueva. `SKIP_STEPS="e2e_tests"` para saltar.

## F.6 — Actualizar CI (si referencia feature/e2e)

`.github/workflows/ci.yml` — el grep inicial no mostro `feature`/`e2e`
en ci.yml (el job e2e-tests con Docker puede estar en otro workflow o haber
sido removido). VERIFICAR en impl:
- Si hay un job `e2e-tests` que levanta Docker + corre Playwright -> migrar
  o eliminar (los E2E contra desplegado no encajan en el CI de PR que no
  tiene SSO/secrets para dev). DECISION: los E2E pesados (api/admin contra
  dev) NO corren en el CI de PR (mutan dev, requieren secretos). Quedan
  como gate manual pre-PR + opcional en un workflow dedicado post-deploy.
- Documentar en `.claude/rules/ci-cd-pipeline.md` que `e2e` es manual/opt-in.

## F.7 — Barrido de referencias residuales

```bash
# Codigo funcional NO debe referenciar los viejos (AC-12)
rg -l "api_e2e" --glob '!docs/specs/**' --glob '!**/__pycache__/**'
rg -l "tests/feature|module=feature|--type=feature|run_feature" \
  --glob '!docs/specs/**' --glob '!**/__pycache__/**'
```

Casos conocidos a actualizar (del barrido inicial):
- `CLAUDE.md` — secciones de comandos/estructura que mencionan `feature`
  y `tests/feature/` -> actualizar a `e2e` + `tests/{api,admin,app,shared}/`.
- `packages/ui/src/components/ContactFormReact.tsx` — referencia `api-e2e`
  en el header de bypass (deuda conocida, ver memory). Revisar si el header
  cambia con la nueva arquitectura; si no, dejar y anotar.
- `serverless/lambda/shared/crypto/{ed25519,bypass_token}.py` — referencian
  `api_e2e` en docstrings/comentarios -> actualizar la mencion a `e2e`.
- `devtools/bypass_token/README.md`, `devtools/weak_assertion/README.md` —
  actualizar menciones.
- `docs/specs/{ai-readiness-2026,b-analytics-api}/` — son planes (algunos
  efimeros). Si son planes ya mergeados que quedaron, no tocar (historicos);
  si estan vivos, actualizar la verificacion E2E para usar `e2e`.

## Verificacion de la fase F

```bash
python devtools/run.py | rg -q "e2e" && echo "e2e registrado"
python devtools/run.py | rg -q "api_e2e" && echo "FAIL: api_e2e sigue" || echo "ok"
python devtools/run.py test_runner --module=feature 2>&1 | rg -q "eliminado|e2e" \
  && echo "feature rechazado con mensaje"
rg -l "api_e2e" --glob '!docs/specs/**' --glob '!**/__pycache__/**' \
  | rg -v "git" || echo "sin referencias vivas a api_e2e"
python devtools/run.py test_runner --module=devtools --type=unit  # unit verde
```

## Done de la fase F

- [ ] `devtools/api_e2e/` eliminado.
- [ ] `tests/feature/` eliminado.
- [ ] modulo `feature` de `test_runner` eliminado/rechazado con migracion.
- [ ] container/dockerfiles/entrypoint `feature` eliminados.
- [ ] pre-push hook actualizado a `e2e` (con la politica de skip decidida).
- [ ] CI revisado (E2E manual/opt-in documentado).
- [ ] `rg` sin referencias vivas a `api_e2e`/`tests/feature`/`module=feature`.
- [ ] `test_runner --module=devtools --type=unit` verde tras los cambios.

[<- 07 modulo app](07-fase-modulo-app.md) | [Siguiente: 09 rule/skill ->](09-fase-rule-skill.md)
