# 07. Paralelizacion con git worktrees

> Seccion 10 del [plan-format](../../../.claude/rules/plan-format.md).

[← 06](06-commits.md) · [README](README.md) · [08 →](08-verificacion-e2e.md)

## Base secuencial (no paralelizable)

Los commits C1-C8 son base secuencial. Cada uno toca codigo
transversal o establece un contrato que los siguientes consumen:

- C1 (carpeta del plan): base.
- C2 (provisioner EDGE): infraestructura comun.
- C3-C4 (yaml dev + stage/prod): editan el mismo `portfolio-api.yaml`
  por env distinto, podrian paralelizarse, pero se hacen seriales por
  consistencia y para evitar conflicto en `serverless/lambda/.state/`.
- C5 (drop stream_event_id): cambio de schema DB + modelo + service.
  El modelo SQLAlchemy lo consume el `stream_processor` ya eliminado y
  el tracking_service; tocar antes de C6.
- C6 (Pydantic required): contrato del payload. C9 (frontend) depende
  de este contrato.
- C7 (ua-parser swap): cambio del modulo `shared/observability/`. C6
  no lo toca; pero ambos commitean en el mismo Lambda → seriales para
  evitar conflictos de `pyproject.toml`/`uv.lock`.
- C8 (cloudfront-viewer-country): cambio de `shared/lambda_kit/`. C6
  no lo toca; seriales por la misma razon de coherencia.

> Decision pragmatica: C5-C8 son tareas pequenas (1-3 archivos cada
> una). Paralelizarlas tiene mas overhead que ganancia.

## Punto de fork — despues de C8

Desde C9 abre la ventana de paralelizacion. C9, C10, C11 y C12 tocan
archivos disjuntos del frontend y no se pisan.

```text
                        C8 (commit en feature/tracking-data-completeness)
                                          │
              ┌───────────┬───────────────┼──────────────┐
              │           │               │              │
       worktree A    worktree B     worktree C     worktree D
       (T9)          (T10)          (T11)          (T12)
       build-track-  ClientRouter   NicheDropdown  HeroIdentity
       payload       + VT.css       + Drawer       + ProjectCard
              │           │               │              │
              └───────────┴───────────────┼──────────────┘
                                          │
                                     merge a feature/  (resolver
                                     conflictos solo en index.ts
                                     barrels si hay)
                                          │
                                     C13 (Playwright)
                                          │
                                    C14 (deploy real)
                                          │
                                    C15 (verificacion + delete plan)
```

## Tabla de colisiones

| Worktree | Archivos exclusivos | Conflicto potencial |
|----------|--------------------|--------------------|
| A — T9 (build-track-payload) | `packages/ui/src/lib/build-track-payload.ts`, `lib/track-event.ts`, `tests/unit/lib/build-track-payload.test.ts` | Ninguno con B/C/D |
| B — T10 (ClientRouter + VT) | `packages/app-shared/src/layouts/BaseLayout.astro`, `packages/ui/src/styles/view-transitions.css`, `packages/ui/src/lib/stagger.ts`, `packages/ui/src/components/ThemeToggle.astro`, `tests/unit/lib/stagger.test.ts` | `packages/ui/src/index.ts` (barrel — si A y B agregan exports). Resolucion: merge manual de exports al cerrar B. |
| C — T11 (navbar) | `packages/ui/src/components/NicheDropdown.astro`, `MobileNavDrawer.astro`, `packages/ui/src/lib/init-mobile-nav.ts`, tests asociados | Ninguno con A/B/D |
| D — T12 (Hero + ProjectCard) | `packages/app-shared/src/components/HeroIdentity.astro`, `ProjectCard.astro`, pages de las 6 apps (`/index`, `/about`, etc.) | `packages/app-shared/src/index.ts` (barrel del export `HeroIdentity`). Resolucion: merge manual. |

## Donde NO paralelizar

- **Config central**: `astro.config.ts` de cada app, `biome.json`,
  `tsconfig.json`, `package.json` de `packages/ui`, `pyproject.toml`
  del shared/observability — solo el commit que los modifica los
  toca.
- **Grilla de comandos**: `devtools/run.py` y `serverless/cli/` solo
  en C2 (provisioner).
- **Limpieza del plan**: C15 solo cuando todo lo anterior esta
  mergeado.
- **Seccion 11 (verificacion E2E)**: C13 + C14 + C15 son seriales.

## Como lanzar cada worktree

Pre-requisito: estar en `feature/tracking-data-completeness` con
C1-C8 commiteados y pusheados.

```bash
# Desde el repo principal
cd /home/bypabloc/projects/bypabloc/portfolio

# Worktree A — T9
git worktree add ../portfolio-w-a feature/tracking-data-completeness
cd ../portfolio-w-a
git checkout -b feature/tracking-completeness-build-payload
# trabajar...
git push -u origin feature/tracking-completeness-build-payload

# Worktree B — T10
git worktree add ../portfolio-w-b feature/tracking-data-completeness
cd ../portfolio-w-b
git checkout -b feature/tracking-completeness-view-transitions

# Worktree C — T11
git worktree add ../portfolio-w-c feature/tracking-data-completeness
cd ../portfolio-w-c
git checkout -b feature/tracking-completeness-navbar-fix

# Worktree D — T12 (depende de B: HeroIdentity necesita view-transitions
# ya pusheadas, sino el bloque transition:name no tiene CSS de soporte;
# pero funcionan independientes, el visual lo ata B+D)
git worktree add ../portfolio-w-d feature/tracking-data-completeness
cd ../portfolio-w-d
git checkout -b feature/tracking-completeness-hero-cards
```

## Estrategia de merge de worktrees

1. Cada worktree commitea + pushea su branch.
2. Cuando A, B, C, D estan listas, abrir 4 PRs hacia
   `feature/tracking-data-completeness` (no `dev`).
3. Mergear A primero (no depende de nadie).
4. Mergear B (puede conflictuar con A en barrel `packages/ui/src/index.ts`).
5. Mergear C (independiente).
6. Mergear D (puede conflictuar con B en barrel `packages/app-shared/src/index.ts`).
7. Una vez los 4 mergeados, `feature/tracking-data-completeness` tiene
   los commits C9, C10, C11, C12.

### Alternativa simple — sequential

Si la coordinacion de 4 worktrees es overkill, ejecutar C9 → C10 → C11
→ C12 secuencial en la misma branch. Trade-off: ~2x tiempo de
implementacion (1 dia vs 1/2 dia), cero conflictos.

> **Recomendacion**: si el plan se ejecuta solo, ir secuencial. Si hay
> 2+ devs, usar worktrees A+C en paralelo (cero conflictos garantizados),
> dejar B y D seriales.

## Anti-patrones

- ❌ Lanzar B antes que C8 commiteado: B necesita el header
  `cloudfront-viewer-country` parseado para no romper en runtime
  cuando el tracking se dispare con view transitions.
- ❌ Lanzar D antes que B: D agrega `transition:name`, B agrega
  `<ClientRouter />`. Sin ClientRouter, los `transition:name` no se
  activan (degradacion silenciosa). El test E2E lo detecta, pero hace
  perder tiempo.
- ❌ Worktrees sin push: si A se queda solo local, no puede mergearse
  a `feature/`. Pushear al menos un commit por worktree antes del
  fin de jornada.
- ❌ Resolver conflictos de barrel con `--theirs`/`--ours` ciego:
  conviene merge manual revisando que ambos exports queden.

---

Siguiente: [08. Verificacion E2E iterativa →](08-verificacion-e2e.md)
