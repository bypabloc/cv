# 08 — Descomposición, commits y paralelización

[← metrics](07-admin-metrics.md) · [Siguiente: verificación E2E →](09-verificacion-e2e.md)

## 8. Descomposición para paralelización

Las fases tocan archivos disjuntos por capa. Backend (fases 2-4) y admin
(fases 5-7) son worktree-safe entre sí (carpetas distintas). PERO el orden
importa: el admin consume las APIs del backend, así que el backend se
implementa primero (aunque el deploy real es Parte C, el contrato y los
tipos se definen en backend).

Granularidad: 9 tareas (T1..T9). Cada una con archivos exclusivos.

| Tarea | Fase | Archivos | Depende de | Paralelizable con | Verify |
|-------|------|----------|------------|-------------------|--------|
| T1 TOTP | 2 | `auth/.../mfa/confirm_totp.py`, `totp_service.py`, `shared/auth/totp.py`, test roundtrip | base | T2,T3 | `serverless tests --lambda=auth` |
| T2 users | 3 | `users/.../profile/get.py`, `status/get.py`, tests | base | T1,T3 | `serverless tests --lambda=users` |
| T3 analytics | 4 | `analytics/.../models/_common.py`, `analytics.py`, tests | base | T1,T2 | `serverless tests --lambda=analytics` |
| T4 settings tabs | 5 | `(admin)/settings/{layout,page,security/page,sessions/page}.tsx`, `profile-form.tsx`, `nav-items.ts`, tests | T2 (status) | T5 parcial | `admin test+build` |
| T5 security panel | 6 | `security-overview-panel.tsx`, `change-password-form.tsx`, `validation.ts`, tipos, tests | T1,T2 | T4 (archivos distintos salvo tipos) | `admin test+build` |
| T6 metrics | 7 | `analytics/components/*`, `hooks/*`, `metrics/page.tsx`, `MetricsRangePicker`, tests | T3 | T4,T5 | `admin test+build` |
| T7 dead code | 6 | eliminar webauthn-credentials-list, mfa-methods-list, email-code-section | T5 | — | `admin build` |

> Por el CAP de concurrencia (orchestration.md: <=4 agentes, 1 workflow a la
> vez) y porque varias tareas comparten `admin/src/types/models.ts` y el
> `index.ts` de settings, NO se usan worktrees: se ejecuta SECUENCIAL inline
> en el orden de commits. Los tests corren en Bash/devtools, NO en agentes
> (regla: no 1 agente LLM por suite determinística).

## 9. Commits (rama `feature/admin-account-fixes-metrics` desde `dev`)

Cada commit deja el repo verde (lint + typecheck + tests del scope). Orden:
backend primero (contrato), luego admin.

1. `docs(specs): plan fixes de cuenta/seguridad admin + /metrics` — crea la
   carpeta del plan.
2. `fix(auth): tolera el clock-drift al confirmar TOTP + test round-trip` —
   T1 (fase 2). [AC-1, AC-2]
3. `feat(users): expone has_password en profile.get y current_session_id en status.get` —
   T2 (fase 3). [AC-5, AC-6, AC-7]
4. `feat(analytics): acepta from/to datetime y bucket minute/hour` — T3
   (fase 4). [AC-3, AC-4]
5. `fix(admin): unifica settings en tabs Perfil/Seguridad/Sesiones + fix display_name` —
   T4 (fase 5). [AC-8, AC-9, AC-10, AC-11]
6. `feat(admin): registro de passkey, set-password condicional y quita email-code del panel` —
   T5 + T7 (fase 6). [AC-12, AC-13, AC-14, AC-15]
7. `fix(admin): arregla la grafica de timeseries, retencion y selector de rango CloudWatch sin polling` —
   T6 (fase 7). [AC-16..AC-20]
8. `test(specs): verificacion E2E + limpieza del plan` — fase 9 + `git rm -r
   docs/specs/admin-account-fixes-metrics/`.

Si el diagnóstico de AC-14 confirma que `users.change-password` necesita
permitir el primer set sin `current_password`, ese cambio backend va en el
commit 3 (users) y la UI lo consume en el commit 6.

Un solo PR `feature/admin-account-fixes-metrics -> dev`.

## 10. Paralelización con git worktrees

N/A — secuencial. Aunque backend y admin son carpetas disjuntas, el plan se
ejecuta inline en el orden de commits (las tareas admin comparten
`types/models.ts` y `settings/index.ts`, y el CAP de concurrencia no amerita
worktrees para 7 tareas). La verificación E2E (fase 9) NO se paraleliza.

[← metrics](07-admin-metrics.md) · [Siguiente: verificación E2E →](09-verificacion-e2e.md)
