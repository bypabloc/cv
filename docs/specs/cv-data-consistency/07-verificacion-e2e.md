# Sección 11 — Verificación E2E iterativa (fase final)

[← Paralelización](06-paralelizacion-worktrees.md) · [README](README.md)

Última fase y último commit del plan (Commit 6). Dos partes. Bucle "no
parar hasta que funcione": ejecutar → si falla, diagnosticar → corregir →
re-ejecutar → repetir. NO se marca completa con un comando fallando, un
test rojo o coverage < 80%.

## Parte A — Refactor de tests

Verificar que el código nuevo está testeado y nada quedó huérfano:

1. `build-stats.test.ts` referencia los valores correctos (companies 5,
   stats objeto exacto) — no hay un test viejo que afirme `companies: 8`.
2. `cv-detail.test.ts` existe, en la ruta correcta
   (`packages/app-shared/tests/unit/lib/`), convención BDD.
3. Barrido global: ningún test ni código referencia los valores viejos:
   ```bash
   rg -n "companies.*8|8 (años|years) de experiencia|over 8 years" \
     packages apps serverless --glob '!**/node_modules/**'
   # esperado: cero resultados que sean el stat viejo
   ```
4. El modelo `ProfileNiche` no rompió ningún test del backend:
   ```bash
   python devtools/run.py serverless tests --type=unit --shared
   ```

## Parte B — Batería de comandos reales

Ejecutar de punta a punta con el código final de las 3 fases integradas.

### B.1 — Frontend (host, sin Docker)

```bash
pnpm install
pnpm exec biome check .
pnpm exec tsc --noEmit
pnpm run typecheck            # astro check recursivo
pnpm run test                 # vitest recursivo en packages
pnpm run test:coverage        # coverage >= 80% per-file en lo modificado
pnpm run build                # las 6 apps compilan a estático
```

### B.2 — Backend Python (schema + seed)

```bash
python -m compileall -q serverless/lambda/shared/db db/cv/seed
python devtools/run.py serverless tests --type=unit --shared

# Migración: aplicar upgrade + downgrade + upgrade en un branch Neon
neon branches create --name test-e2e-profile-niches --parent main
cd serverless/lambda
.venv/bin/alembic -c shared/db/alembic.ini upgrade head
.venv/bin/alembic -c shared/db/alembic.ini current     # confirma head
.venv/bin/alembic -c shared/db/alembic.ini downgrade -1
.venv/bin/alembic -c shared/db/alembic.ini upgrade head
cd ../..
neon branches delete test-e2e-profile-niches
```

> Si no hay acceso a Neon en la sesión: validar la migración con
> `alembic upgrade --sql` + `alembic downgrade --sql` (genera el SQL sin
> aplicar). La aplicación real a dev/prod la hace el usuario con la
> Lambda `db` (`serverless run --lambda=db --event=events/migrate.json`).

### B.3 — E2E Playwright (stack local)

```bash
python devtools/run.py docker up --env=local
python devtools/run.py test_runner --module=feature --type=feature --env=local
python devtools/run.py docker down --env=local
```

Valida: los 6 subdominios renderizan sin HTTP 502, la StatsBar muestra
`12 / 5 / 4 / 11`, el CV genérico se construye con el detalle completo.

### B.4 — Verificación visual (preview)

```bash
pnpm run preview
```

Abrir `localhost` (generic) y `architect.localhost` (un niche):

- Generic: cada experiencia muestra TODAS sus responsibilities + la
  sección de achievements (AC-9).
- Architect: cada experiencia muestra máximo 3 responsibilities, sin
  achievements (AC-10).
- Ambos: StatsBar con `12 años / 5 empresas / 4 países / 11 certs`.

## Matriz de cierre — AC vs verificación

| AC | Verificación que lo cubre |
|----|----------------------------|
| AC-1, AC-2 | B.1 `vitest run` + B.4 preview |
| AC-3, AC-4 | B.1 `build-stats.test.ts` verde |
| AC-5, AC-6, AC-8 | B.2 migración upgrade/downgrade + `--sql` |
| AC-7 | B.2 seed en branch Neon (5 filas en `profile_niches`) |
| AC-9, AC-10 | B.1 `cv-detail.test.ts` + B.3 E2E + B.4 preview |
| AC-11 | B.1 `pnpm run build` + B.3 E2E |

## Regla de cierre

El plan se marca completo SOLO cuando:

- B.1: todos los comandos verdes, coverage >= 80% per-file.
- B.2: `compileall` verde, tests `--shared` verdes, migración aplica
  `upgrade`+`downgrade`+`upgrade` sin error (o `--sql` validado).
- B.3: E2E Playwright verde, 6 subdominios sin 502.
- B.4: diferencia generic vs niche confirmada visualmente.
- Parte A: barrido `rg` sin resultados de valores viejos.

Si algo falla: diagnosticar, corregir, re-ejecutar la batería completa.
No se difiere.

## Commit final

El Commit 6 incluye:

```bash
git rm -r docs/specs/cv-data-consistency/
git commit -m "test(cv-data): verificación E2E del plan de consistencia

- ejecuta la batería completa (lint, typecheck, unit, build, E2E)
- elimina la carpeta efímera del plan tras completar la implementación"
```

La carpeta del plan es efímera: el `git log` y el PR mergeado conservan
la trazabilidad. Si alguna decisión debe sobrevivir, se promueve a
`.claude/rules/` ANTES de borrar (en este plan, las decisiones son
correcciones de datos puntuales — nada que promover).

[← Paralelización](06-paralelizacion-worktrees.md) · [README](README.md)
