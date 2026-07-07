"""Blender headless: install MPFB2 (optional) + enable Rigify.

Run via devtools:
  python devtools/run.py npc_pipeline install-addons \
    --mpfb2-zip=devtools/npc_pipeline/vendor/mpfb2.zip

Direct invocation:
  blender --background --python install_addons.py -- \
    --mpfb2-zip=<path>

El zip de MPFB2 se descarga desde extensions.blender.org (sin cuenta,
link directo con sha256 verificable) — ver
.claude/docs/journey-npc-realism/01-pipeline-blender-headless.md. Rigify
viene incluido en Blender: solo requiere habilitarse.

MPFB2 se distribuye como EXTENSION de Blender 4.2+ (``blender_manifest.toml``
en la raiz del zip), NO como addon legacy — se instala con
``bpy.ops.extensions.package_install_files(repo='user_default', ...)``,
no con ``bpy.ops.preferences.addon_install`` (ese falla con
"ZIP packaged incorrectly", descubierto corriendo el pipeline real). El
modulo Python resultante queda namespaced como
``bl_ext.user_default.mpfb`` (no ``mpfb`` a secas).
"""

from pathlib import Path
import sys

import bpy


# Blender no siempre agrega el directorio del script a sys.path en modo
# --background --python (verificado corriendo el pipeline real): hay que
# hacerlo explicito para poder importar el _argv.py hermano.
sys.path.insert(0, str(Path(__file__).resolve().parent))
from _argv import parse_args


def main() -> None:
    args = parse_args()
    mpfb2_zip = args.get('mpfb2_zip')

    if mpfb2_zip:
        result = bpy.ops.extensions.package_install_files(
            filepath=mpfb2_zip,
            repo='user_default',
            enable_on_install=True,
        )
        if result != {'FINISHED'}:
            msg = f'Instalacion de MPFB2 fallo: {result}'
            raise RuntimeError(msg)
        print(f'MPFB2 instalado desde {mpfb2_zip} (bl_ext.user_default.mpfb)')
    else:
        print('--mpfb2-zip no provisto: solo se habilita Rigify')

    bpy.ops.preferences.addon_enable(module='rigify')
    bpy.ops.wm.save_userpref()
    print('Rigify habilitado')


if __name__ == '__main__':
    main()
