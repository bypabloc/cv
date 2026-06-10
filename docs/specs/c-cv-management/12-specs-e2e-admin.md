# 12 — Specs E2E browser del admin (`tests/admin/`) — detalle completo

> playwright-python contra `admin.portfolio.dev.the-full-stack.com`
> (`e2e --module=admin --env=dev`). Un archivo = un escenario. Flujos
> COMPLETOS de cada interfaz: login real → navegar → llenar TODOS los
> campos → guardar → verificar → recargar → editar → eliminar → cleanup.
> [Volver al README](README.md).

## Convenciones del modulo (aplican a todos los specs)

- Login REAL con el user admin sintetico promovido a whitelist (mismas
  fixtures del modulo admin existente + `cv_admin_session` del doc 11).
- Selectores SOLO por `data-testid` estable (la Fase 3 los define en cada
  componente interactivo); NUNCA por texto visible.
- Anti-flake: `wait_for_load_state('networkidle')` antes de interactuar
  con islands/forms hidratados; reintento del evento si el handler no
  monto (patron de la rule e2e-testing).
- Captura de errores de consola en cada page: al final de cada spec,
  assert `console_errors == []`.
- Datos: slugs sinteticos `e2e-cvadm-ui-<rand>`; teardown via API
  (`delete-<entidad>`) idempotente registrado en el conftest del modulo.
- El dispatch REAL de publish NO se ejecuta desde browser (lo cubre la
  capa API): el spec de publish intercepta `POST /cv-admin` con
  `page.route` (patron `/track` del modulo app).

## `test_cv_navigation_all_sections.py`

1. Login → goto `/cv` → overview renderiza.
2. Assert: 10 cards de seccion visibles (`data-testid=cv-section-card-*`)
   y el conteo numerico de cada card == el largo de la seccion en
   `cv_get('<seccion>')` (consulta API en el arrange; asserts `==`).
3. `publish-card` visible con boton habilitado.
4. Navegar a CADA sub-ruta (10): `/cv/profile`, `/cv/experiences`,
   `/cv/projects`, `/cv/education`, `/cv/certificates`, `/cv/awards`,
   `/cv/languages`, `/cv/endorsements`, `/cv/publications`, `/cv/skills`.
   En cada una: el sub-nav marca la seccion activa, la lista renderiza N
   items == al GET correspondiente, sin skeleton residual tras
   networkidle.
5. Assert final: cero errores de consola acumulados en todo el recorrido.

## `test_cv_overview_publish_ui.py`

1. Login → `/cv` → interceptar con `page.route` el `POST /cv-admin` cuyo
   body tenga `operation == 'publish'`: responder 200 local
   `{is_valid: true, code: 0, data: {url: '<fake-run-url>'}}` y CAPTURAR
   el request.
2. Click `cv-publish-button` → AlertDialog visible: titulo y descripcion
   esperados (avisa que dispara un deploy de las 6 apps del env).
3. Click cancelar → dialog cierra, NINGUN request capturado.
4. Click publicar → confirmar → assert del request capturado:
   `{operation:'publish', action:'dispatch'}` con Bearer presente.
5. Toast de exito visible + link "Ver en Actions" con `href` == la url
   devuelta.
6. `publish-status` re-consulta (`action:'status'` tambien interceptada):
   la card muestra estado `queued` con timestamp. Cero console errors.

## `test_cv_experience_create_edit_delete_flow.py` (flujo completo, sin atajos)

1. Login → `/cv/experiences` → snapshot del conteo inicial de cards.
2. Click `cv-entity-new` → form/dialog abre vacio (assert: inputs vacios,
   submit deshabilitado o validacion activa).
3. Llenar TODOS los campos:
   - `role` es y en (inputs lado a lado `bilang-field`),
   - company, country, companyUrl,
   - start `2024-01`, end `2025-06` (y assert del formato aceptado),
   - seniority via Select → `senior`,
   - toggle metricsEstimated ON,
   - bullets responsibilities: agregar 2 items es/en
     (`bilang-list-editor`), bullets achievements: agregar 2 items es/en,
   - reordenar: subir el achievement[1] a posicion 0 (boton
     `bilang-item-up`) → assert orden visual,
   - eliminar el responsibility[1] → assert queda 1,
   - skillsTechnical: tag-input → seleccionar 2 sugerencias del catalogo
     (autocomplete visible con datos reales) + crear 1 nueva
     (`E2E Skill <rand>`),
   - skillsSoft: 1 del catalogo,
   - niches: checkbox `generic` ON + priority input = 5; checkbox `vibe`
     ON + priority = 3 (`niche-priority-picker`).
4. Guardar → toast exito → dialog cierra → card nueva visible con role
   es, company y rango de fechas exactos; badges `generic` y `vibe`.
5. `page.reload()` → la card persiste (conteo == inicial + 1).
6. Reabrir editar → HIDRATACION EXACTA: assert valor por valor de CADA
   campo del paso 3 (es y en, orden de bullets, tags, niches, priorities).
7. Mutar: role.en nuevo; agregar 1 responsibility al inicio; quitar la
   skill creada; desmarcar niche `vibe` → guardar → toast.
8. Verificar: reabrir → mutaciones exactas; GET
   `experiences?niche=vibe` (API) ya NO la incluye;
   `experiences?niche=generic` SI, con bullets en el orden final.
