# 16 — Seccion 12: Validacion y Definition of Done

[<- 15 verificacion e2e](15-verificacion-e2e.md) | [README ->](README.md)

## Pre-implementacion

- [ ] Todos los AC (AC-1..AC-13) numerados y referenciados por tests/tareas.
- [ ] Rama de trabajo `feature/e2e-refactor` creada desde `dev` (NO trabajar
      en `dev` protegida).
- [ ] `devtools/.venv` con Python 3.14 operativo (`python devtools/run.py
      --help` bootstrapea uv).
- [ ] SSO `tfs-dev` activo + clave privada Ed25519 en `docker/env/dev-cli/.dev`
      disponibles (para verificar api/admin contra dev).
- [ ] Inventario de specs TS leido (alimenta el portado D/E).
- [ ] No hay otro plan E2E en curso que colisione.

## Definition of Done

### Funcional
- [ ] `python devtools/run.py e2e --module=api --env=dev` PASS (AC-1).
- [ ] `python devtools/run.py e2e --module=admin --env=dev` PASS, flujos
      reales end-to-end (login/logout/forms/MFA) (AC-2).
- [ ] `python devtools/run.py e2e --module=app --env=dev` PASS, 6 apps,
      screenshots generados (AC-3).
- [ ] `python devtools/run.py e2e --env=dev` corre los 3 en orden (AC-4).
- [ ] Validacion de flags: `--module=foo` y `--env=prod` -> error (AC-5).
- [ ] `api`/`admin` fallan duro sin SSO/clave; `app` corre igual (AC-6).
- [ ] Container `e2e` con Python 3.14 + playwright browsers (AC-7).
- [ ] `tests/shared/` portador unico (db/secrets/http/browser/reporter) (AC-8).
- [ ] Hermetismo: ningun secreto a stdout (AC-9).
- [ ] Cleanup de datos sinteticos en Neon + blacklist (AC-10).
- [ ] Reporte de tiempos cold/warm por caso (AC-11).

### Limpieza
- [ ] `api_e2e`, `tests/feature/`, `test_runner --module=feature`,
      container/dockerfiles `feature` ELIMINADOS (AC-12).
- [ ] `rg` sin referencias vivas a los viejos (codigo funcional).
- [ ] pre-push hook + CI actualizados a `e2e` (politica de skip documentada).
- [ ] CLAUDE.md refleja `e2e` + `tests/{api,admin,app,shared}/`.

### Documentacion Claude
- [ ] `.claude/rules/e2e-testing.md` creada.
- [ ] `.claude/skills/e2e-testing/SKILL.md` creada y validada `claude -p`
      (5/5 angulos) (AC-13).

### Calidad
- [ ] `python devtools/run.py test_runner --module=devtools --type=unit`
      verde, coverage >=80% per-file en `devtools/e2e/` + shared portado.
- [ ] `devtools/.venv/bin/python -m compileall` sin SyntaxError.
- [ ] `pnpm run lint` + `pnpm run typecheck` + `pnpm run build` verdes (el
      refactor no rompe el frontend).
- [ ] ruff sin errores en `devtools/e2e/` + `tests/`.
- [ ] Cada `.md` del plan < 300 lineas.

### Cierre
- [ ] Bateria seccion 11 (Partes A+B) verde antes del push/PR.
- [ ] Un PR `feature/e2e-refactor -> dev`, merge commit, sin atribucion IA.
- [ ] Ultimo commit elimina `docs/specs/e2e-refactor/` (`git rm -r`).
- [ ] Si una decision de arquitectura debe sobrevivir, ya esta en la rule
      `.claude/rules/e2e-testing.md` (no en la spec efimera).

## Riesgos y mitigaciones

| Riesgo | Mitigacion |
|--------|------------|
| Imagen playwright-python choca con pin 3.14 | Imagen base 3.14 + `playwright install --with-deps`; documentar (fase B) |
| WebKit/CORS contra dev desplegado | Correr chromium por defecto; webkit opcional (como el TS) |
| Multi-tab logout fragil contra desplegado | Degradar a verificar `storage` event (como el TS) |
| Pre-push requiere SSO (no siempre activo) | Pre-push corre solo `--module=app` (sin auth) o skip `[OMITIDO]` |
| `server feature` de classification.py es otro concepto | Confirmar que apunta a `server/tests/feature/`, no a la raiz borrada |
| ContactFormReact referencia api-e2e (header) | Revisar si el header cambia; si no, dejar + anotar deuda |
| Reescritura de flows api_e2e introduce regresion | C-A: invocar los flows existentes desde tests, no reescribir la logica |
| `claude -p` cambia cuenta gh activa | Validar la skill DESPUES de las git ops; restaurar cuenta bypabloc |

[<- 15 verificacion e2e](15-verificacion-e2e.md) | [README ->](README.md)
