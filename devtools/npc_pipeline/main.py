"""Orchestrate the journey-npc-realism Blender headless pipeline.

Subcommand-style script:
  python devtools/run.py npc_pipeline <command> [flags...]

Comandos soportados:
  status           Verifica Blender (>=4.2) en PATH
  install-addons   Instala MPFB2 (zip local) + habilita Rigify
  generate-mesh    Genera la malla base humanoide (MPFB2)
  rig              Riggea la malla con Rigify
  animate          Crea los clips idle/walk (keyframes FK) sobre el rig
  export           Exporta a .glb (nativo Blender + glTF-Transform Meshopt)

Cada comando (salvo `status`) invoca Blender headless
(`blender --background --python <script> -- <args>`) — la logica bpy real
vive en `npc_pipeline/scripts/*.py`, corriendo en el Python EMBEBIDO de
Blender, no en `devtools/.venv`. Ver
.claude/docs/journey-npc-realism/ para el detalle del pipeline.

Ejemplos:
  python devtools/run.py npc_pipeline status
  python devtools/run.py npc_pipeline install-addons \\
    --mpfb2-zip=devtools/npc_pipeline/vendor/mpfb2.zip
  python devtools/run.py npc_pipeline generate-mesh \\
    --output=apps/journey-realistic/blender/assets/npc-base.blend \\
    --preview-dir=tmp/npc-pipeline/
  python devtools/run.py npc_pipeline rig \\
    --input=apps/journey-realistic/blender/assets/npc-base.blend \\
    --output=apps/journey-realistic/blender/assets/npc-rigged.blend
  python devtools/run.py npc_pipeline export \\
    --input=apps/journey-realistic/blender/assets/npc-rigged.blend \\
    --output=apps/journey-realistic/public/models/npc-base.glb
"""

from pathlib import Path
import subprocess

from npc_pipeline import blender_runner
from npc_pipeline.blender_runner import NpcPipelineError


def _dispatch_status(flags: dict) -> int:
    ok, message = blender_runner.check_blender_available(
        blender_bin=flags['blender_bin'],
    )
    print(message)
    return 0 if ok else 1


def _dispatch_install_addons(flags: dict) -> int:
    script_args = []
    if flags.get('mpfb2_zip'):
        script_args.append(f'--mpfb2-zip={flags["mpfb2_zip"]}')
    result = blender_runner.run_blender_script(
        script_name='install_addons.py',
        script_args=script_args,
        blender_bin=flags['blender_bin'],
    )
    print(result.stdout)
    return 0


def _dispatch_generate_mesh(flags: dict) -> int:
    script_args = [f'--output={flags["output"]}']
    if flags.get('preview_dir'):
        script_args.append(f'--preview-dir={flags["preview_dir"]}')
    result = blender_runner.run_blender_script(
        script_name='generate_mesh.py',
        script_args=script_args,
        blender_bin=flags['blender_bin'],
    )
    print(result.stdout)
    return 0


def _dispatch_rig(flags: dict) -> int:
    result = blender_runner.run_blender_script(
        script_name='rig_mesh.py',
        script_args=[
            f'--input={flags["input"]}',
            f'--output={flags["output"]}',
        ],
        blender_bin=flags['blender_bin'],
    )
    print(result.stdout)
    return 0


def _dispatch_animate(flags: dict) -> int:
    result = blender_runner.run_blender_script(
        script_name='animate.py',
        script_args=[
            f'--input={flags["input"]}',
            f'--output={flags["output"]}',
        ],
        blender_bin=flags['blender_bin'],
    )
    print(result.stdout)
    return 0


def _dispatch_export(flags: dict) -> int:
    output = Path(flags['output'])
    raw_glb = output.with_suffix('.raw.glb')

    result = blender_runner.run_blender_script(
        script_name='export_glb.py',
        script_args=[
            f'--input={flags["input"]}',
            f'--output={raw_glb}',
        ],
        blender_bin=flags['blender_bin'],
    )
    print(result.stdout)

    if flags.get('skip_compress'):
        raw_glb.replace(output)
        return 0

    output.parent.mkdir(parents=True, exist_ok=True)
    # S603/S607: `npx` es un CLI conocido resuelto via PATH (mismo patron
    # que sync_secrets/**/*.py con `gh`); args fijos + paths propios.
    gltf_transform_cmd = [
        'npx',
        '--yes',
        '@gltf-transform/cli',
        'meshopt',
        str(raw_glb),
        str(output),
    ]
    compress = subprocess.run(gltf_transform_cmd, check=False)  # noqa: S603
    if compress.returncode == 0:
        raw_glb.unlink(missing_ok=True)
    return compress.returncode


_DISPATCH = {
    'status': _dispatch_status,
    'install-addons': _dispatch_install_addons,
    'generate-mesh': _dispatch_generate_mesh,
    'rig': _dispatch_rig,
    'animate': _dispatch_animate,
    'export': _dispatch_export,
}


def main(flags: dict) -> int:
    """Entry point invoked by ``devtools/run.py``."""
    command = flags['command']
    handler = _DISPATCH.get(command)
    if handler is None:
        # No deberia llegar aqui — flags.py ya valida VALID_COMMANDS.
        print(f'Comando no implementado: {command}')
        return 1
    try:
        return handler(flags)
    except NpcPipelineError as exc:
        print(str(exc))
        return 1
