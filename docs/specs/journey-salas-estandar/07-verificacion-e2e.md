# 07 — Verificacion E2E iterativa (seccion 11)

> [<- 06 Worktrees](06-paralelizacion-worktrees.md) · [README](README.md)

Fase de cierre. Ultimo commit del plan (C17). Tres partes. Bucle "no parar
hasta que funcione": ejecutar -> si falla, diagnosticar -> corregir ->
re-ejecutar -> repetir.

## Parte A — refactor de tests / referencias

`apps/journey` esta EXENTA de tests unit (no declara script `test`). Aun asi:

- **Barrido de referencias muertas**: ningun archivo referencia el viejo id
  `cima` como RoomId, ni `rooms/past.ts` monolitico, ni `MVP_ROOM_SPECS`.

  ```bash
  cd apps/journey
  rg -l "'cima'|\"cima\"|MVP_ROOM_SPECS|rooms/past'" src   # esperado: 0 (o solo comentarios historicos)
  rg -l "rooms/past\b" src                                  # -> ahora rooms/past/index
  ```

- Confirmar que los 8 ids estan en `RoomId`, `THEMES`, `PAST_CAPTIONS`,
  `WORLD` manifest, `ROOM_SPECS` y tienen su `rooms/<id>.ts` + dialogos.

## Parte B — bateria de comandos reales (VERDE obligatorio)

Desde la raiz del repo, con el codigo final:

```bash
# 1. Typecheck de journey (astro check + tsc)
pnpm --filter @portfolio/journey typecheck        # 0 errores

# 2. Lint/format (Biome)
pnpm --filter @portfolio/journey lint             # o: pnpm exec biome check apps/journey

# 3. Build estatico (detecta window/document en client:only, imports rotos)
pnpm --filter @portfolio/journey build            # dist/ generado sin error

# 4. Build global (el pre-push exige las apps; confirma que journey no rompe
#    el catalogo de las 11 keys ni las otras apps)
pnpm run build
```

Recordatorio del gotcha del catalogo: el build global del pre-push exige las
11 keys del catalogo — no introducir env nuevas sin declararlas.

### Verificacion visual manual (8 salas) — local-first

```bash
pnpm --filter @portfolio/journey dev              # http://localhost:4327/
```

Recorrer y confirmar por sala:

| Sala | Que verificar |
|------|---------------|
| aula | profesor sentado que elogia a Pablo + compañeros nuevos; pasado intacto (AC-9) |
| corpoelec | oficina ordenada + seccion inventario (equipos) + cascos + cuadros generadores/transformadores/lineas + showcase gestion/buscador/reportes; pasado equipos regados + frustrados (AC-10, AC-11) |
| ipasme | consultorio + showcase historias clinicas + pasado carpetas papel (AC-14, AC-20) |
| cofasa | linea blisters + andon + showcase paradas + pasado planillas (AC-14, AC-20) |
| dibal | salon+cocina POS/KDS/SUNAT + showcase POS + pasado comandas perdidas (AC-14, AC-20) |
| goodmeal | Good Bags + app + showcase + pasado comida al tacho (AC-14, AC-20) |
| destacame | SIN Chile/Mexico + oficina real + 2 areas (PagaloAqui x3 + destacame x2) + guiños DS/vibe + proximamente + CTA; pasado deudas/tristes (AC-12, AC-13) |
| futuro | roadmap + proximamente + CTA fuerte; build OK sin slug (AC-15) |

Verificacion transversal:

- **Paredes blancas** en las 8 (AC-2); acento del rubro visible.
- **NPCs**: 4-5 conversables por sala (menos aula que ya cumple, menos futuro
  que es cierre), 2 enfoques, dialogos abren sin error (AC-5).
- **Showcase**: E abre panel HTML operable, cicla demos (AC-6). Todas menos
  aula.
- **Cuadros**: 2-4 por sala, ≥1 inspeccionable (AC-7).
- **Kit info**: retos/aprendizajes/grieta/cuaderno en posiciones canonicas
  (AC-8).
- **Teleport (M)**: lista las 8 salas (AC-16).
- **Tour guiado** (forzar tier reduced): recorre las 8 (AC-17).
- **Static** (forzar sin WebGL): CV 2D completo indexable (AC-18).
- **Audio**: opt-in por sala, respeta mute (AC-19).
- **Perf**: `renderer.info.render.calls < 100` por sala en full (AC-4) —
  medir con un `console.log` temporal o el HUD de debug.

### Bucle de correccion

Si un comando falla o una sala no cumple su AC: diagnosticar -> corregir ->
re-ejecutar la bateria completa. NO marcar completa con typecheck/build en
rojo o un AC visual sin cumplir.

## Parte C — despliegue REAL

**N/A en el gate de este PR** (local-first): el usuario NO despliega al
terminar. El deploy a Cloudflare Pages es un PR posterior explicito.

Cuando se haga ese PR de deploy, la Parte C aplicara: mirar el workflow
`deploy-apps.yml` + `curl` a `journey.portfolio.<env>.the-full-stack.com/`
(200 + marcador) hasta confirmar que sirve. Ver `verify-before-done.md`
("Verificacion de despliegue REAL").

## Regla de cierre

El plan se declara "listo" al usuario SOLO cuando:

1. Parte A: cero referencias muertas.
2. Parte B: typecheck + lint + build (journey y global) VERDE + las 8 salas
   cumplen sus AC en la verificacion visual.
3. Se le da el comando `pnpm --filter @portfolio/journey dev` para que Pablo
   pruebe (local-first), SIN push/PR/deploy hasta que confirme.

El `git push` + PR se hace solo tras B verde. El deploy queda para otro PR.
