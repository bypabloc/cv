# 09 — Fase 7: docs, rules, skill, CLAUDE.md

> [Anterior: 08](08-fase-6-eliminar-sam.md) | [README](README.md) | [Siguiente: 10](10-commits.md)

Actualiza toda la documentacion del repo que describe el backend
serverless en terminos de SAM. Es la ultima fase: describe el resultado
final, asi que se hace cuando las Fases 1-6 estan estables.

## Objetivo

Dos cosas en toda la documentacion (rules / docs / skill / CLAUDE.md):

1. Eliminar toda referencia a SAM, `sam-generate`, `template.yaml`
   efimero, `Transform`. Reemplazar por el modelo `provisioner` +
   `infra_provision` + estado local.
2. Actualizar el nombre del manifiesto: `lambda.yaml` ya se renombro a
   `manifest.yaml` en la Fase 2. Toda mencion de `lambda.yaml` en la
   documentacion debe pasar a `manifest.yaml`.

## Archivos afectados

### Modificar — rules

- `.claude/rules/lambda-controller.md` — el cambio mas grande de la fase:
  - quitar todas las menciones a `template.yaml`, `sam-generate`,
    `sam local invoke`, `sam deploy`, `Transform`.
  - reemplazar la seccion "Operacion con devtools" por el flujo
    `provisioner` + `state`.
  - actualizar la tabla de anti-patrones (quitar las filas de
    `template.yaml`).
  - renombrar `lambda.yaml` -> `manifest.yaml` en todo el archivo
    (estructura obligatoria, reglas SIEMPRE/NUNCA, ejemplos); el
    `manifest.yaml` ahora lo consume `provisioner.py`.
- `.claude/rules/neon-management.md` — la Lambda `db` ya no se opera con
  `sam`; revisar menciones (probablemente menores) + `lambda.yaml`.
- `.claude/rules/serverless-secrets.md` — menciona `template.yaml` y
  `samconfig.toml`; actualizar a "config renderizada por devtools".

### Modificar — docs

- `.claude/docs/lambda-controller/` (los 5-6 capitulos) — quitar SAM,
  `template.yaml`, `sam-generate`; renombrar `lambda.yaml` ->
  `manifest.yaml`. El capitulo `06-devtools-operations.md` se reescribe
  casi entero; `README.md` menciona `lambda.yaml`.
- `.claude/docs/serverless-backend/04-deploy-operacion.md` — reescribir:
  el deploy ya no es CloudFormation/SAM sino `provisioner` + AWS CLI;
  menciona `lambda.yaml`.
- `.claude/docs/serverless-backend/01-arquitectura-5-stacks.md` — el
  modelo "5 stacks" cambia; menciona `lambda.yaml`.
- `.claude/docs/serverless-backend/README.md` — el modelo "5 stacks
  CloudFormation" deja de ser cierto; pasa a "recursos gestionados por
  devtools con estado local"; menciona `lambda.yaml`.
- `.claude/docs/aws-lambda/` — revisar menciones a SAM deploy.

### Modificar — skill

- `.claude/skills/lambda-controller/SKILL.md` — quitar `sam-generate`,
  `template.yaml`, `lambda.yaml -> SAM` de la descripcion y el cuerpo;
  renombrar `lambda.yaml` -> `manifest.yaml`. Actualizar keywords si
  mencionan SAM.

### Modificar — scaffold

- `.claude/templates/lambda-controller/` — el archivo
  `lambda.yaml` del scaffold YA se renombro a `manifest.yaml` en la
  Fase 2. Aqui se actualizan sus comentarios (sin SAM) y el
  `.claude/templates/lambda-controller/README.md` que lo describe.

### Modificar — CLAUDE.md raiz

- `CLAUDE.md` — la tabla del arbol de conocimiento:
  - fila "Formato de Lambdas Python" — quitar "del que devtools genera el
    SAM efimero".
  - fila "Devtools serverless CLI" — quitar "deploy-infra ... y, con
    --path=..., los Lambdas lambda-controller (sam-generate, ...)".
  - fila "Backend serverless" — "Modelo de 5 stacks CloudFormation" pasa
    a describir el modelo nuevo.
  - seccion "Skills disponibles" — la descripcion de `lambda-controller`
    menciona SAM; actualizar.

### Crear

