# Harness Protocol - portfolio

> Convenciones de Harness Engineering aplicadas al portfolio. Define como
> Claude Code orquesta subagentes, gestiona contexto y se auto-verifica.

## Activacion

Esta regla aplica SIEMPRE en este proyecto cuando se trabaja con harness queue
(`docs/<modulo>/feature_list.json`) o subagentes con outputs grandes. Define
el contrato entre:

- Claude main (orquestador)
- Subagentes (researcher, code-reviewer)
- El filesystem (`docs/progress/`, `docs/<modulo>/feature_list.json`)
- El usuario (humano supervisor)

Para proyectos chicos donde no necesitas la queue, este protocolo solo aplica
parcialmente: el patron output-en-disco para subagentes sigue siendo util.

## Principios

1. **Filesystem como substrate.** El estado del proyecto vive en disco, no
   en la ventana de contexto.
2. **Contexto es recurso escaso.** Compactar agresivamente al 75% (env
   `CLAUDE_AUTOCOMPACT_PCT_OVERRIDE=75`).
3. **Anti-telefono-descompuesto.** Los subagentes escriben sus outputs en
   archivos del filesystem. El orquestador solo lee referencias.
4. **Verificacion ejecutable.** Nunca decir "listo" sin demostrarlo. Tests,
   linters, typecheck deben correr.
5. **Auto-mejora.** Cuando el harness detecta un patron de error, se modifica
   a si mismo (nueva regla, nuevo hook, nueva entrada).

## Ventana de contexto: regla del 75%

Investigacion confirma que la degradacion del modelo empieza alrededor del
20% de uso de la ventana y se vuelve notoria al 40-48%.

### Configuracion actual del proyecto

En `.claude/settings.json`:

```json
{
  "env": {
    "CLAUDE_AUTOCOMPACT_PCT_OVERRIDE": "75"
  },
  "autoCompactEnabled": true
}
```

### Que significa

- Auto-compact se dispara al 75% de uso de la ventana
- Trade-off: pagas un re-compact mas frecuente (rompe prompt cache 1 vez) a
  cambio de evitar que el modelo se vuelva "tonto" en sesiones largas

### Comandos relevantes

| Comando | Cuando usarlo |
|---------|---------------|
| `/compact` | Compactar manualmente ahora |
| `/clear` | Reset total (perdes contexto, no recomendado mid-feature) |
| `/context` | Ver % de uso actual de la ventana |

## Subagentes: patron output-en-disco

Cuando Claude main lanza un subagente via Task tool y se espera output
extenso (research, code review), el prompt al subagente DEBE incluir esta
instruccion:

> "Escribe tu resultado completo en `docs/progress/<rol>_<scope>.md`. Tu
> respuesta a mi orquestador debe ser solo una linea:
> `done -> docs/progress/<rol>_<scope>.md` o
> `blocked -> ver docs/progress/current.md`."

### Naming convention para outputs

| Subagente | Patron de archivo |
|-----------|-------------------|
| researcher | `docs/progress/explore_<tema>.md` |
| Explore (general-purpose) | `docs/progress/explore_<tema>.md` |
| code-reviewer | `docs/progress/review_<feature>.md` |

### Cuando NO aplica

- Subagentes que devuelven 1-3 lineas (ej: validacion booleana)
- Tareas exploratorias triviales que caben en un parrafo
- Cuando el usuario explicitamente pide "muestralo en chat"

## feature_list.json (opcional, harness queue)

Si el proyecto usa harness queue, mantener un `feature_list.json` con:

- `one_feature_at_a_time: true` — solo 1 feature en `in_progress` a la vez
- Estados validos: `pending`, `in_progress`, `done`, `blocked`
- Numeracion incremental
- Si trabajas varios sub-areas (ej. CV, projects, blog), crea uno por area
  en `docs/<area>/feature_list.json`

### Estructura de una feature

```json
{
  "id": 1,
  "name": "snake_case_id",
  "title": "Titulo legible",
  "description": "Que hace y por que",
  "acceptance": [
    "Criterio observable 1",
    "Criterio observable 2"
  ],
  "status": "pending"
}
```

### Como elegir feature

1. Abrir `docs/<area>/feature_list.json` (o el principal si solo hay uno)
2. Filtrar por `status == "pending"`
3. Tomar la de menor `id`
4. Cambiar status a `in_progress`, guardar
5. Anotar en `docs/progress/current.md`

## docs/progress/current.md y history.md

- `current.md` = estado de la sesion ACTIVA. Se actualiza en tiempo real.
- `history.md` = bitacora append-only de sesiones cerradas.

Al cerrar sesion (hook `Stop`):

1. Mover resumen de `current.md` al final de `history.md`
2. Vaciar `current.md` dejando solo el template
3. Limpiar archivos temporales (`explore_*.md`, `review_*.md`)
   en `docs/progress/`

## Gate de inicio de sesion

```bash
./.claude/hooks/harness-init.sh
HARNESS_INIT_QUIET=1 ./.claude/hooks/harness-init.sh   # solo [WARN] y [FAIL]
```

Verifica:

1. Archivos base existen (`.claude/settings.json` critico; `CLAUDE.md`,
   `docs/progress/` recomendados)
2. `docs/<modulo>/feature_list.json` existente es JSON valido (si aplica)
3. pnpm disponible + node_modules presente
4. Branch actual no es protegida
5. `docs/progress/` no tiene temporales viejos sin sesion activa

## Hooks como enforcement

Todos los principios de esta regla se enforzan via hooks en
`.claude/settings.json`:

- `PreToolUse` Bash — protege comandos peligrosos, branches protegidas
- `PreToolUse` Edit/Write — protege archivos sensibles
- `PostToolUse` Edit/Write — format-on-save automatico (Biome)
- `PostToolBatch` — lint-check global tras una serie de edits
- `Stop` — verify-state al cerrar (mueve current → history, limpia temps)
- `SubagentStop` — recordatorio de memoria post-subagente
- `SessionStart` (compact) — context al volver de compactacion
- `SessionStart` (startup) — health check soft de inicio

Diferencia con prosa en CLAUDE.md: los hooks SE EJECUTAN, no se pueden saltar.

## Anti-patterns

- ❌ Outputs largos de subagentes en chat (rompe contexto del orquestador)
- ❌ Multiples features in_progress simultaneamente en el mismo modulo
- ❌ Marcar feature como `done` sin tests verdes
- ❌ Editar `docs/progress/history.md` (es append-only)
- ❌ Confiar en CLAUDE.md como enforcement (debe ser hook)
- ❌ Compactar contexto util (compact al 75% solo si la sesion lo justifica)

## Escala del workflow

| Tamano | Cuando aplicar harness completo |
|--------|--------------------------------|
| Micro (1-2 archivos, hotfix) | Saltar feature_list.json. Solo verify-before-done. |
| Small (3-5 archivos) | feature_list.json opcional + tests obligatorios |
| Medium (6-10 archivos) | Full harness + 1-2 subagentes con output en disco |
| Large (11+ archivos) | Full harness + leader/implementer/reviewer pattern |
