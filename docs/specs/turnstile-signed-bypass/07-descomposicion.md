# 07 — Sección 8: descomposición para paralelización

[← 06 secrets/docs](06-fase-secrets-docs.md) · [Siguiente: Sección 9 →](08-commits.md)

> Tareas atómicas. Orquestación según
> [orchestration.md](../../../.claude/rules/orchestration.md): trabajo
> determinista (tests/lint) en Bash; olas de <=4 agentes si se paraleliza.

| # | Tarea | Archivos | AC | Depende de | Verify |
|---|-------|----------|----|-----------|--------|
| T1 | `BypassTokenError` | `shared/core/exceptions.py` | AC-3 | — | tests shared |
| T2 | `shared.crypto` (ed25519+bypass_token+pyproject+tests) | `shared/crypto/**`, tests | AC-2..5,13 | T1 | `tests --shared` |
| T3 | Orquestador `captcha.py` + tests | `shared/crypto/captcha.py`, tests | AC-1,2,3 | T2 | `tests --shared` |
| T4 | turnstile httpx-puro | `shared/http/turnstile.py` + test | AC-12 | T3 | `tests --shared` |
| T5 | Transporte header/`_meta` | `shared/lambda_kit/http_dispatch.py`, `shared/http/cors.py`, test | — | T3 | `tests --shared` |
| T6 | Wiring `contact_form` | `services/contact_form/**` | AC-1,2 | T3,T5 | `tests --lambda=contact_form` |
| T7 | Wiring `auth` | `services/auth/**` | AC-1,2 | T3,T5 | `tests --lambda=auth` |
| T8 | Limpieza `tracking_pixel` | `services/tracking_pixel/**` | AC-10,12 | T5 | `tests --lambda=tracking_pixel` |
| T9 | Limpieza `cv` | `services/cv/**` | AC-10,12 | T5 | `tests --lambda=cv` |
| T10 | devtools keygen | `devtools/rotate_secrets/**` | AC-7 | T2 | keygen --dry-run |
| T11 | devtools firmante api_e2e + mint | `devtools/api_e2e/**` | AC-8,9 | T2,T5 | `api_e2e mint-bypass` |
| T12 | Secrets/SSM + borrado viejo | `resources/secrets/**`, `docker/env/server/.example` | AC-11 | T6,T7 | `rg` vacío |
| T13 | Docs/rules | `.claude/rules/*`, READMEs | AC-11,12 | T4,T6,T7 | `claude -p` |

Base secuencial: **T1 → T2 → T3 → T4/T5**. Fan-out posible: T6–T9 (archivos
disjuntos por Lambda). Verificación SIEMPRE en Bash, nunca 1 agente por suite.

[← 06 secrets/docs](06-fase-secrets-docs.md) · [Siguiente: Sección 9 →](08-commits.md)
