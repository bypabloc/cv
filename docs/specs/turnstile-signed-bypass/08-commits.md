# 08 — Sección 9: commits

[← 07 descomposición](07-descomposicion.md) · [Siguiente: Sección 10 →](09-worktrees.md)

> Conventional Commits en español. Cada commit deja el repo verde y verifica
> lo suyo antes de commitear. Un solo PR `feature/turnstile-signed-bypass -> dev`.

## Rama

`feature/turnstile-signed-bypass` desde `dev` (la rama de api_e2e ya está
mergeada en `dev` — PR #207).

## Secuencia

1. `docs(specs): plan de bypass de Turnstile firmado con Ed25519`
2. `feat(shared): BypassTokenError + subpaquete shared.crypto` (T1+T2)
3. `feat(shared): orquestador captcha-o-bypass en shared.crypto` (T3)
4. `refactor(shared): turnstile httpx-puro + header bypass-token` (T4+T5)
5. `feat(contact_form): bypass Turnstile via token Ed25519 firmado` (T6)
6. `feat(auth): bypass Turnstile via token Ed25519 firmado` (T7)
7. `refactor(tracking_pixel,cv): elimina campo bypass muerto de _meta` (T8+T9)
8. `feat(devtools): keygen Ed25519 + firmante de bypass en api_e2e` (T10+T11)
9. `chore(secrets): publica clave publica de bypass + elimina secreto fijo` (T12)
10. `docs(rules): documenta bypass firmado + portador shared.crypto` (T13)
11. `test(serverless): verificacion E2E del bypass firmado + limpia spec`
    (sección 11 + `git rm -r docs/specs/turnstile-signed-bypass/`)

## Regla por commit

Cada commit corre su `Verify` antes de `git commit`. El push + PR ocurren SOLO
con la batería de la sección 11 completa en verde.

[← 07 descomposición](07-descomposicion.md) · [Siguiente: Sección 10 →](09-worktrees.md)
