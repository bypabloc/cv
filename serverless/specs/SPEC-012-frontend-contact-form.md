# SPEC-012: Componente `ContactForm.astro` + integracion 6 apps

**Estado**: draft
**Autor**: Pablo Contreras
**Fecha**: 2026-05-14
**Areas afectadas**: `packages/ui/src/components/`, `apps/*/src/pages/` (los 6)
**Dependencias**: SPEC-005 (Lambda contact_form deployada y operacional)
**Paralelizable con**: SPEC-013

## 1. Contexto

Frontend del form de contacto que llama al backend serverless. Vive en
`packages/ui` (componente compartido) e integrado en los 6 sitios del
portfolio (generic, hub, fintech, architect, leader, vibe).

### Hallazgos de exploracion

- Convencion `packages/ui/src/components/` para componentes compartidos
- Astro 6 + TypeScript strict (`.claude/rules/astro-landing.md`)
- Skill `cloudflare-turnstile` doc 03-frontend-integration con codigo
  base del widget

## 2. Solucion propuesta

Crear 4 archivos en `packages/ui/src/components/contact/`:

```text
packages/ui/src/components/contact/
├── ContactForm.astro            # markup + slot styles + script
├── contact-form.client.ts       # logica client-side TypeScript
├── contact-form.types.ts        # types compartidos
└── contact-form.css             # estilos con design tokens
```

Mas integracion en las 6 paginas `/contact` (1 por app, con i18n
es/en).

### Decisiones clave

- **Decision 1: Sin framework JS adicional** — vanilla TypeScript +
  Astro islands. Razon: 0 KB JS adicional vs React/Vue. Form simple
  con ~50 lineas TS.
- **Decision 2: Turnstile Managed mode** — Cloudflare decide
  invisible vs interactive segun risk score (decision documentada en
  `.claude/docs/cloudflare-turnstile/02-modes-comparison.md`).
- **Decision 3: Optimistic UI feedback** — disable button + show
  spinner durante submit. En error, mostrar mensaje accionable +
  `turnstile.reset()` para nuevo token. En success, mostrar
  mensaje + form.reset() + scroll.
- **Decision 4: Field visibility progresiva** — campos opcionales
  (empresa, cargo, presupuesto, timeline) en `<details>` colapsado
  para no abrumar.

## 3. Criterios de Aceptacion (AC)

- **AC-1**: Given visitante en https://the-full-stack.com/contact,
  When la pagina renderiza, Then ve form con campos nombre, email,
  mensaje, tipo de servicio (dropdown), boton "Enviar"
- **AC-2**: Given visitante completa form con datos validos, When click
  "Enviar", Then UI muestra spinner + boton disabled + Turnstile token
  generado automaticamente (Managed mode)
- **AC-3**: Given submit exitoso (Lambda responde 200), When llega
  response, Then UI muestra mensaje verde "Gracias, te respondo en
  24-48h" + form.reset() + Turnstile.reset()
- **AC-4**: Given submit falla con 429 (rate-limit), When llega
  response, Then UI muestra mensaje amarillo "Has enviado muchos
  mensajes. Reintenta en X minutos" + form NO se limpia (preservar
  contenido para no perder datos del usuario)
- **AC-5**: Given submit falla con 403 (Turnstile rechazado), When
  llega response, Then UI muestra "Verificacion de seguridad fallo,
  recarga la pagina"
- **AC-6**: Given submit falla con 5XX o network error, When llega
  response, Then UI muestra "Hubo un problema, intenta de nuevo en
  unos segundos" + boton vuelve a enabled
- **AC-7**: Given las 6 apps deployadas con el componente, When abro
  /contact en cada subdominio, Then form funciona identico + envia al
  mismo endpoint API
- **AC-8**: Given form rendered, When inspecciono lighthouse, Then
  scores: Performance >= 95, Accessibility >= 95 (form labels,
  contrast, focus visible), Best Practices >= 95
- **AC-9**: Given form rendered, When uso solo teclado (Tab + Enter),
  Then puedo completar todo el flow sin mouse

## 4. Diagrama de Flujo

