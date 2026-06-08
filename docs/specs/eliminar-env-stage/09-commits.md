# 09 — Commits

[← README](README.md)

13 commits atómicos, cada uno deja el repo verde. Un solo PR
`feature/eliminar-env-stage -> dev`.

```
1   docs(specs): plan eliminar-env-stage                          (sin codigo)
2   ci(workflows): flujo de promocion dev -> main directo (quitar stage)   BASE
3   refactor(devtools/serverless): quitar stage de stages validos          BASE
4   refactor(devtools): quitar stage de ai_audit + e2e + sync_secrets      [paralelo]
5   refactor(devtools): quitar stage de docker + bypass_token + package.json [paralelo]
6   refactor(devtools): quitar stage de cloudflare_setup + rotate_secrets   [paralelo]
7   refactor(serverless): api gateway + secrets sin stage                   [paralelo]
8   refactor(serverless): manifests sin seccion stage                       [paralelo]
9   refactor(seo): sitemap/headers sin stage + tests                        [paralelo]
10  chore(docker): eliminar archivos y referencias del entorno stage        (depende 4-9)
11  docs: rules + standard de subdominios a 2 envs (dev + prod)             [paralelo]
12  docs(skills): quitar ejemplos de stage                                  [paralelo]
13  test: verificacion e2e eliminacion de stage + git rm carpeta del plan   (ultimo)
```

- Commits 2-3 son la BASE secuencial (CI/CD + config central de envs).
- Commits 4-12 son paralelizables (archivos disjuntos), salvo el 10 (depende de
  4-9 limpios).
- El commit 13 incluye `git rm -r docs/specs/eliminar-env-stage/`.
- Push + PR SOLO con la Parte A+B de la sección 11 en verde.
