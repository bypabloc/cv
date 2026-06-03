# 07 — Fase E: `tests/app/` (las 6 apps Astro)

[<- 06 modulo admin](06-fase-modulo-admin.md) | [Siguiente: 08 eliminacion ->](08-fase-eliminacion.md)

> Porta smoke + navbar + contact + tracking + screenshots a
> playwright-python contra los subdominios DESPLEGADOS
> `{niche}.portfolio.{env}.the-full-stack.com`. AC-3. La MAYORIA de estos
> specs NO mutan datos (interceptan `/track`, validan UI client-side), asi
> que funcionan contra dev/stage sin riesgo. Requiere el container `e2e`.

## E.1 — Archivos (porta de `tests/feature/{smoke,navbar,contact,tracking}`)

| Archivo | Porta de | Cobertura | Browser? |
|---------|----------|-----------|----------|
| `tests/app/conftest.py` | fixtures index.ts | `browser`, `page`, `subdomain` helper (URLs desplegadas) | — |
| `tests/app/test_smoke.py` | smoke/smoke.spec | 6 subdominios `/` -> 2xx + body/h1 visible | si |
| `tests/app/test_hub_links.py` | smoke/hub-links.spec | hub cards -> hrefs env-driven, click fintech -> 2xx | si |
| `tests/app/test_cv_filters.py` | smoke/cv-filters.spec | `?tech=` filtra en 5 apps, chip/clear, JS-disabled fallback, /cv-filters.js bundle | si |
| `tests/app/test_navbar.py` | navbar/navbar-breakpoints.spec | dropdown desktop, drawer mobile, breakpoint 1280->375, ARIA/focus | si |
| `tests/app/test_contact_form.py` | contact/contact-form.spec | form Zod validation, localStorage persist, resend | si |
| `tests/app/test_contact_funnel.py` | contact/contact-funnel.spec | CONTACT_VIEW + CONTACT_FORM_START (route intercept) | si |
| `tests/app/test_tracking_pageload.py` | tracking/track-pageload.spec | always-on en 6 apps, no banner, SPA re-trigger | si |
| `tests/app/test_tracking_payload.py` | tracking/track-payload-fields.spec | payload 16 campos, utm, viewport (route intercept) | si |
| `tests/app/test_screenshots.py` | smoke/cv-screenshots.spec | 3 viewports x 6 apps -> PNG en tests/results/ | si |

## E.2 — Helpers de browser reutilizados (de `tests/shared/browser.py`)

- `disable_send_beacon(page)` — para que playwright lea el `postData` de
  `/track` (los tests de tracking/funnel dependen de esto).
- `capture_track(page)` — `page.route('**/track')` acumulando payloads.
- `subdomain(niche)` — URL desplegada del niche (de `shared/config.py`).
- `screenshot(page, path, full_page)` — para `test_screenshots`.

## E.3 — Ajustes por correr contra DESPLEGADO (no local)

- URLs: `{niche}.portfolio.{env}.the-full-stack.com` en vez de
  `{niche}.localhost:9970`. El helper `subdomain()` lo resuelve por env.
- `services.localhost` (smoke viejo) NO tiene equivalente desplegado ->
  ese sub-caso se DESCARTA (anotar en el test) o se reemplaza por un check
  del apex/hub.
- `cv-filters.js` y assets: validar la ruta del bundle en la URL desplegada
  (puede diferir del path local).
- Tracking REAL: los tests interceptan `/track` con `route`, asi que NO
  mutan datos del backend desplegado (responden 204 localmente). Confirmar
  que ningun test de `app` escriba tracking real (si alguno deja pasar el
  request, registrar el session_id para cleanup — pero el patron intercept
  evita esto).

## E.4 — Screenshots (AC-3, decision: portar)

`test_screenshots.py`: loop 3 viewports (mobile 375x812, tablet 768x1024,
desktop 1280x800) x 6 apps, 3 capturas (hero/mid/bottom). Salida en
`tests/results/<niche>/<viewport>/*.png` (gitignored). Verifica ademas que
no hay scroll horizontal (`scrollWidth <= clientWidth + 1`). Es lento (~54
PNG): correr solo chromium (como el TS).

## E.5 — No requiere auth dura

`--module=app` NO exige SSO ni clave bypass (no muta, no autentica). Corre
con solo el container `e2e` + salida a internet. (AC-6: app es la excepcion
al fail-duro.)

## Verificacion de la fase E

```bash
python devtools/run.py e2e --module=app --env=dev
# screenshots generados:
ls tests/results/fintech/desktop/*.png
```

## Done de la fase E

- [ ] smoke (6 apps) + hub-links + cv-filters portados.
- [ ] navbar responsive (dropdown/drawer/breakpoint/ARIA) portado.
- [ ] contact (validation + funnel) portado con route intercept.
- [ ] tracking (pageload + payload) portado con route intercept.
- [ ] screenshots (3 viewports x 6 apps) generan PNG en tests/results/.
- [ ] `e2e --module=app --env=dev` exit 0 con PASS.
- [ ] Ningun test de `app` muta datos del backend desplegado.

[<- 06 modulo admin](06-fase-modulo-admin.md) | [Siguiente: 08 eliminacion ->](08-fase-eliminacion.md)
