# Fase 5 — Summary por nicho en el i18n curriculum

[← Fase 4](05-fase-proyectos.md) · [Fase 6 →](07-fase-paginas-detalle.md)

## Objetivo

Cada nicho muestra un `summary` específico en su hero. Cubre AC-9, AC-10.

## Estado actual

- `CurriculumStringsSchema.hero` (schemas.ts:507) ya tiene `summary`.
- `CurriculumOverrideSchema.hero` (schemas.ts:534) ya tiene
  `summary: z.string().min(1).optional()`.
- **El schema YA soporta el summary por nicho** — esta fase NO toca
  `schemas.ts`, es solo data.
- `mergeCurriculum` hace shallow merge de `hero`: si el override de un
  nicho declara `hero.summary`, reemplaza el del `_base`; si no, hereda.
- Hoy: `_base.{es,en}.yaml` declara `hero.summary`; los overrides de
  nicho (`fintech.es.yaml`, etc.) **ya declaran o no** un `summary`
  propio según el archivo — hay que revisarlos uno por uno.

## Sub-tareas

### 5.1 — Auditar los 5 niches

Para cada `curriculum/<nicho>.{es,en}.yaml` (fintech, architect, leader,
vibe, generic), verificar si `hero.summary` ya está declarado y si su
contenido es realmente específico del nicho o una copia del `_base`.

### 5.2 — Redactar el summary de cada nicho

Cada nicho tiene un `hero.summary` que posiciona ese perfil. Insumos: la
respuesta del usuario al cuestionario (P1, P2) + la decisión D-12.

| Nicho | Enfoque del summary |
|-------|---------------------|
| `fintech` | Producto fintech replicable: integró Scotiabank, Santander, Santander Consumer como configuración; sistemas que escalan e iteran con datos de usuario |
| `architect` | Diseñó arquitecturas completas (frontend + microservicios) que se implementaron con éxito; deprecó sistemas legacy |
| `leader` | Liderazgo técnico de equipos; reestructuró proyectos en dificultad y los llevó a término |
| `vibe` | Vibe coding, Claude Code, dev tools; FastStruct (pre-Claude-Code), este portfolio, el CV open source |
| `generic` | Full Stack senior, 12 años, el perfil más completo y detallado |

Reglas:
- Español neutro; inglés con tono US (D-13, D-14).
- El summary del nicho es coherente con el `headline` y `nicheLabel`
  que ese mismo YAML ya define.
- Si una afirmación incluye una cifra estimada, registrarla en
  `11-metricas-estimadas.md`.

### 5.3 — `_base` y `profile.ts` como fallback

- `_base.{es,en}.yaml` mantiene su `hero.summary` genérico: es el
  fallback si un nicho no declara el suyo (AC-10).
- El `summary` de `profile.ts` (corregido en el plan A) es el fallback
  global del perfil — no se toca aquí. (D-12: "si solo hay uno toma ese;
  si existe el del perfil, lo captura").

> Aclaración del flujo: el hero del CV usa `getCurriculum(<nicho>)` ->
> `hero.summary`. El `profile.summary` lo usan otros lugares (JSON-LD,
> meta). Son dos summaries distintos con dos propósitos; esta fase toca
> el del curriculum (hero visible). El de `profile.ts` quedó del plan A.

## Verificación de la fase

```bash
pnpm --filter @portfolio/content exec vitest run
pnpm --filter @portfolio/app-shared exec vitest run
pnpm --filter @portfolio/content run typecheck
```

Si hay un test del merge de curriculum, debe seguir verde; si no, se
agrega uno que valide AC-9 y AC-10.

## Definition of Done de la fase

- [ ] Los 5 niches tienen `hero.summary` específico en su
      `curriculum/<nicho>.{es,en}.yaml`.
- [ ] `_base.{es,en}.yaml` mantiene su `summary` genérico como fallback.
- [ ] Test que valida: nicho con summary propio lo usa; nicho sin
      summary cae al `_base`.
- [ ] `vitest` content + app-shared + typecheck verdes.

[← Fase 4](05-fase-proyectos.md) · [Fase 6 →](07-fase-paginas-detalle.md)