- `.claude/docs/serverless-backend/05-estado-local.md` (o seccion
  equivalente) — documenta el archivo de estado de devtools: esquema,
  donde vive, gitignore, comandos `status` / `destroy`.

## Validacion obligatoria de los cambios `.claude/*`

Todo cambio en `.claude/skills/`, `.claude/rules/`, `.claude/docs/` debe
validarse con `claude -p` segun
[.claude/rules/claude-config-testing.md](../../../.claude/rules/claude-config-testing.md).
Minimo 5 angulos en espanol. Ejemplos de prompts para esta fase:

```bash
claude --permission-mode bypassPermissions \
  --disallowedTools "WebSearch" "WebFetch" \
  --strict-mcp-config --mcp-config '{"mcpServers":{}}' \
  --output-format json \
  -p "como deployo un lambda del portfolio"
# Esperado: explica `serverless deploy`, NADA de sam

  -p "que es el template.yaml del lambda"
# Esperado: explica que YA NO EXISTE, devtools provisiona directo

  -p "como ejecuto un lambda en local"
# Esperado: `run --stage=local`, RIE / direct, NADA de sam local invoke

  -p "como destruyo la infra del backend en dev"
# Esperado: `serverless destroy --stage=dev`

  -p "el deploy del backend usa cloudformation?"   # angulo trampa
# Esperado: NO, devtools usa AWS CLI directo + estado local

  -p "que es el manifest.yaml de un lambda"
# Esperado: manifiesto de config del Lambda; NADA de `lambda.yaml`
```

## Criterios de aceptacion

- **AC-7.1**: When se busca `sam` en `.claude/rules/lambda-controller.md`,
  Then no hay resultados (salvo en contexto historico explicito).
- **AC-7.2**: When se busca `template.yaml` o `Transform` en
  `.claude/docs/lambda-controller/`, Then no hay resultados.
- **AC-7.3**: Given el prompt "como deployo un lambda del portfolio",
  When se ejecuta `claude -p`, Then la respuesta describe `serverless
  deploy` sin mencionar SAM.
- **AC-7.4**: Given el prompt trampa "el deploy usa cloudformation?",
  When se ejecuta `claude -p`, Then la respuesta dice que NO.
- **AC-7.5**: When se lee la tabla del arbol de conocimiento de
  `CLAUDE.md`, Then ninguna fila menciona SAM ni "5 stacks
  CloudFormation".
- **AC-7.6**: When se busca `lambda.yaml` en `.claude/` (fuera de
  `docs/specs/`), Then no hay resultados — toda la documentacion usa
  `manifest.yaml`.
- **AC-7.7**: Given el prompt "que es el manifest.yaml de un lambda",
  When se ejecuta `claude -p`, Then la respuesta lo describe como el
  manifiesto de config del Lambda y NO menciona `lambda.yaml`.

## Verificacion incremental con comandos devtools

Esta fase solo toca documentacion (`.claude/` y `CLAUDE.md`), pero igual
se re-corre la grilla de comandos para confirmar que el rename de
`.claude/templates/lambda-controller/manifest.yaml` y los docs no
rompieron nada que el CLI use:

```bash
python devtools/run.py serverless tests --type=unit
python devtools/run.py serverless help
```

Ambos deben pasar — el CLI no depende de `.claude/`, asi que esto es un
chequeo de no-regresion barato.

## Verificacion (Definition of Done de la fase)

```bash
rg -l "\bsam\b|template\.yaml|Transform: AWS::Serverless|lambda\.yaml" \
   .claude/ CLAUDE.md --glob '!docs/specs/**'      # 0 resultados
# 6 prompts claude -p (5 de SAM + 1 de manifest.yaml), num_turns > 1
python devtools/run.py serverless tests --type=unit    # no-regresion
python devtools/run.py serverless help
```

- [ ] AC-7.1..AC-7.7 cubiertos
- [ ] Los 6 prompts `claude -p` pasan (6/6)
- [ ] `CLAUDE.md` actualizado
- [ ] skill `lambda-controller` validada
- [ ] Cero menciones a SAM ni a `lambda.yaml` en `.claude/` (fuera de
      `docs/specs/`)
- [ ] `serverless tests` + `serverless help` siguen verdes

---

[Anterior: 08](08-fase-6-eliminar-sam.md) | [README](README.md) | [Siguiente: 10](10-commits.md)
