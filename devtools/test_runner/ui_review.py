"""Optional Gemini-CLI UI review pass over generated screenshots.

Triggered by ``--ui-review``. Copies E2E screenshots to a non-gitignored
tmp directory so the gemini CLI can read them, builds a structured prompt
and prints the model's findings. Failures here do not invalidate the test
suite — the review is advisory.
"""

from __future__ import annotations

from pathlib import Path
import shutil
import subprocess

from shared.console import _err
from shared.console import _header
from shared.console import _ok
from shared.console import _step
from shared.console import _warn
from shared.paths import PROJECT_ROOT


UI_REVIEW_PROMPT = """\
Eres un auditor senior de UI/UX. Analiza las siguientes capturas de pantalla \
y detecta inconsistencias, errores visuales y problemas de calidad.

IMÁGENES:
{image_lines}

EVALUACIÓN REQUERIDA:
1. Espaciado: margenes y paddings consistentes entre elementos. Detectar gaps \
irregulares, espacios desiguales entre campos, secciones o componentes.
2. Tipografia: consistencia de font-size, font-weight, line-height y \
font-family entre elementos del mismo tipo. Detectar jerarquías rotas.
3. Layout y alineacion: elementos desalineados, centrado incorrecto, anchos \
inconsistentes, overflow de contenido.
4. Colores y contraste: uso consistente de la paleta de colores. Contraste \
texto/fondo conforme a WCAG AA (4.5:1 texto normal, 3:1 texto grande).
5. Componentes: botones, inputs, labels, iconos deben ser visualmente \
consistentes entre todas las capturas. Detectar variaciones no intencionales.
6. Estados: si hay estados visibles (hover, focus, error, disabled, empty, \
filled), evaluar si son claros, distinguibles y consistentes.
7. Responsividad: si hay capturas de diferentes viewports, evaluar que el \
layout se adapte correctamente sin romper alineacion ni legibilidad.
8. Accesibilidad visual: touch targets mínimo 44x44px en mobile, indicadores \
de campos requeridos, visibilidad de mensajes de error.
9. Artefactos: elementos de debug, overlays de desarrollo, tooltips residuales \
o cualquier elemento que no deberia estar visible en la UI final.
10. Overflow y truncamiento: texto cortado, contenido que desborda su \
contenedor, scrollbars inesperados.

FORMATO DE SALIDA (por cada hallazgo):

---
### [SEVERIDAD] Título descriptivo del problema
- **Archivos afectados**: lista completa de paths origen
- **Elemento**: componente o elemento HTML afectado
- **Problema**: descripción técnica precisa de la inconsistencia detectada
- **Impacto UX**: como afecta al usuario final
- **Cambio técnico esperado**:
  - CSS: propiedad y valor exacto a aplicar o corregir
  - Componente: nombre generico del componente a modificar
  - Lógica: cambio de lógica si aplica
- **Criterio WCAG**: número y nombre si aplica, o N/A
---

SEVERIDADES:
- CRÍTICA: bloquea release o rompe funcionalidad/accesibilidad
- MAYOR: afecta experiencia de usuario significativamente
- MENOR: inconsistencia visual notable
- COSMÉTICA: detalle de polish

FALSOS POSITIVOS CONOCIDOS (NO reportar):
- Estado de foco (focus ring/border) visible en inputs dentro de screenshots: \
las capturas son generadas por Playwright que interactua programaticamente con \
los campos. El último campo editado retiene el foco porque no hay blur \
explicito. Esto NO es un bug de la aplicación, es un artefacto del test runner.
- Espaciado responsive diferente entre viewports (ej. gap-4 en mobile vs gap-6 \
en desktop): variaciones intencionales de spacing entre breakpoints son \
decisiones de diseño válidas, no inconsistencias. Solo reportar si el spacing \
rompe la alineacion o legibilidad dentro de un mismo viewport.
- Campos de formulario sin icono junto a campos con icono: la presencia de \
iconos decorativos en inputs es opcional por campo según su contexto semántico. \
No todos los campos requieren icono. Solo reportar si la ausencia de icono \
rompe la alineacion horizontal o el tamaño del input respecto a los demas.

REGLAS:
- Responder SOLO en ESPAÑOL
- NO incluir introducción, conclusion ni texto fuera del formato
- Cada hallazgo debe ser accionable: un desarrollador frontend debe poder \
implementar el fix sin preguntas
- Si no hay problemas, responder: Sin hallazgos.
"""


RESULTS_DIR = PROJECT_ROOT / 'e2e' / 'results'
REVIEW_TMP_DIR = PROJECT_ROOT / '.claude' / 'tmp-review'


def _collect_screenshots() -> list[Path]:
    """Collect all .png files from E2E results directory."""
    if not RESULTS_DIR.is_dir():
        return []
    return sorted(RESULTS_DIR.rglob('*.png'))


def _prepare_review_images(screenshots: list[Path]) -> list[str]:
    """Copy screenshots to a non-gitignored dir, return prompt-ready lines."""
    if REVIEW_TMP_DIR.exists():
        shutil.rmtree(REVIEW_TMP_DIR)
    REVIEW_TMP_DIR.mkdir(parents=True)

    image_lines: list[str] = []
    for screenshot in screenshots:
        orig_path = screenshot.relative_to(PROJECT_ROOT)
        tmp_name = str(orig_path).replace('/', '_')
        tmp_path = REVIEW_TMP_DIR / tmp_name
        shutil.copy2(screenshot, tmp_path)

        tmp_rel = tmp_path.relative_to(PROJECT_ROOT)
        image_lines.append(f'- @{tmp_rel} (origen: {orig_path})')
    return image_lines


def _execute_gemini_review(prompt: str) -> int:
    """Execute the gemini CLI with ``prompt``. Returns exit code."""
    gemini_bin = shutil.which('gemini')
    if not gemini_bin:
        _err('gemini CLI no instalado (npm i -g @google/gemini-cli)')
        return 1

    try:
        result = subprocess.run(  # noqa: S603
            [gemini_bin, '-p', prompt],
            capture_output=True,
            text=True,
            check=False,
            timeout=180,
            cwd=str(PROJECT_ROOT),
        )
    except subprocess.TimeoutExpired:
        _err('gemini CLI timeout (180s)')
        return 1

    if result.returncode != 0:
        _err('gemini CLI fallo')
        if result.stderr:
            print(result.stderr)
        return 1

    output = result.stdout.strip()
    if output:
        print()
        print(output)
        print()

    return 0


def run_ui_review(*, verbose: bool) -> int:
    """Run a Gemini CLI UI review on the latest E2E screenshots."""
    _header('UI Review (Gemini CLI)')

    screenshots = _collect_screenshots()
    if not screenshots:
        _warn('Sin screenshots para revisar en e2e/results/')
        return 0

    _step(f'Encontrados {len(screenshots)} screenshot(s)')

    try:
        image_lines = _prepare_review_images(screenshots)
        prompt = UI_REVIEW_PROMPT.format(
            image_lines='\n'.join(image_lines),
        )

        if verbose:
            for line in image_lines:
                print(f'  {line}')

        _step('Ejecutando gemini CLI...')
        rc = _execute_gemini_review(prompt)

        if rc == 0:
            _ok('UI Review completado')
        return rc

    finally:
        if REVIEW_TMP_DIR.exists():
            shutil.rmtree(REVIEW_TMP_DIR)
