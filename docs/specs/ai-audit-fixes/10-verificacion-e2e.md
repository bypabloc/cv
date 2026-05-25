# 10 - Verificacion E2E + cierre

[< 09 Worktrees](09-paralelizacion-worktrees.md) | [README](README.md)

Fase de cierre. Es el ULTIMO commit del plan. Incluye:

- Refactor de tests (Parte A)
- Bateria de verificacion (Parte B) — bucle "no parar hasta verde"
- Re-correr `ai_audit` y comparar contra baseline
- Eliminar `docs/specs/ai-audit-fixes/` (carpeta efimera)
- Push + crear PR a `dev`

## Parte A - Refactor de tests

Verificar que:

1. Ningun test viejo referencia archivos eliminados.
2. Coverage >= 80% en archivos modificados.
3. Barrido global:
   ```bash
   rg -l "ahrefs|semrush|aibotchecker" devtools/tests/ packages/*/tests/
   ```
   (debe estar vacio — ya eliminados en commit anterior).

## Parte B - Bateria de verificacion (bucle no-parar-hasta-verde)

Ejecutar en orden. Si UNO falla: corregir y re-correr la suite completa.

```bash
# 1. Lint
pnpm exec biome check .

# 2. Typecheck
pnpm exec tsc --noEmit
pnpm exec astro check

# 3. Tests unit packages
pnpm exec vitest run

# 4. Tests unit devtools
python devtools/run.py test_runner --module=devtools --type=unit
# esperado: 789+ tests verde (785 base + ~4 nuevos)

# 5. Build estatico de los 6 sites
pnpm run build

# 6. Coverage threshold
pnpm exec vitest run --coverage
# verificar >= 80% per-file en archivos modificados

# 7. (post-deploy) Smoke audit
python devtools/run.py ai_audit
# esperado: avg >= 85 (baseline era 63)

# 8. (post-deploy) Headers
curl -I https://the-full-stack.com/ | grep -i ^link
# esperado: 3 lineas Link

# 9. (post-deploy) Sitemap alias
curl -I https://the-full-stack.com/sitemap.xml | grep -i location
# esperado: location: /sitemap-index.xml (HTTP 301)

# 10. (post-deploy) API catalog
curl -sS https://the-full-stack.com/.well-known/api-catalog | jq .
# esperado: JSON valido shape {linkset: [...]}

# 11. (post-deploy) WebSite JSON-LD
curl -sS https://the-full-stack.com/ | grep -o '"@type":"WebSite"'
# esperado: 1 match
```

Si pasan TODOS, continuar al cierre.

## Cierre del plan

### Eliminar carpeta del plan

```bash
git rm -r docs/specs/ai-audit-fixes/
```

### Commit final

```text
chore(specs): cierra plan ai-audit-fixes

- bateria E2E completa en verde:
  * 789+ tests devtools
  * pnpm build los 6 verde
  * ai_audit post-deploy avg 85+/100
  * todos los headers Link + sitemap alias + api-catalog OK
- elimina docs/specs/ai-audit-fixes/ (carpeta efimera del plan)
```

### Push

```bash
git push  # rama ya tracked
```

### PR a dev

```bash
gh pr create --base dev --head feature/ai-audit-devtools \
  --title "feat(ai-audit): mejoras readiness IA + SEO (validators 100, lighthouse 100, +3 builders seo)" \
  --body "$(cat docs/specs/ai-audit-fixes/08-commits.md | sed -n '/^## PR/,$p')"
```

(Body se construye desde 08-commits.md ANTES de hacer el `git rm`.)

Despues:

```bash
gh pr view --web   # link al PR
```

## Regla de cierre

NO declarar el plan completo hasta que:

- [ ] La bateria de la Parte B pasa COMPLETA en verde
- [ ] La carpeta del plan esta eliminada (`docs/specs/ai-audit-fixes/`)
- [ ] El push + PR estan creados
- [ ] El audit post-deploy confirma avg >= 85

[< 09 Worktrees](09-paralelizacion-worktrees.md) | [README](README.md)
