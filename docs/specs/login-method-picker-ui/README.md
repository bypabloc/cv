# Plan: lista selectora de metodos de login (estilo MercadoLibre)

> Plan **Small-Medium** (frontend admin Next.js). Rediseña la UI del checklist
> de login: con 1 metodo `required` muestra su input directo; con >1 muestra una
> LISTA selectora (icono + titulo + descripcion + chevron, estilo MercadoLibre),
> y al elegir uno entra a su input. Al completar un factor vuelve a la lista
> automaticamente. **1 PR** a `dev`. Carpeta efimera: se elimina al mergear.

## 1. Contexto / Problema

El login del admin usa el modelo de "lista de metodos `required`"
(plan login-mfa-list-redesign): `login.check-email` devuelve `methods_required`
y el user completa los factores en cualquier orden. Hoy `LoginChecklist`
(`admin/src/features/auth/components/login-checklist.tsx`) renderiza TODOS los
metodos con su input INLINE a la vez, dentro de cards apiladas. Resultado actual
(Imagen 1 del usuario): con 1 metodo `password`, se ve la card del checklist con
"0 de 1 completados" + el input de contrasena directo — funcional pero pobre como
selector cuando hay varios factores.

El usuario pide la UX de la Imagen 2 (selector de metodo de verificacion estilo
MercadoLibre): una LISTA de filas clickeables (icono + titulo + descripcion +
chevron) cuando hay mas de un metodo; y que con un solo metodo `required` se
muestre directamente ese metodo (su input), sin lista intermedia.

### Hallazgos de exploracion (cerrados)

- `LoginChecklist` recibe `methodsRequired: MethodRequired[]`, `initialTempToken`,
  `email`, `initialPending`. El `tempToken` es ROLLING; `reconcilePending` marca
  satisfechos los metodos que el backend ya no lista en `methods`. El cierre
  ocurre cuando un verify devuelve un `AuthResponse` (`isAuthResponse`).
- Cada input ya soporta modo "checklist" (props `tempToken` + `onResult` +
  `testid`): `LoginPasswordInput`, `LoginTotpInput`, `VerifyCodeInput` (email),
  `WebAuthnLoginButton`, `RecoveryCodeInput`. **No se tocan** — el picker los
  reutiliza tal cual.
- `MethodKind = 'password'|'passwordless'|'totp'|'email_code'|'webauthn'`.
  `MethodRequired.input = 'password'|'code6'|'code8'|'email'|'webauthn'`.
- El backend garantiza `methods_required` con minimo 1 entrada (invariante
  ">=1 required" via fallback passwordless).
- `data-testid="login-checklist"` lo verifica `login-form.test.tsx` (debe
  preservarse en el contenedor raiz de `LoginChecklist`).
- Tests que tocan el checklist: `login-checklist.test.tsx` (6 casos),
  `checklist-input-modes.test.tsx` (modos de input), `login-form.test.tsx` (solo
  el testid del contenedor). lucide-react `^1.17.0` ya integrado en el admin.
- La page `/login` (`(auth)/login/page.tsx`) monta `LoginForm` dentro de
  `max-w-sm`; el `<h1>Iniciar sesion</h1>` vive en la page, NO en el componente.

## 2. Solucion Propuesta

Refactorizar `LoginChecklist` en DOS sub-vistas con una maquina de vista local,
manteniendo intacta toda la logica de tokens/reconciliacion/cierre:

1. **1 metodo `required`** -> render directo del input de ese metodo (como hoy,
   sin la fila selectora). Es el caso de la Imagen 1 pero limpio (sin la card
   "0 de 1").
2. **>1 metodo `required`** -> una vista `MethodPicker` (lista selectora estilo
   MercadoLibre): una fila por metodo con icono + titulo + descripcion + chevron;
   las completadas muestran un check y quedan deshabilitadas (no accionables).
   Al click en una fila pendiente -> sub-vista con el input de ese metodo + un
   boton "Atras" que vuelve a la lista. Al COMPLETAR un factor (verify que rota
   el temp y deja pendientes) -> vuelve a la lista automaticamente. Al completar
   el ULTIMO -> el verify devuelve `AuthResponse` y cierra el login (igual que
   hoy).

