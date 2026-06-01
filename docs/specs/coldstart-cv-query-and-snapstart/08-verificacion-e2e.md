# 08 — Verificacion E2E iterativa (seccion 11, fase final)

[< Worktrees](07-paralelizacion-worktrees.md) | [README](README.md)

> Última fase y último commit. Gate del PR: push + PR SOLO con esta
> batería completa en verde. Bucle "no parar hasta que funcione".

## Parte A — refactor de tests

- [ ] Ningún test viejo referencia funciones eliminadas de
  `cv_repository.py` (las públicas se mantienen; las internas son
  nuevas). Barrido: `grep -rn '_on_session' serverless/lambda/shared/tests`
  debe encontrar solo los tests nuevos.
- [ ] El test nuevo `test_cv_full_uses_single_session.py` existe en
  `serverless/lambda/shared/tests/unit/shared/db/` y verifica AC-1.
- [ ] Si se tocó `api_e2e`, sus tests unit nuevos están en
  `devtools/tests/`.

## Parte B — bateria de comandos reales

Ejecutar de punta a punta. Si algo falla: diagnosticar -> corregir ->
re-ejecutar la suite -> repetir. NO marcar completo con un comando rojo.

### B.1 — Lint + tests (local, sin AWS)

```bash
# Shared (cv_repository vive aca)
python devtools/run.py serverless lint-deps --shared
python devtools/run.py serverless lint-deps --lambda=cv
python devtools/run.py serverless tests --type=unit --shared
python devtools/run.py serverless tests --type=coverage --lambda=cv   # >=80%

# Si se toco devtools (api_e2e / packaging)
python devtools/run.py serverless tests --type=unit --module=devtools
```

### B.2 — Deploy a dev

```bash
export AWS_PROFILE=tfs-dev
# cv es el cambio principal; redeployar tambien los que importan shared.db
# por si el refactor de cv_repository afecto el cierre (no deberia, pero
# se verifica que no rompio nada):
python devtools/run.py serverless deploy --lambda=cv --stage=dev --aws-profile=tfs-dev
python devtools/run.py serverless status --lambda=cv --stage=dev --aws-profile=tfs-dev
# Confirmar SnapStart sigue On y API integra :live (AC-7):
aws lambda get-function-configuration --function-name portfolio-cv-dev --qualifier live \
  --region us-east-1 --profile tfs-dev --query 'SnapStart'
```

### B.3 — Medición antes/despues (AC-2, AC-5, AC-6)

```bash
# DESPUES del deploy con los cambios:
python devtools/run.py api_e2e --env=dev
# Comparar contra la baseline (guardada antes de empezar):
#   cv.get warm:  7.3s  -> objetivo < 2.0s   [AC-2]
#   cv.get cold:  desglosado restore vs INIT crudo  [AC-6]
#   INIT crudo:   7-20s -> objetivo < 6s (si se hizo C6)  [AC-5]
```

Guardar la baseline ANTES de cualquier cambio:

```bash
# baseline (commitear el output en tmp/ NO; pegar en el PR body)
python devtools/run.py api_e2e --env=dev | tee tmp/api_e2e_baseline.txt
```

### B.4 — No-regresion de los otros Lambdas EN DEV (AC-9)

```bash
# SOLO dev. stage/prod corren codigo viejo, no se tocan ni se comparan.
# auth/users/contact/tracking_writer importan shared.db: confirmar que el
# refactor de cv_repository NO los afecto (cv_repository es solo cv, pero
# se verifica el cierre):
python devtools/run.py serverless lint-deps --lambda=auth
python devtools/run.py serverless lint-deps --lambda=users
python devtools/run.py serverless lint-deps --lambda=contact_form
# Y el flujo E2E completo (auth/users/contact/tracking) en api_e2e ya
# corre arriba — verificar que ninguno regresiona en tiempos/errores.
```

## Criterio de cierre

- [ ] AC-1: `get_full_cv` abre `db_session` exactamente 1 vez (test verde).
- [ ] AC-2: `cv.get` warm < 2.0s en dev (medido).
- [ ] AC-3: contrato de las 9 funciones idéntico (tests verdes).
- [ ] AC-4: cache HIT < 0.1s sin tocar Neon.
- [ ] AC-5: INIT crudo < 6s (si se hizo C6) o documentado por qué no.
- [ ] AC-6: `api_e2e` desglosa restore vs INIT crudo.
- [ ] AC-7: SnapStart On + API integra `:live` tras deploy.
- [ ] AC-8: lint-deps + coverage >= 80% verdes.
- [ ] AC-9: auth/users/contact/tracking sin regresión.
- [ ] Coverage per-file >= 80% en archivos modificados.
- [ ] `git rm -r docs/specs/coldstart-cv-query-and-snapstart/` en el
  último commit (carpeta efímera).

SOLO con TODO lo anterior en verde: `git push` + crear PR.

[< Worktrees](07-paralelizacion-worktrees.md) | [README](README.md)
