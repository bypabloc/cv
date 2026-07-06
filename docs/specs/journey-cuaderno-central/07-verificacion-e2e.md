# 07 — Verificacion E2E iterativa (seccion 11)

> [<- 06 Worktrees](06-paralelizacion-worktrees.md) · [README](README.md)

Fase de cierre. Ultimo commit del plan (C9). Bucle "no parar hasta que
funcione": ejecutar -> si falla, diagnosticar -> corregir -> re-ejecutar ->
repetir.

## Parte A — refactor de tests / referencias

`apps/journey` esta EXENTA de tests unit (no declara script `test`). Aun
asi, barrido de referencias:

```bash
cd apps/journey
# confirmar que ningun archivo de sala referencia la posicion vieja del
# cuaderno (el offset -half+0.9 solo debe existir para retos/aprendizajes,
# NO para lecternNotebook)
rg -n "lecternNotebook" src/engine/rooms/props.ts
rg -n "NOTE_ENTRY_Z_OFFSET" src
```

## Parte B — bateria de comandos reales (VERDE obligatorio)

Desde la raiz del repo:

```bash
# 1. Typecheck de journey
pnpm --filter @portfolio/journey typecheck        # 0 errores

# 2. Lint/format (Biome)
pnpm --filter @portfolio/journey lint

# 3. Build estatico
pnpm --filter @portfolio/journey build

# 4. Build global (confirma que journey no rompe otras apps)
pnpm run build
```

### Verificacion visual manual (10 salas) — local-first

```bash
pnpm --filter @portfolio/journey dev              # http://localhost:4327/
```

Recorrer y confirmar por sala (usar el menu de teleport `M` para saltar
entre las 10 sin recorrer todo el pasillo cada vez):

| Sala | Que verificar |
|------|---------------|
| aula | pilar del cuaderno en el eje central cerca de la entrada, bloquea el paso; sin regresion (canon, ya sin officeLayout que ajustar) |
| corpoelec | pilar centrado; entrada ya estaba libre, sin regresion de escritorios |
| ipasme | pilar centrado + escritorios corridos, entrada despejada (AC-6) |
| iai | idem ipasme (spots identicos) |
| asesoria | pilar centrado + escritorios corridos (AC-6) |
| cofasa | pilar centrado + escritorios corridos (AC-6) |
| dibal | pilar centrado + escritorios laterales corridos (AC-6) |
| goodmeal | pilar centrado + escritorio corrido + NPC "daniela" rodea el pilar sin cruzarlo (AC-5, AC-6) |
| destacame | pilar centrado + escritorio corrido + NPC "valentina" rodea el pilar sin cruzarlo (AC-5, AC-6) |
| futuro | pilar centrado cerca de la entrada + pedestal-CTA propio en el muro final, sin overlap (AC-7) |

Verificacion transversal:

- **Bloqueo real**: en las 10 salas, caminar en linea recta desde la
  entrada por x=0 y confirmar que el jugador choca con el pilar y debe
  desviarse (AC-1).
- **Posicion**: el pilar queda en `x=0` y en la mitad de la sala mas
  cercana a la entrada en las 10 (AC-2).
- **Sin cambio visual**: el cuaderno se ve identico al de antes del
  cambio — mismo cilindro, misma textura, mismo halo/luz (AC-3).
- **Interaccion intacta**: acercarse + E abre el panel de historia
  completa en las 10 salas (AC-8).
- **Retos/aprendizajes/grieta sin cambios**: comparar posicion visual
  contra el estado previo al plan (AC-4).
- **NPCs**: "daniela" (goodmeal) y "valentina" (destacame) completan su
  paseo sin atravesar el pilar (AC-5).
- **Escritorios**: entrada de las 7 salas ajustadas queda tan despejada
  como el aula (AC-6).
- **Futuro**: pilar + pedestal-CTA coexisten sin problema (AC-7).

### Bucle de correccion

Si un comando falla o una sala no cumple su AC: diagnosticar -> corregir ->
re-ejecutar la bateria completa. NO marcar completa con typecheck/build en
rojo o un AC visual sin cumplir.

## Parte C — despliegue REAL

**N/A en el gate de este PR** (local-first, misma politica que
`journey-salas-estandar`): el usuario NO despliega al terminar. El deploy a
Cloudflare Pages es un PR posterior explicito.

## Regla de cierre

El plan se declara "listo" al usuario SOLO cuando:

1. Parte A: sin referencias muertas a la posicion vieja del cuaderno.
2. Parte B: typecheck + lint + build (journey y global) VERDE + las 10
   salas cumplen sus AC en la verificacion visual.
3. Se le da el comando `pnpm --filter @portfolio/journey dev` para que
   Pablo pruebe (local-first), SIN push/PR/deploy hasta que confirme.

El `git push` + PR se hace solo tras la Parte B verde.
