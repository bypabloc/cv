# Fase G — Commit comment con resumen del deploy

> Al final de cada workflow `deploy-backend.yml` y `deploy-apps.yml`,
> postear un comment en el commit con: que se deployo, URLs, duracion,
> resultados. Visible en `https://github.com/bypabloc/cv/commit/<sha>`.

## Contexto / Problema

Hoy el operador inspecciona los runs de GitHub Actions individualmente
para ver que paso. Falta un solo lugar consolidado por commit.

GitHub commit comments son markdown, soportan tablas, links a CloudWatch
y a Cloudflare Pages, persisten al lado del commit.

## Solucion

### G.1 — Job `report` en cada workflow

Job final en `deploy-backend.yml`:

```yaml
  report:
    name: Report deploy summary
    needs: [resolve-env, migrate-db, detect-changes, deploy-lambdas]
    if: always()
    runs-on: ubuntu-24.04
    steps:
      - uses: actions/checkout@v4

      - name: Build report body
        id: build-report
        run: |
          stage="${{ needs.resolve-env.outputs.stage }}"
          affected='${{ needs.detect-changes.outputs.affected }}'
          migrate_result='${{ needs.migrate-db.result }}'
          deploy_result='${{ needs.deploy-lambdas.result }}'

          {
            echo "## Backend deploy report — \`${stage}\`"
            echo
            echo "| Step | Result |"
            echo "|------|--------|"
            echo "| Migrations | ${migrate_result} |"
            echo "| Lambdas affected | \`${affected}\` |"
            echo "| Lambdas deploy | ${deploy_result} |"
            echo
            echo "Workflow: [run #${{ github.run_id }}](${{ github.server_url }}/${{ github.repository }}/actions/runs/${{ github.run_id }})"
          } > /tmp/body.md
          {
            echo "body<<EOF"
            cat /tmp/body.md
            echo "EOF"
          } >> "$GITHUB_OUTPUT"

      - name: Post commit comment
        uses: peter-evans/commit-comment@v3
        with:
          sha: ${{ github.sha }}
          body: ${{ steps.build-report.outputs.body }}
```

Job final en `deploy-apps.yml`:

```yaml
  report:
    name: Report apps deploy summary
    needs: [resolve-env, deploy-pages]
    if: always()
    runs-on: ubuntu-24.04
    steps:
      - uses: actions/checkout@v4

      - name: Build report body
        id: build-report
        run: |
          stage="${{ needs.resolve-env.outputs.stage }}"
          suffix="${{ needs.resolve-env.outputs.project-suffix }}"
          deploy_result='${{ needs.deploy-pages.result }}'

          # URLs canonicas por env. main -> sin etiqueta de env.
          if [[ "$stage" == "prod" ]]; then
            generic_url="https://the-full-stack.com"
            base_url="portfolio.the-full-stack.com"
          else
            generic_url="https://the-full-stack.com"  # apex no cambia
            base_url="portfolio.${stage}.the-full-stack.com"
          fi

          {
            echo "## Apps deploy report — \`${stage}\`"
            echo
            echo "| Niche | Project | URL |"
            echo "|-------|---------|-----|"
            for niche in generic hub fintech architect leader vibe; do
              project="portfolio-${niche}${suffix}"
              if [[ "$niche" == "generic" && "$stage" == "prod" ]]; then
                url="${generic_url}"
              else
                url="https://${niche}.${base_url}"
              fi
              echo "| \`${niche}\` | \`${project}\` | ${url} |"
            done
            echo
            echo "Overall: ${deploy_result}"
            echo
            echo "Workflow: [run #${{ github.run_id }}](${{ github.server_url }}/${{ github.repository }}/actions/runs/${{ github.run_id }})"
          } > /tmp/body.md
          {
            echo "body<<EOF"
            cat /tmp/body.md
            echo "EOF"
          } >> "$GITHUB_OUTPUT"

      - name: Post commit comment
        uses: peter-evans/commit-comment@v3
        with:
          sha: ${{ github.sha }}
          body: ${{ steps.build-report.outputs.body }}
```

### G.2 — Ejemplo de output esperado

En el commit `019a90c`:

```markdown
## Backend deploy report — `dev`

| Step | Result |
|------|--------|
| Migrations | success |
| Lambdas affected | `["cv","contact_form"]` |
| Lambdas deploy | success |

Workflow: [run #1234567890](https://github.com/bypabloc/cv/actions/runs/1234567890)
```

```markdown
## Apps deploy report — `dev`

| Niche | Project | URL |
|-------|---------|-----|
| `generic` | `portfolio-generic-dev` | https://generic.portfolio.dev.the-full-stack.com |
| `hub` | `portfolio-hub-dev` | https://hub.portfolio.dev.the-full-stack.com |
| `fintech` | `portfolio-fintech-dev` | https://fintech.portfolio.dev.the-full-stack.com |
| `architect` | `portfolio-architect-dev` | https://architect.portfolio.dev.the-full-stack.com |
| `leader` | `portfolio-leader-dev` | https://leader.portfolio.dev.the-full-stack.com |
| `vibe` | `portfolio-vibe-dev` | https://vibe.portfolio.dev.the-full-stack.com |

Overall: success

Workflow: [run #1234567891](https://github.com/bypabloc/cv/actions/runs/1234567891)
```

### G.3 — Permiso `pull-requests: write`

`peter-evans/commit-comment@v3` requiere `permissions:
pull-requests: write` (o `contents: write`). Agregar al workflow:

```yaml
permissions:
  id-token: write       # OIDC (deploy-backend)
  contents: read
  pull-requests: write  # commit-comment
```

## Archivos afectados

### Modificar

- `.github/workflows/deploy-backend.yml` — agrega job `report` al
  final, con `needs: [..., deploy-lambdas]` + `if: always()`.
- `.github/workflows/deploy-apps.yml` — agrega job `report` al
  final, con `needs: [..., deploy-pages]` + `if: always()`.

## Criterios de aceptacion

- **AC-G1**: Given un workflow `deploy-backend.yml` exitoso, When
  inspecciono el commit `<sha>`, Then aparece un comentario con
  "Backend deploy report — `<stage>`" + tabla con resultados.
- **AC-G2**: Given un workflow con `migrate-db` fallido, Then el
  commit comment muestra `Migrations | failure` y el badge del
  workflow es rojo.
- **AC-G3**: Given un workflow `deploy-apps.yml` exitoso en `dev`,
  Then el comment lista las 6 URLs `*.portfolio.dev.the-full-stack.com`.
- **AC-G4**: Given un workflow `deploy-apps.yml` exitoso en `main`,
  Then la URL de `generic` es `https://the-full-stack.com` (apex, no
  subdominio).

## Verificacion

```bash
actionlint .github/workflows/deploy-backend.yml
actionlint .github/workflows/deploy-apps.yml

# Tras mergear el plan, push a dev y verificar:
gh run watch
gh api repos/bypabloc/cv/commits/$(git rev-parse HEAD)/comments
```

## Commit

```text
feat(ci): commit comment con resumen de cada deploy

- Agrega job 'report' al final de deploy-backend.yml y deploy-apps.yml
- needs: [...] + if: always() — corre tambien si pasos previos fallan
  (permite ver el resultado consolidado)
- Body en Markdown con tabla de resultados por step + URLs canonicas
  por env (dev: portfolio.dev.the-full-stack.com, stage: idem stage,
  main: portfolio.the-full-stack.com con apex para generic)
- Usa peter-evans/commit-comment@v3 (requiere
  permissions.pull-requests: write)
- Workflow links de vuelta al run de GH Actions para inspeccion
  detallada"
```