```text
Usuario carga /contact
    |
    v
ContactForm.astro renderiza (SSG)
    |
    v
contact-form.client.ts hidrata (client:visible)
    |
    v
Turnstile script async defer carga
    |
    v
Widget genera token automatico (Managed mode)
    |
    v
Usuario completa fields
    |
    v
Submit click -> validacion client (email shape, message length)
    |
    +-- invalid -> show inline errors + return
    |
    v
fetch POST /contact con body + cf_token
    |
    +-- 200 -> show success + reset form
    +-- 400 -> show inline validation errors
    +-- 403 -> show "verificacion fallo, recarga"
    +-- 429 -> show "espera X minutos"
    +-- 5XX -> show "error temporal, reintenta"
    +-- network -> show "sin conexion, reintenta"
```

## 5. Diagrama ER

N/A — frontend, sin schema.

## 6. Tests Requeridos

### 6.A. TDD Flows

- WHEN form rendered THEN inputs requeridos presentes [AC-1]
- WHEN submit con valid data THEN fetch llamado con body correcto [AC-2]
- WHEN response 200 THEN UI success state [AC-3]
- WHEN response 429 THEN UI shows retry message + preserves form [AC-4]

### 6.B. Unit Tests (Vitest)

- `tests/unit/components/contact/test_contact_form_client.ts` — logica TS

### 6.D. E2E (Playwright, OBLIGATORIO porque es flujo completo del usuario)

- `tests/feature/contact-form/contact-form.feature` — Gherkin scenarios:
  - Visitante envia form valido (mock Turnstile MOCK_PASS) -> success
  - Visitante envia con rate-limit hit -> retry message
  - Visitante con keyboard-only completa el form

## 7. Archivos Afectados

### Crear

- `packages/ui/src/components/contact/ContactForm.astro`
- `packages/ui/src/components/contact/contact-form.client.ts`
- `packages/ui/src/components/contact/contact-form.types.ts`
- `packages/ui/src/components/contact/contact-form.css`
- `apps/generic/src/pages/contact.astro` — usa ContactForm
- `apps/hub/src/pages/contact.astro` — idem
- `apps/fintech/src/pages/contact.astro`
- `apps/architect/src/pages/contact.astro`
- `apps/leader/src/pages/contact.astro`
- `apps/vibe/src/pages/contact.astro`
- `tests/feature/contact-form/contact-form.feature`
- `tests/feature/contact-form/contact_form_steps.ts`

### Modificar

- `packages/ui/src/index.ts` — export `ContactForm` para uso desde apps
- `packages/ui/package.json` — sin deps nuevas (Turnstile via CDN)
- Cada app `astro.config.ts` — verificar `vite.env` permite
  `PUBLIC_API_ENDPOINT` y `PUBLIC_TURNSTILE_SITEKEY`
- `apps/*/src/env.d.ts` — agregar tipos `ImportMetaEnv.PUBLIC_API_ENDPOINT`

### Env vars (build-time, exposed al cliente con PUBLIC_ prefix)

- `PUBLIC_API_ENDPOINT` — ej. `https://abc123.execute-api.us-east-1.amazonaws.com/prod`
- `PUBLIC_TURNSTILE_SITEKEY` — del widget creado en SPEC-000

## 8. Descomposicion para Paralelizacion

| Task | Archivos | Depende de | Paralelizable con |
|------|----------|------------|-------------------|
| T1 | contact-form.types.ts + contact-form.css | — | T2 |
| T2 | contact-form.client.ts | T1 | T1 |
| T3 | ContactForm.astro | T1, T2 | — |
| T4 | 6 paginas /contact (apps/*) | T3 | T5 |
| T5 | Playwright tests | T3 | T4 |
| T6 | Smoke test E2E contra dev backend | T4, T5 | — |

## 9. Validacion y Definition of Done

### Pre-implementacion

- [ ] SPEC-005 done (Lambda contact_form deployada en stage dev)
- [ ] PUBLIC_API_ENDPOINT + PUBLIC_TURNSTILE_SITEKEY agregados a
      `apps/*/env/*` (gitignored para values reales)

### Definition of Done

- [ ] AC-1 a AC-9 cumplidos
- [ ] Tests Vitest pasan (>= 80% coverage en TS)
- [ ] Tests Playwright pasan en los 6 apps
- [ ] Lighthouse scores AC-8 cumplidos en mobile + desktop
- [ ] Manual testing en Chrome + Firefox + Safari + mobile (iOS/Android)
- [ ] Email del owner recibido en cada test (un total minimo de 6)
- [ ] Sin warnings en consola del browser durante uso normal