El link "Usar codigo de recuperacion" queda SIEMPRE visible abajo (en el input
directo de 1 metodo y en la lista de >1).

### Decisiones clave (confirmadas por el usuario)

- **Decision 1 — volver a la lista automaticamente al completar un factor** +
  boton "Atras" para volver manualmente sin completar. (No avance lineal
  automatico al siguiente input.)
- **Decision 2 — la lista muestra TODOS los `required`** con un check en los
  completados; las filas completadas quedan deshabilitadas (no accionables).
- **Decision 3 — recovery code link siempre visible abajo** (ambos casos).
- **Decision 4 — 1 metodo = input directo** (sin lista intermedia ni fila
  selectora).
- **Decision 5 — NO tocar los inputs ni el backend ni el contrato de tipos**.
  Solo `LoginChecklist` se refactoriza + 1 componente nuevo `LoginMethodPicker`.

## 3. Criterios de Aceptacion (AC)

- **AC-1**: Given `methodsRequired` con 1 entrada (ej. solo `password`), When se
  monta `LoginChecklist`, Then se muestra el input de ese metodo directamente
  (sin filas selectoras ni el texto "0 de N completados") + el link de recovery
  abajo.
- **AC-2**: Given `methodsRequired` con >1 entrada, When se monta, Then se
  muestra una LISTA con una fila por metodo (icono + titulo + descripcion +
  chevron), el contador "0 de N completados", y el link de recovery abajo. NO
  hay ningun input visible todavia.
- **AC-3**: Given la lista (>1) y un metodo pendiente, When click en su fila,
  Then se muestra el input de ese metodo + un boton "Atras".
- **AC-4**: Given la sub-vista de un input (>1) con el boton "Atras", When click
  en "Atras", Then vuelve a la lista SIN haber completado el metodo (sigue
  pendiente).
- **AC-5**: Given >1 metodo y se completa un factor (verify rota el temp y deja
  pendientes), When el verify resuelve, Then vuelve AUTOMATICAMENTE a la lista,
  la fila completada muestra el check y queda deshabilitada, y el contador sube.
- **AC-6**: Given el ULTIMO metodo pendiente (1 input directo, o la sub-vista del
  ultimo en la lista), When el verify devuelve `AuthResponse`, Then setTokens +
  router.replace(dashboard) + toast "Sesion iniciada" (comportamiento actual,
  sin cambios).
- **AC-7**: Given cualquiera de los dos casos, When click en "Usar codigo de
  recuperacion", Then se muestra el `RecoveryCodeInput` (como hoy) y un boton
  "Volver a los metodos".
- **AC-8**: Given un metodo `email_code`/`passwordless` (sin code enviado aun),
  When se entra a su input (lista) o se monta directo (1 metodo), Then aparece el
  boton "Enviar codigo" antes del input del code (comportamiento actual).
- **AC-9**: Given el contenedor raiz de `LoginChecklist`, Then conserva
  `data-testid="login-checklist"` (no rompe `login-form.test.tsx`).

## 4. Diagrama de Flujo (Antes y Despues)

### Antes
```
LoginChecklist:
  [contador "0 de N"]
  for each metodo: card { titulo | input INLINE (todos visibles a la vez) }
  [link recovery]
```

### Despues
```
LoginChecklist:
  required.length == 1 ?
    -> input directo del unico metodo  +  [link recovery]
  : required.length > 1 ?
    -> view == 'list' :
         [contador "C de N"]
         for each metodo: fila { icono | titulo + descripcion | check|chevron }
           (completada => check + disabled ; pendiente => click -> view=metodo)
         [link recovery]
    -> view == <metodo> :
         [boton Atras -> view='list']
         input del metodo (reusa el componente existente)
         (al completar => onResult rota temp, vuelve a view='list' auto;
          al cerrar => AuthResponse => setTokens + replace)
  showRecovery (override de ambos): RecoveryCodeInput + [Volver a los metodos]
```

## 5. Diagrama ER

N/A — no hay cambios en base de datos ni en content collections. Es UI pura del
admin; el contrato de tipos (`MethodKind`, `MethodRequired`, `VerifyResult`) NO
cambia.

## 6. Tests Requeridos — frontend admin (Vitest + Testing Library)

Mirror: `admin/src/features/auth/components/<X>.tsx` ->
`admin/tests/unit/features/auth/components/<X>.test.tsx`.

