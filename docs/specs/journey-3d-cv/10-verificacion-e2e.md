# Verificacion E2E iterativa — MVP Propuesta A

> [<- Worktrees](09-paralelizacion-worktrees.md) · Seccion 11 del plan-format.
> Ultima fase y ultimo commit (C8). Bucle: ejecutar -> si falla, diagnosticar
> -> corregir -> re-ejecutar TODO -> repetir. No se declara completa con un
> comando en rojo.

## Parte A — refactor de tests

- Ningun test viejo referencia codigo eliminado (esta feature solo AGREGA una
  app; no elimina nada — el barrido debe dar cero).
- Tests nuevos en su ruta mirror: `apps/journey/tests/unit/lib/<X>.test.ts`
  para cada `apps/journey/src/lib/<X>.ts` con logica.
- Barrido global (cero resultados esperados):

```bash
rg -l "journey" packages/ --glob '!**/dist/**' | rg -v "content|node_modules" || true
# ningun package debe haber sido tocado para acomodar a journey
```

## Parte B — bateria de comandos reales

Ejecutar desde el root, en este orden, TODO en verde:

```bash
# 1. Lint + format (Biome, todo el repo)
pnpm exec biome check .

# 2. Typecheck de la app nueva
pnpm --filter @portfolio/journey run typecheck        # astro check + tsc

# 3. Unit tests de la app (coverage >= 80% per-file en lib/)
pnpm --filter @portfolio/journey exec vitest run --coverage

# 4. Unit tests de packages (regresion: journey no debe romper nada)
pnpm run test

# 5. Build estatico de TODAS las apps (journey incluida)
pnpm run build

# 6. Verificacion del HTML generado (AC-3, AC-14)
#    - el CV texto esta en el HTML sin JS:
rg -c "achievements|logros" apps/journey/dist/index.html || \
  rg -c 'cv-fallback' apps/journey/dist/index.html
#    - three NO esta en el chunk critico (es un chunk aparte lazy):
head -c 200000 apps/journey/dist/index.html | rg -c "three" && echo "FAIL: three inline" || echo "OK"

# 7. Preview + smoke HTTP
pnpm --filter @portfolio/journey run preview &
sleep 3
curl -fsS -o /dev/null -w "HTTP %{http_code}\n" http://localhost:4321/
curl -fsS http://localhost:4321/ | rg -c "cv-fallback"
kill %1

# 8. Hooks completos en local
SKIP_STEPS="" git push --dry-run origin feature/journey-3d-propuesta-a
```

Verificacion manual (preview, no automatizable en esta fase):

- Tier Full: caminar las 3 salas, abrir puertas ida/vuelta, leer las fichas,
  cruzar los 3 portales al pasado, disparar 1 micro-interaccion por sala,
  teletransportarse con M, activar/desactivar audio.
- Tier Reduced (DevTools, emulacion movil): el tour guiado corre solo.
- Tier Static (DevTools: bloquear WebGL o `prefers-reduced-motion`): se ve el
  CV 2D completo.

## Parte C — verificacion de despliegue REAL

**N/A en este PR** — decision del usuario: sin deploy (solo local). Cuando el
MVP se valide y se decida desplegar, el PR de deploy tendra su propia Parte C
(cloudflare_setup all, workflow matrix, curl a
`https://journey.portfolio.dev.the-full-stack.com/` con 200 + marcador).

## Gate del PR

`git push` + `gh pr create` SOLO cuando Partes A y B esten completas en verde:
cero tests rojos, coverage >= 80% per-file en archivos con logica, build de
todas las apps exitoso, smoke HTTP 200 con fallback presente.
