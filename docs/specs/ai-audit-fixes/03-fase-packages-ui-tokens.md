# Fase 2 - packages/ui: color contrast tokens

[< 02 packages/seo](02-fase-packages-seo.md) | [04 devtools/validator >](04-fase-devtools-validator.md)

## Objetivo

Subir `accessibility` Lighthouse de 97 a 100 arreglando los 2
tokens que fallan WCAG AA contrast ratio en small text (4.5:1 min).

## Diagnostico

`packages/ui/src/styles/tokens.css`:

| Token | Valor | Sobre dark bg `#0a0a0a` | WCAG AA small text? |
|-------|-------|------------------------|---------------------|
| `--color-text-muted: grey-40` (`#7a7a74`) | dark | 5.71:1 | ok |
| `--color-text-subtle: grey-50` (`#5c5c57`) | dark | 3.42:1 | **fail** |

| Token | Valor | Sobre light bg `#f7f7f5` | WCAG AA small text? |
|-------|-------|--------------------------|---------------------|
| `--color-text-muted: grey-40` (`#7a7a74`) | light | 4.31:1 | **fail** |
| `--color-text-subtle: grey-50` (`#5c5c57`) | light | 7.18:1 | ok |

## Cambios

### A. Dark mode: subir text-subtle

```diff
  :root {
-   --color-text-subtle: var(--color-grey-50);  /* #5c5c57 -> 3.42:1 FAIL */
+   --color-text-subtle: var(--color-grey-40);  /* #7a7a74 -> 5.71:1 OK */
  }
```

### B. Light mode: oscurecer text-muted

```diff
  :root.light {
-   --color-text-muted: var(--color-grey-40);  /* #7a7a74 -> 4.31:1 FAIL */
+   --color-text-muted: var(--color-grey-60);  /* #46463f -> 8.95:1 OK */
  }
```

## Verificacion visual

Antes de mergear, levantar dev de UN niche + togglear dark/light y
confirmar que los textos `text-muted`/`text-subtle` siguen legibles
y consistentes:

```bash
pnpm --filter @portfolio/generic run dev
# abrir http://localhost:4321
# usar toggle de tema y verificar Hero, ExperienceCard, ProjectCard
```

## Tests

No hay test automatizado de contrast (Lighthouse PSI lo cubre en
fase 9). Si en el futuro se quiere unit test, se puede agregar uno
que use `wcag-contrast-ratio` (npm) — pero NO bloquea este plan.

## Archivos afectados

### Modificar

- `packages/ui/src/styles/tokens.css` — 2 lineas (dark + light)
  - Verificar visual: `pnpm --filter @portfolio/generic run dev` +
    inspeccion manual
  - Verificar build: `pnpm run build` los 6 verde
  - Verificar audit (fase 9): `lighthouse_psi.accessibility == 100`

## Verificacion incremental

```bash
# Build verde
pnpm run build

# Visual
pnpm --filter @portfolio/generic run dev

# Audit (post-deploy)
python devtools/run.py ai_audit --niches=generic --tools=lighthouse_psi
# esperado: accessibility=100
```

[< 02 packages/seo](02-fase-packages-seo.md) | [04 devtools/validator >](04-fase-devtools-validator.md)