### 6.B. Unit Tests

- `login-checklist.test.tsx` (EXTENDER, no romper los 6 casos de rolling/cierre):
  - 1 metodo `required` -> input directo, sin filas, sin contador [AC-1].
  - >1 metodo -> lista con filas (icono/titulo/descripcion/chevron) + contador,
    sin input [AC-2].
  - click en una fila pendiente -> aparece su input + boton "Atras" [AC-3].
  - "Atras" -> vuelve a la lista, metodo sigue pendiente [AC-4].
  - completar 1 de 2 -> vuelve a la lista auto, fila con check + disabled,
    contador "1 de 2" [AC-5].
  - completar el ultimo -> replace("/") + setTokens [AC-6] (ya cubierto; adaptar
    a la navegacion lista->input->lista->input).
  - email_code: el boton "Enviar codigo" sigue apareciendo en la sub-vista
    [AC-8].
  - recovery link en ambos casos -> RecoveryCodeInput + "Volver" [AC-7].
  - `data-testid="login-checklist"` presente [AC-9].
- `login-method-picker.test.tsx` (NUEVO, si el picker es un componente separado):
  - renderiza una fila por metodo con su icono/titulo/descripcion.
  - fila completada -> check + `disabled`/no-click.
  - click en fila pendiente -> dispara `onSelect(type)`.
- Asserts EXACTOS, BDD-style en `it()`, coverage >=80% per-file en los archivos
  tocados.

### 6.C. Typecheck / lint

- `pnpm --filter @portfolio/admin typecheck` (tsc + sin `any`).
- `pnpm --filter @portfolio/admin lint` (Biome).

### 6.D. E2E (Playwright Python contra dev)

- `tests/admin/` (modulo `app`/`admin`): los specs de login existentes
  (`test_login_create_and_verify.py`) deben seguir verdes — el flujo de tokens NO
  cambia. NO se agregan specs nuevos (la UI es interna; el contrato API es el
  mismo). Verificacion E2E post-merge solo confirma que el alta+login sigue
  funcionando.

## 7. Archivos Afectados

### Crear
- `admin/src/features/auth/components/login-method-picker.tsx` — la lista
  selectora (icono + titulo + descripcion + chevron por metodo; check en
  completados; `onSelect`). Presentacional puro.
  - Verificar: `pnpm --filter @portfolio/admin exec vitest run tests/unit/features/auth/components/login-method-picker.test.tsx`
- `admin/tests/unit/features/auth/components/login-method-picker.test.tsx` — tests
  del picker.

### Modificar
- `admin/src/features/auth/components/login-checklist.tsx` — maquina de vista:
  1 metodo -> input directo; >1 -> picker + sub-vista de input con "Atras" +
  vuelta-a-lista auto. Conserva `reconcilePending`, `onResult`, el rolling token,
  el cierre `isAuthResponse`, el `data-testid="login-checklist"` y el link de
  recovery.
  - Verificar: `pnpm --filter @portfolio/admin exec vitest run tests/unit/features/auth/components/login-checklist.test.tsx`
  - Verificar: `pnpm --filter @portfolio/admin exec vitest run tests/unit/features/auth/components/login-form.test.tsx`
- `admin/tests/unit/features/auth/components/login-checklist.test.tsx` — extender
  con los casos de las 2 vistas (sin romper rolling/cierre).
- `admin/src/features/auth/index.ts` — exportar `LoginMethodPicker` (barrel) si se
  decide hacerlo publico (opcional; el picker puede quedar interno al feature).

### NO se tocan
- `login-password-input.tsx`, `login-totp-input.tsx`, `verify-code-input.tsx`,
  `webauthn-login-button.tsx`, `recovery-code-input.tsx` — sus modos "checklist"
  ya sirven; el picker los reusa.
- `login-form.tsx` — sigue montando `LoginChecklist` igual (mismas props).
- `types/api.ts`, backend, hooks — sin cambios.

## 8. Descomposicion para Paralelizacion

N/A — cambio atomico de UI (1 componente nuevo + 1 refactor + sus tests). Todo
en `admin/src/features/auth/` + su mirror de tests. Secuencial inline:
picker -> refactor del checklist -> tests. NO fan-out.

