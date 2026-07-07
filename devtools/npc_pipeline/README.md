# npc_pipeline

Orquesta el pipeline Blender headless del plan `journey-npc-realism`:
malla humanoide (MPFB2) -> rig (Rigify) -> animación (keyframing manual)
-> export (`.glb` vía Blender nativo + glTF-Transform Meshopt).

Referencia completa: [.claude/docs/journey-npc-realism/](../../.claude/docs/journey-npc-realism/)
y el skill `/journey-npc-realism`.

## Requisito manual (no es dependencia del monorepo)

Blender >= 4.2 instalado localmente (`blender.org`, sin cuenta). Este
script NUNCA lo instala — solo verifica que esté disponible
(`npc_pipeline status`) y da un mensaje claro si falta.

## Comandos

```bash
python devtools/run.py npc_pipeline status
python devtools/run.py npc_pipeline install-addons --mpfb2-zip=devtools/npc_pipeline/vendor/mpfb2.zip
python devtools/run.py npc_pipeline generate-mesh --output=<path.blend> [--preview-dir=<dir>]
python devtools/run.py npc_pipeline rig --input=<npc-base.blend> --output=<npc-rigged.blend>
python devtools/run.py npc_pipeline export --input=<npc-rigged.blend> --output=<npc-base.glb> [--skip-compress]
```

## Estructura

```text
npc_pipeline/
├── __init__.py
├── main.py             # dispatch de subcomandos
├── flags.py             # parsing + validacion
├── blender_runner.py     # arma/corre `blender --background --python ...`
├── scripts/              # corren DENTRO de Blender (bpy), no en devtools/.venv
│   ├── install_addons.py
│   ├── generate_mesh.py
│   ├── rig_mesh.py
│   └── export_glb.py
├── vendor/               # zips de addons (gitignored, ver .gitignore)
└── README.md
```

## Estado (2026-07-06)

Los scripts `bpy` están escritos siguiendo el API documentado de Rigify y
del exportador nativo glTF2 de Blender (confianza alta, verificado en el
research). El API exacto de MPFB2 (`bpy.ops.mpfb.*`) usado en
`generate_mesh.py` es un **placeholder pendiente del spike de
descubrimiento** (correr `dir(bpy.ops.mpfb)` con Blender + MPFB2
instalados) — no se pudo verificar sin Blender disponible en este
entorno. Ver el `TODO` marcado en ese archivo.
