# 05 — Admin: tabs de /settings + fix display_name + sesiones

[← analytics](04-backend-analytics.md) · [Siguiente: panel seguridad →](06-admin-security-panel.md)

> Cubre AC-8, AC-9, AC-10, AC-11. Solo frontend admin.

## Estado actual

- `/settings/page.tsx`: Tabs `Perfil | Cuenta` (no security, no sessions).
- `/settings/security/page.tsx`: page independiente con el panel.
- `/sessions/page.tsx`: page independiente (sesiones). Muestra `user_id`,
  `status`, `current_session_id` — vacíos porque `status.get` no los daba
  (fase 3 lo arregla en backend).
- Sidebar (`admin-shell/lib/nav-items.ts`): items separados "Configuración"
  (`/settings`), "Seguridad" (`/settings/security`), "Mis sesiones"
  (`/sessions`).
- `profile-form.tsx`: el `useEffect(reset(...))` con `profile.data` en deps
  RE-RESETEA el form en cada render (Tanstack devuelve nueva referencia) →
  pisa lo que el usuario tipea en "Nombre para mostrar".

## Solución

### AC-8 / AC-9 — 3 tabs, rutas reales (D-1)

Layout de tabs compartido en `/settings` con 3 tabs que son **rutas reales**:
`/settings` (Perfil y cuenta), `/settings/security` (Seguridad),
`/settings/sessions` (Sesiones).

Patrón Next App Router (export estático): un `(admin)/settings/layout.tsx`
que renderiza la `<TabsList>` (links a las 3 rutas, tab activo según
`usePathname()`), y cada `page.tsx` renderiza su `<TabsContent>`. Como es
SPA estático con client routing, los tabs navegan con `<Link>` sin recargar.

```
admin/src/app/(admin)/settings/
├── layout.tsx          # NUEVO: header "Configuración" + TabsList (3 links,
│                       #        activo por usePathname) + {children}
├── page.tsx            # Tab Perfil y cuenta (ProfileForm + ChangeEmail +
│                       #   ConfirmEmailChange + DeleteAccountSection)
├── security/page.tsx   # Tab Seguridad (SecurityOverviewPanel) — ya existe
└── sessions/page.tsx   # NUEVO: Tab Sesiones (mueve el contenido de /sessions)
```

- Mover el contenido de `(admin)/sessions/page.tsx` a
  `(admin)/settings/sessions/page.tsx`.
- `(admin)/sessions/page.tsx`: o se elimina, o se deja como redirect a
  `/settings/sessions` (Next `redirect()` no aplica en export; usar un
  componente client que `router.replace('/settings/sessions')`). Preferir
  ELIMINAR + actualizar el sidebar (AC-9).
- Unificar el tab "Cuenta" (delete-account) dentro del tab "Perfil y cuenta"
  o como su propio sub-bloque — el usuario pidió "Perfil y cuenta" como un
  tab; mantener delete-account ahí.

Sidebar (`nav-items.ts`): quitar los items "Seguridad" y "Mis sesiones"
separados (los tabs los cubren). Dejar "Configuración" → `/settings`. El
plan `b-analytics-api` ya removió/agregó items; ajustar el conteo en los
tests del sidebar.

### AC-10 — vista de sesiones con datos

El tab Sesiones consume `useAccountStatus()` (`status.get`). Tras la fase 3,
`status.get` devuelve `current_session_id` → la vista muestra `user_id`,
`status`, `current_session_id` no vacíos. El tipo `AccountStatus`
(`types/models.ts`) ya tiene los 3 campos; confirmar que el cliente
desempaqueta bien la respuesta.

### AC-11 — fix "Nombre para mostrar" editable

El `useEffect` que hace `reset({ display_name })` se dispara en cada render
porque `profile.data` cambia de referencia → pisa el input. Fix: resetear
solo cuando el VALOR cambia (no la referencia), o usar el patrón `values` de
react-hook-form (que sincroniza sin pisar ediciones del usuario).

```tsx
// profile-form.tsx — opción A (preferida): inicializar el form con values
// una vez, con un guard de "ya inicializado":
const initialized = useRef(false);
useEffect(() => {
  if (profile.data && !initialized.current) {
    reset({ display_name: profile.data.display_name ?? "" });
    initialized.current = true;
  }
}, [profile.data, reset]);

// opción B: no usar reset en effect; pasar defaultValues derivados con
// `key={profile.data?.id}` en el form para remount limpio una vez.
```

Test: el input acepta texto tras la carga (el reset no lo pisa) + submit
envía el valor tipeado.

## 7. Archivos afectados (fase 5)

### Crear
- `admin/src/app/(admin)/settings/layout.tsx` — TabsList con 3 links
  (Perfil y cuenta | Seguridad | Sesiones), activo por `usePathname`.
- `admin/src/app/(admin)/settings/sessions/page.tsx` — tab Sesiones (mueve el
  contenido de `(admin)/sessions/page.tsx`).
- `admin/tests/unit/app/(admin)/settings/layout.test.tsx` — los 3 tabs
  renderizan + el activo según pathname. [AC-8]
- `admin/tests/unit/features/settings/components/profile-form-editable.test.tsx`
  — el campo display_name acepta texto sin ser pisado por el reset. [AC-11]

### Modificar
- `admin/src/app/(admin)/settings/page.tsx` — quitar su propio `<Tabs>`
  interno (ahora el layout tiene los tabs); renderizar solo el contenido de
  "Perfil y cuenta" (Profile + ChangeEmail + Confirm + DeleteAccount).
  - Verificar: `pnpm --filter @portfolio/admin build`.
- `admin/src/app/(admin)/settings/security/page.tsx` — adaptar a renderizar
  bajo el layout de tabs (sin su propio header duplicado).
- `admin/src/features/settings/components/profile-form.tsx` — fix del reset
  (AC-11).
  - Verificar: `pnpm --filter @portfolio/admin test`.
- `admin/src/features/admin-shell/lib/nav-items.ts` — quitar items separados
  "Seguridad" y "Mis sesiones"; dejar "Configuración" → `/settings`.
  - Verificar: tests del sidebar (ajustar conteo + hrefs).
- `admin/tests/unit/features/admin-shell/...` (use-nav-items, sidebar,
  mobile-sidebar) — ajustar conteo de items + hrefs esperados. [AC-9]
- `admin/src/features/sessions-mgmt/...` — confirmar que el cliente y el tipo
  `AccountStatus` exponen `current_session_id` tras el backend (fase 3).

### Eliminar
- `admin/src/app/(admin)/sessions/page.tsx` — su contenido se movió al tab.
  Si hay E2E/tests que apuntan a `/sessions`, redirigir o actualizar a
  `/settings/sessions`.

## Verificación (fase 5)

```bash
pnpm --filter @portfolio/admin lint
pnpm --filter @portfolio/admin typecheck
pnpm --filter @portfolio/admin test
pnpm --filter @portfolio/admin build
```

Parte C (dev real): `/settings`, `/settings/security`, `/settings/sessions`
→ 200 con tab activo; "Nombre para mostrar" editable; sesiones con
`current_session_id`. [AC-8, AC-10, AC-11]

[← analytics](04-backend-analytics.md) · [Siguiente: panel seguridad →](06-admin-security-panel.md)
