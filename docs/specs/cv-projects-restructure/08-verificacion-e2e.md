# Seccion 11: Verificacion E2E iterativa (gate de cierre)

> Fase FINAL del plan. NO se hace `git push` ni se crea PR hasta que
> esta bateria entera pase en verde.

## Parte A: refactor de tests

- [ ] Buscar referencias a `cv-builder` y `portfolio-astro` en todo el repo:
  ```bash
  rg "cv-builder|portfolio-astro" --type yaml --type ts --type tsx --type astro
  # debe devolver 0 resultados (salvo este plan)
  ```
- [ ] Buscar tests viejos que asumian 6 proyectos:
  ```bash
  rg "length.*6|length === 6" packages/content/tests/
  # corregir cualquier match
  ```
- [ ] Buscar `CaseStudyExpander` en `CvSections.astro`:
  ```bash
  rg "CaseStudyExpander" packages/app-shared/src/components/CvSections.astro
  # debe devolver 0 resultados
  ```
- [ ] Tests del schema deben validar `links` y `summary`:
  ```bash
  pnpm --filter @portfolio/content exec vitest run
  ```

## Parte B: bateria de comandos reales

Ejecutar en orden. Si algo falla: diagnosticar -> corregir -> re-ejecutar
TODA la bateria desde el principio.

```bash
# 1. Conformance
pnpm exec biome check .                            # debe pasar

# 2. Typecheck packages
pnpm exec tsc --noEmit                             # debe pasar

# 3. Astro check de las 6 apps
pnpm exec astro check                              # debe pasar (recursivo)

# 4. Unit tests con coverage en packages
pnpm exec vitest run --coverage                    # >=80% per-file en mods

# 5. Build de las 6 apps
pnpm run build                                     # debe pasar

# 6. Seed del CV en dev y regenerar cache
python devtools/run.py serverless run --stage=dev --lambda=db \
  --event=serverless/lambda/services/db/events/seed.json \
  --aws-profile=tfs-dev                            # debe pasar

node scripts/fetch-cv-cache.mjs                    # cache regenerado

# 7. Verificacion del /track endpoint
curl -X POST https://api.dev.the-full-stack.com/track \
  -H "Content-Type: application/json" \
  -d '{
    "operation": "tracking",
    "action": "track",
    "data": {
      "session_id": "00000000-0000-0000-0000-000000000000",
      "event_id": "11111111-1111-1111-1111-111111111111",
      "event_type_id": "22222222-2222-2222-2222-222222222222",
      "page_url": "https://generic.portfolio.dev.the-full-stack.com/",
      "event_props": {}
    }
  }' \
  -i 2>&1 | head -10                               # debe responder 204

# 8. E2E Playwright contra los 6 subdominios (opcional pero recomendado)
python devtools/run.py docker up --env=local
python devtools/run.py test_runner --module=feature --type=feature --env=local
python devtools/run.py docker down --env=local
```

## Checks visuales (manual)

Levantar dev en cada app que cambia visualmente y verificar:

```bash
pnpm --filter @portfolio/fintech run dev
# Abrir http://fintech.localhost:9970:
# - Seccion "Proyectos" (NO "destacados")
# - 2-3 proyectos visibles (Chile, Mexico, MVP en fintech)
# - destacame-debt-chile muestra 3 botones de links
# - NO existe bloque .case-studies bajo el grid
# - Click en card abre /projects/<slug> donde aparece el acordeon caseStudyDetailed
# - TimelineItem muestra summary corto, no listado completo
# - Click en item del nav "Otras vistas" -> dropdown con 5 niches
# - Click en una niche -> navega en misma tab al subdominio correspondiente

pnpm --filter @portfolio/hub run dev
# Abrir http://hub.localhost:9970:
# - heroIntro tiene fondo full-bleed
# - Texto del intro tiene <180 chars
# - Tipografia mas pequena que antes
```

## Eliminar la spec (ultimo commit)

```bash
git rm -r docs/specs/cv-projects-restructure/
git commit -m "$(cat <<'EOF'
chore(specs): borrar docs/specs/cv-projects-restructure

- El plan fue ejecutado en 13 commits previos.
- Las decisiones que deben sobrevivir ya viven en rules + memoria engram.
- Carpeta efimera segun .claude/rules/plan-format.md.
EOF
)"
```

## Push y PR

SOLO si TODOS los pasos anteriores pasaron:

```bash
git push origin feature/cv-projects-restructure
gh pr create --base dev --head feature/cv-projects-restructure \
  --title "feat: refactor de proyectos + experiencias + nav + hub + fix track" \
  --body "$(cat <<'EOF'
## Problema

1. Catalogo de proyectos tenia 6 entries con 2 obsoletas.
2. Sistema de saldar deudas Chile tiene 3 URLs, el schema solo soportaba 1.
3. Casos de estudio sobrecargaban el home en cada niche.
4. "Otras vistas" abria pestana nueva, queriamos dropdown interno.
5. Hub hero con texto largo y fondo no full-bleed.
6. /track devolvia 403 en dev.
7. Experiences mostraban todos los responsibilities en el home.

## Solucion

1. Eliminar 2 proyectos obsoletos, dejar 4 curados (Chile, Mexico, MVP, FastStruct).
2. Extender ProjectSchema con `links: { label, url }[]`.
3. Mover bloque CaseStudyExpander al ProjectDetail.
4. Reemplazar item nav por NicheDropdown con 5 niches y navegacion same-tab.
5. Hub hero: full-bleed bg + texto corto + tipografia mas chica.
6. Diagnosticar y arreglar /track (causa documentada en commit 13).
7. Agregar `summary: BiLang` obligatorio a Experience, render solo en home.

## Como probar

Ver bateria de la seccion 11 del plan (ya ejecutada, verde).

## TODO

- Si quedaron datos estimados (`metricsEstimated: true`), confirmar antes de merge a stage/main.
EOF
)"
```

## Regla de cierre

Si CUALQUIER paso de la Parte B falla, NO continuar: diagnosticar y
corregir hasta que TODO pase. Esta fase NO se marca completa con un
test rojo, build roto o /track respondiendo algo distinto a 204.
