# Sección 11 — Verificación E2E iterativa (fase final)

[← Paralelización](09-paralelizacion-worktrees.md) · [Anexo métricas →](11-metricas-estimadas.md)

Última fase y último commit (Commit 9). Bucle "no parar hasta que
funcione": ejecutar → si falla, diagnosticar → corregir → re-ejecutar →
repetir. NO se marca completa con un comando fallando, un test rojo o
coverage < 80%.

## Parte A — Refactor de tests + anexo de métricas

1. Tests del schema (`country`, `metricsEstimated`) verdes.
2. `data-parity` baselines (`experiences.json`, `projects.json`)
   actualizados a la data nueva — cambio deliberado.
3. Test del merge del summary por nicho presente y verde.
4. Barrido: ninguna ruta dinámica usa `getCollection()` (el proyecto no
   tiene content collections):
   ```bash
   rg -n "getCollection" apps packages --glob '!**/node_modules/**'
   # esperado: cero resultados
   ```
5. **Anexo `11-metricas-estimadas.md` completo**: cada entry con
   `metricsEstimated: true` tiene su cifra listada con justificación.
   Verificar que el set del anexo == el set de entries marcadas:
   ```bash
   rg -l "metricsEstimated: true" packages/content/src/data
   # cada archivo listado debe estar cubierto en el anexo
   ```

## Parte B — Batería de comandos reales

### B.1 — Frontend

```bash
pnpm install
pnpm exec biome check .
pnpm exec tsc --noEmit
pnpm run typecheck            # astro check recursivo (incluye [slug].astro)
pnpm run test
pnpm run test:coverage        # >= 80% per-file en lo modificado
pnpm run build                # las 6 apps + las ~192 paginas de detalle
```

### B.2 — Backend Python (Fase 2)

```bash
python -m compileall -q serverless/lambda/shared/db db/cv/seed
python devtools/run.py serverless tests --type=unit --shared

# migracion: cadena Alembic + upgrade/downgrade
#   (branch Neon efimero, o --sql offline si no hay Neon — ver plan A)
```

### B.3 — E2E Playwright

```bash
python devtools/run.py docker up --env=local
python devtools/run.py test_runner --module=feature --type=feature --env=local
python devtools/run.py docker down --env=local
```

Si se agregan specs de las páginas de detalle (decisión de esta fase):
deben navegar a una `/experience/<slug>` y una `/projects/<slug>` y
verificar HTTP 200 + contenido esperado.

### B.4 — Verificación visual

```bash
pnpm run preview
```

- Home de un nicho: experiencias destacadas con detalle + experiencias
  antiguas como tarjeta resumen con botón.
- `/experience/<slug>`: render completo de una experiencia.
- `/projects/<slug>`: render completo de un proyecto con case study.
- Cambio de idioma es↔en en una página de detalle.
- Confirmar que `metricsEstimated` NO aparece en ningún HTML.

## Matriz de cierre — AC vs verificación

| AC | Verificación |
|----|--------------|
| AC-1, AC-2 | B.1 `vitest` content |
| AC-3 | B.1 — `stats.countries` deriva; 4 países |
| AC-3b, AC-3c, AC-3d | B.2 — migración + tests `shared` |
| AC-4, AC-5, AC-7 | B.1 `vitest` + B.4 preview |
| AC-6, AC-8 | B.1 `vitest` content |
| AC-9, AC-10 | B.1 test del merge + B.4 preview |
| AC-11, AC-12 | B.1 `pnpm run build` + B.3 |
| AC-13 | B.3 + B.4 — enlaces desde las tarjetas |
| AC-14 | Parte A — revisión de textos (español neutro, inglés US) |

## Regla de cierre

El plan se marca completo SOLO cuando:

- B.1: comandos verdes, coverage >= 80% per-file, 6 apps + ~192 páginas
  buildean.
- B.2: `compileall` verde, tests `shared` verdes, migración
  `upgrade`/`downgrade` OK.
- B.3: E2E Playwright verde.
- B.4: páginas de detalle renderizan; `metricsEstimated` no visible.
- Parte A: anexo de métricas completo y sincronizado con las entries
  marcadas; barrido `getCollection` sin resultados.

Si algo falla: diagnosticar, corregir, re-ejecutar la batería completa.

## Commit final

```bash
git rm -r docs/specs/cv-content-enrichment/
git commit -m "test(cv-content): verificacion E2E del plan de enriquecimiento

- ejecuta la bateria completa con el codigo final integrado
- elimina la carpeta efimera del plan tras completar la implementacion"
```

> El anexo `11-metricas-estimadas.md` se elimina con la carpeta. Antes de
> borrarlo, su contenido debe haberse trasladado al cuerpo del PR (o a un
> issue de seguimiento) para que el usuario conserve la lista de cifras a
> validar tras el merge. La carpeta del plan es efímera; la lista de
> métricas estimadas NO debe perderse.

[← Paralelización](09-paralelizacion-worktrees.md) · [Anexo métricas →](11-metricas-estimadas.md)