9. Eliminar: menu de la card → "Eliminar" → AlertDialog → confirmar →
   card desaparece → reload → ausente (conteo == inicial).
10. Teardown: delete API idempotente del slug + cero console errors.

## `test_cv_project_create_edit_delete_flow.py`

Mismos 10 pasos con los campos de proyecto:

- name, url, repo, links: agregar 2 pares {label, url} (editor de lista),
- status Select `active`, projectType Select `web`, toggles
  isConfidential OFF / metricsEstimated ON,
- description es/en,
- metrics: 2 pares {key, value} ordenados + reorder (subir metric[1]),
- stack: tag-input con 3 tech-tags (2 existentes + 1 nuevo),
- caseStudy: problem/process/result es y en (6 textareas),
- niches `generic` + priority 4.

Mutaciones (paso 7): metric nueva al inicio, eliminar un link, cambiar
status → `inactive`, caseStudy.result.en. Asserts API espejo (paso 8):
GET `projects` refleja metrics en orden, stack sin duplicados, case study
completo.

## `test_cv_profile_edit_flow.py` (singleton — restore obligatorio)

1. SNAPSHOT API: `cv_get('profile')` completo.
2. Login → `/cv/profile` → form hidratado con los valores actuales
   (assert contra el snapshot, campo a campo).
3. Editar: headline.es, summary.en, location, stats.years (+1) con
   marcadores `E2E-CVADM-UI`.
4. Guardar → toast → reload → persiste (asserts exactos).
5. RESTORE por UI: re-editar con los valores del snapshot → guardar.
6. Verificar restauracion: GET API == snapshot original. Restore ademas
   en teardown `finally` via `upsert-profile` API por si el spec muere.

## `test_cv_reorder_ui_flow.py`

1. ARRANGE via API: crear 3 experiencias sinteticas (priorities 1,2,3 en
   `generic`).
2. Login → `/cv/experiences` → selector de niche = `generic` → las 3
   sinteticas visibles al final de la lista (orden por prioridad desc del
   resto intacto).
3. Snapshot del orden DOM completo (`data-testid=cv-entity-card` ids).
4. Boton `cv-entity-move-up` de la sintetica #3 dos veces → assert orden
   DOM tras cada click (optimistic o tras respuesta — definir en Fase 3 y
   assertear el definitivo).
5. Reload → orden persiste; GET API `experiences?niche=generic` →
   posiciones relativas == DOM.
6. Cambiar selector a niche `vibe` → las sinteticas NO aparecen (no
   asignadas) y el orden de `vibe` no cambio.
7. RESTORE: orden original via boton move-down / API reorder con el
   snapshot → verificar == paso 3. Teardown: delete de las 3.

## Secciones simples — un spec por interfaz (mismos 10 pasos del flujo de experiencia, con sus campos)

| Spec | Campos completos del form |
|------|---------------------------|
| `test_cv_education_create_edit_delete_flow.py` | institution, degree es/en, description es/en, start, end, url, niches+priority |
| `test_cv_certificate_create_edit_delete_flow.py` | title, issuer, date, url, niches+priority |
| `test_cv_award_create_edit_delete_flow.py` | issuer, date, url, title es/en, motivation es/en, niches+priority |
| `test_cv_language_create_edit_delete_flow.py` | name es/en, level es/en, niches |
| `test_cv_endorsement_create_edit_delete_flow.py` | name, role, company, linkedin, relation es/en, niches |
| `test_cv_publication_create_edit_delete_flow.py` | title, platform, url, canonicalUrl, date, niches |
| `test_cv_skill_category_create_edit_delete_flow.py` | name es/en, kind Select, skills tag-input ordenado (3, con reorder interno), niches |

Cada uno DEBE incluir: hidratacion exacta al reabrir (paso 6), una
mutacion es + una en (paso 7), verificacion API espejo (paso 8), delete
con confirmacion + reload (paso 9), teardown idempotente.

## `test_cv_bilang_validation_ui.py`

1. `/cv/experiences` → nueva → submit con todo vacio → FormMessage del
   primer campo requerido visible (texto exacto del Zod schema); el
   dialog NO cierra; NINGUN request POST salio (interceptor de espia).
2. role.es lleno y role.en vacio → error especifico del par BiLang
   (regla de la Fase 3: ambos locales requeridos en campos BiLang).
3. Fecha `2026-13` → error de formato exacto.
4. Corregir todo → submit habilitado y guardado OK (cleanup).

## `test_cv_non_admin_hidden.py`

1. Login con user sintetico activo NO whitelisted.
2. Sidebar NO contiene el item "Gestion CV" (`data-testid` del nav).
3. `goto /cv` directo → pantalla de no autorizado (mismo tratamiento que
   `users-admin` ante 404: NO redirect a login, NO crash).
4. `goto /cv/experiences` directo → idem. Cero console errors.

## Cobertura AC de esta capa

| AC | Specs |
|----|-------|
| AC-5 | reorder_ui_flow |
| AC-6 | experience/project/profile/secciones simples + bilang_validation |
| AC-7 (UI) | overview_publish_ui (dispatch real: capa API) |
| AC-13 | non_admin_hidden |
| Navegacion/consistencia | navigation_all_sections |
