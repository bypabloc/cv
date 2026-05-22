# 09 — Verificacion E2E iterativa (fase final)

[<- 08 Worktrees](08-paralelizacion-worktrees.md) | [README](README.md)

## 11. Verificacion E2E iterativa

Ultima fase y ultimo commit del plan. Es el gate del PR: `git push` + crear PR
SOLO cuando esta bateria pase completa en verde.

## Parte A — refactor de tests

- [ ] Ningun test viejo de `contact_form`/`tracking_pixel` construye el evento
  con `operation`/`action` hardcodeados fuera del body — todos usan el nuevo
  contrato.
- [ ] Los tests del handler HTTP generico estan en
  `shared/tests/unit/lambda_kit/`, un escenario por archivo.
- [ ] Los tests del Lambda `cv` siguen el estandar (un archivo = un escenario,
  unit + integration separados).
- [ ] Barrido global: `rg -l "operation.*=.*'contact'" serverless/lambda/services`
  no devuelve hardcodeos en `handler.py` (solo en `OPERATIONS` y tests
  legitimos). Cero hardcodeos de `operation`/`action` en el cuerpo de los
  handlers HTTP.

## Parte B — bateria de comandos reales

Bucle "no parar hasta que funcione": ejecutar -> si falla, diagnosticar ->
corregir -> re-ejecutar la suite -> repetir. NO se marca completa con un
comando fallando, un test rojo o coverage < 80%.

### B.0 — Precondicion (verificar primero)

```bash
python devtools/run.py serverless run --stage=dev --lambda=db \
  --event=events/tables.json --aws-profile=tfs-dev
```

Las tablas del CV deben tener `rows > 0`. Si estan vacias, el seed (otra
sesion) no corrio — la verificacion E2E de `cv` no puede completarse. NO
declarar el plan listo hasta que el seed este aplicado.

### B.1 — Backend serverless

```bash
# tests unit + coverage de todo lo tocado
python devtools/run.py serverless tests --type=unit --shared
python devtools/run.py serverless tests --type=coverage --shared
python devtools/run.py serverless tests --type=unit --lambda=contact_form
python devtools/run.py serverless tests --type=unit --lambda=tracking_pixel
python devtools/run.py serverless tests --type=coverage --lambda=cv
python devtools/run.py serverless lint-deps --lambda=cv

# deploy del Lambda cv a dev
python devtools/run.py serverless deploy --lambda=cv --stage=dev --aws-profile=tfs-dev
python devtools/run.py serverless status --lambda=cv --stage=dev --aws-profile=tfs-dev

# integration E2E contra dev (cv) — branch Neon poblado
python devtools/run.py serverless tests --type=integration --lambda=cv
python devtools/run.py serverless tests --type=integration --lambda=contact_form
python devtools/run.py serverless tests --type=integration --lambda=tracking_pixel

# prueba manual del API: CV completo + una entidad + action invalida
curl -s "$API_BASE/cv?operation=cv&action=get&niche=fintech&locale=es" | head
curl -s "$API_BASE/cv?operation=cv&action=experiences&niche=fintech" | head
curl -s -o /dev/null -w '%{http_code}' "$API_BASE/cv?operation=cv&action=foobar"  # espera 400
```

### B.2 — Frontend Astro

```bash
pnpm install
pnpm exec biome check .
pnpm run typecheck
pnpm exec vitest run            # unit packages (incluye cv-api-client)
pnpm run build                  # 6 apps consumiendo el API cv
pnpm run preview                # verificacion visual del CV
```

### B.3 — E2E Playwright (stack local)

```bash
python devtools/run.py docker up --env=local
python devtools/run.py test_runner --module=feature --type=feature --env=local
python devtools/run.py docker down --env=local
```

La suite `tests/feature/` debe seguir verde: las 6 apps renderizan el CV
obtenido del API; el form de contacto y el tracking siguen funcionando con el
nuevo contrato `operation`/`action`.

## Regla de cierre

El plan NO se marca completo mientras:

- algun comando de B.1/B.2/B.3 falle,
- algun test este rojo,
- el coverage per-file sea < 80% en archivos modificados,
- la precondicion B.0 no se cumpla (DB sin seed).

Cuando TODO pasa: commit 15 (incluye `git rm -r docs/specs/c-cv-data-service/`),
`git push`, crear el PR `feature/cv-data-service -> dev`.

## 12. Definition of Done

**Pre-implementacion**
- [ ] Precondicion B.0 verificada: DB Neon dev poblada con el CV
- [ ] Rama de trabajo correcta (no `dev`/`stage`/`main`)
- [ ] `pnpm install` sin warnings, dev server arranca

**Definition of Done**
- [ ] Los 10 AC tienen al menos un test que los cubre y pasa
- [ ] Coverage per-file >= 80% en archivos modificados/creados
- [ ] Typecheck verde (Python `compileall` + `tsc` + `astro check`)
- [ ] Conformance verde (`biome check`)
- [ ] Build estatico de las 6 apps verde consumiendo el API
- [ ] E2E Playwright verde
- [ ] `contact_form`/`tracking_pixel` sin regresion de comportamiento
- [ ] El contrato `http_handler` promovido a `.claude/rules/lambda-controller.md`
- [ ] Carpeta `docs/specs/c-cv-data-service/` eliminada en el commit 15

[<- README](README.md)
