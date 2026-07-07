# App nueva `apps/journey-realistic` + comando devtools `npc_pipeline`

## Por qué una copia y no modificar `apps/journey` in-place

`apps/journey` está deployada y sirve el CV real (`journey.portfolio.*`).
El pipeline propuesto es un cambio arquitectónico grande (de 100%
procedural a `.glb` rigged) con incertidumbre real (performance no
medida, calidad visual a validar). Copiarla a una app nueva permite:

- Comparar A/B el resultado sin arriesgar la app en producción.
- Iterar sin pisar el trabajo en curso de otros planes de `apps/journey`
  (ej. `journey-puerta-sillas-pilar`, activo en este momento).
- Descartar el experimento sin costo si el resultado no convence — basta
  con borrar `apps/journey-realistic`.

## Qué se copia vs qué se comparte

`pnpm-workspace.yaml` ya usa el glob `apps/*`, así que una carpeta nueva
bajo `apps/` se suma al workspace sin editar ese archivo.

| Origen (`apps/journey`) | Destino (`apps/journey-realistic`) | Tratamiento |
|---|---|---|
| `package.json` | `package.json` | Copiar y renombrar: `name: "@portfolio/journey-realistic"`, puerto de dev distinto (ej. `4328`, el actual de journey es `4327`) |
| `astro.config.ts` | `astro.config.ts` | Copiar; ajustar `SITE`/slug si aplica (sin deploy en este plan, ver decisión 12 — puede apuntar a un placeholder) |
| `src/engine/character.ts`, `toon.ts` | idem | **Se bifurca** — es el corazón del cambio (nueva implementación interna, misma interfaz pública) |
| `src/engine/rooms/`, `dialogs/`, `world.ts`, `themes.ts` | idem | Copiar tal cual para tener un banco de pruebas completo (10 salas); no se planea editar contenido de salas en este plan |
| `src/lib/*` | idem | Copiar tal cual |
| `src/pages/*` | idem | Copiar tal cual |
| `@portfolio/content`, `@portfolio/ui`, `@portfolio/app-shared`, `@portfolio/seo` | mismos, `workspace:*` | **NO se duplican** — se siguen consumiendo como dependencia de workspace, ningún cambio a esos packages |
| `public/models/` | **nuevo** | Directorio nuevo para los `.glb` generados por el pipeline (no existe en `apps/journey` porque no usa assets externos) |
| `blender/assets/` | **nuevo** | `.blend` intermedios del pipeline (NO se commitean — ver `.gitignore` en la descomposición) |

## Comando devtools nuevo: `npc_pipeline`

Siguiendo la convención existente de scripts subcommand-style
(`.claude/rules/devtools.md`, mismo patrón que `serverless`/`docker`/
`rotate_secrets`): comando posicional + flags, un paquete
`devtools/npc_pipeline/` con `main.py` + `flags.py` + `README.md`.

```bash
python devtools/run.py npc_pipeline install-addons --mpfb2-zip=<path>
python devtools/run.py npc_pipeline generate-mesh --output=apps/journey-realistic/blender/assets/npc-base.blend
python devtools/run.py npc_pipeline rig --input=<...npc-base.blend> --output=<...npc-rigged.blend>
python devtools/run.py npc_pipeline export --input=<...npc-rigged.blend> --output=apps/journey-realistic/public/models/npc-base.glb
python devtools/run.py npc_pipeline status   # verifica que Blender + MPFB2 + Rigify estan disponibles
```

Responsabilidad de `devtools/npc_pipeline/`: **orquestar** (armar el
comando `blender --background --python <script>.py -- <args>` como
subprocess, capturar stdout/stderr, exit codes) — la lógica real de cada
etapa vive en los scripts `bpy` bajo
`devtools/npc_pipeline/scripts/*.py` (ver
[02-blender-pipeline-etapa1.md](02-blender-pipeline-etapa1.md)), porque
esos scripts corren DENTRO del Python embebido de Blender, no bajo
`devtools/.venv` (Python 3.14) — son procesos separados por diseño.

```text
devtools/npc_pipeline/
├── __init__.py
├── main.py                  # dispatch de subcomandos (install-addons/generate-mesh/rig/export/status)
├── flags.py                 # parsing (--output, --input, --mpfb2-zip, ...)
├── blender_runner.py        # arma y corre `blender --background --python ...` via subprocess
├── scripts/                 # los .py que corren DENTRO de Blender (bpy)
│   ├── install_addons.py
│   ├── generate_mesh.py
│   ├── rig_mesh.py
│   └── export_glb.py
├── vendor/                  # zips de addons descargados manualmente (gitignored si pesan)
└── README.md
```

## Verificación local de Blender (pre-requisito, no bloquea el plan)

Blender no es una dependencia del monorepo (no vía pnpm/uv) — es un
binario que el dev instala en su máquina. `npc_pipeline status` valida
que `blender` esté en `PATH` y con la versión mínima (>=4.2) antes de
correr cualquier subcomando, dando un mensaje claro si falta.