## 9. Commits (rama `feature/login-method-picker-ui` desde `dev`)

1. `docs(specs): plan lista selectora de metodos de login`.
2. `feat(auth): LoginMethodPicker (lista selectora de metodos)` — el componente
   nuevo presentacional + sus tests.
3. `feat(auth): el checklist muestra picker con >1 metodo, input directo con 1` —
   refactor de `LoginChecklist` (las 2 vistas) + extension de su test.
4. `test(specs): verificacion E2E + limpieza del plan` (seccion 11 +
   `git rm -r docs/specs/login-method-picker-ui/`).

1 PR `feature/login-method-picker-ui -> dev`. Cada commit deja el repo verde
(lint + typecheck + unit del scope).

## 10. Paralelizacion con git worktrees

N/A — secuencial inline. El picker bloquea el refactor del checklist; el resto es
mecanico.

## 11. Verificacion E2E iterativa (fase final)

**Parte A — refactor de tests**: `login-checklist.test.tsx` cubre las 2 vistas;
`login-form.test.tsx` sigue verde (testid intacto); ningun test referencia un
import inexistente. Barrido `rg -n "login-method-picker|LoginMethodPicker"` ->
solo el componente nuevo + su test + (opcional) el barrel.

**Parte B — bateria local (repo verde)**:
```
pnpm --filter @portfolio/admin lint
pnpm --filter @portfolio/admin typecheck
pnpm --filter @portfolio/admin test:coverage   # >=80% per-file en tocados
pnpm --filter @portfolio/admin build           # export estatico OK
```
Bucle "no parar hasta verde": corregir -> re-ejecutar. Gate de push/PR: A+B verde.

**Parte C — despliegue REAL (post-merge)**: el admin se deploya a Cloudflare
Pages dev (`admin.portfolio.dev.the-full-stack.com`) via `deploy-apps.yml`.
1. Esperar y MIRAR el workflow (cada job, incl. `Verify admin dist`).
2. `curl -fsS` a `https://admin.portfolio.dev.the-full-stack.com/login/` -> 200 +
   marcador (`<title>` o "Iniciar sesion").
3. Smoke manual del flujo: con 1 metodo required -> input directo; con >1 ->
   lista selectora -> elegir uno -> completar -> vuelve a la lista -> completar
   el resto -> entra al shell.
Bucle de correccion identico a la Parte B.

## 12. Validacion y Definition of Done

**Pre-implementacion**:
- [ ] AC-1..9 referenciados por tests.
- [ ] Rama `feature/login-method-picker-ui` desde `dev`.

**Definition of Done**:
- [ ] Todos los AC con test/verificacion + Parte C (deploy real dev).
- [ ] Coverage per-file >=80% en los archivos tocados; sin `any`.
- [ ] lint + typecheck + build limpios.
- [ ] CI verde; PR mergeado a `dev` con `--merge`.
- [ ] Parte C: `/login/` 200 en dev + smoke de las 2 vistas.
- [ ] Carpeta `docs/specs/login-method-picker-ui/` eliminada en el ultimo commit.

## Riesgos / Edge-cases

- **No romper el rolling token**: la logica de `tempToken`/`reconcilePending`/
  `onResult` se MUEVE pero NO cambia. Los tests de rolling/cierre/cualquier-orden
  de `login-checklist.test.tsx` deben seguir verdes (adaptando solo la navegacion
  lista->input).
- **El caso de 1 metodo NO debe mostrar el contador** "0 de 1" (es ruido). Solo
  el input + recovery.
- **`email_code`/`passwordless`**: el boton "Enviar codigo" + `emailCodeSent`
  state se preservan en la sub-vista del input (no en la fila de la lista).
- **`data-testid="login-checklist"`** debe quedar en el contenedor raiz en AMBAS
  vistas (lo verifica `login-form.test.tsx`).
- **Iconos lucide**: usar iconos ya disponibles (`KeyRound`/`Lock` password,
  `Mail` email/passwordless, `Smartphone`/`KeyRound` totp, `Fingerprint`
  passkey, `ChevronRight` chevron, `Check`/`CheckCircle2` completado).
- **Accesibilidad**: las filas son `<button>` (no `<div onClick>`) para foco +
  teclado; las completadas con `disabled` + `aria-disabled`.
