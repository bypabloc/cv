"""Mutation testing config consumida por ``devtools/mutation_testing/main.py``.

Define paths bajo ``server/`` con thresholds por criticidad. Politica completa:
``.claude/rules/ai-testing-independence.md``.

| Categoria | Threshold | Razon |
|-----------|-----------|-------|
| critical  | 85%       | Bugs = perdida economica/legal (pagos, auth, PCI) |
| standard  | 70%       | Logica de negocio core |
| experimental | 30%    | Features nuevas; subir progresivo |

Uso:

    python devtools/run.py mutation_testing --paths=apps/payments
    python devtools/run.py mutation_testing --category=critical
    python devtools/run.py mutation_testing --all

NO es config nativa de mutmut — es un modulo Python propio del proyecto.
``main.py`` lo importa para clasificar paths y aplicar el threshold por
categoria. mutmut se invoca via subprocess, no lee este archivo directamente.
"""

from __future__ import annotations


# ── Categorias y thresholds ──────────────────────────────────────────────

CRITICAL_THRESHOLD = 0.85
STANDARD_THRESHOLD = 0.70
EXPERIMENTAL_THRESHOLD = 0.30

# Paths bajo server/ por categoria. Agregar nuevos modulos aqui cuando se
# creen apps. NO incluir tests/, migrations/, __init__.py — mutmut los
# excluye automaticamente.
CRITICAL_PATHS: tuple[str, ...] = (
    # Apps con dinero o credenciales — mutation score >= 85%
    'apps/payments/services',
    'apps/auth/services',
    'common/security',
)

STANDARD_PATHS: tuple[str, ...] = (
    # Logica de negocio core — mutation score >= 70%
    'apps/orders/services',
    'apps/orders/selectors',
)

EXPERIMENTAL_PATHS: tuple[str, ...] = (
    # Features nuevas o experimentales — mutation score >= 30%, subir progresivo
)

# Paths a excluir incluso si caen dentro de los anteriores (no aplica
# mutation testing a archivos de configuracion/admin).
EXCLUDED_FRAGMENTS: tuple[str, ...] = (
    '/admin/',
    '/migrations/',
    '/management/',
    '/__init__.py',
    '/apps.py',
    '/urls.py',
    '/constants.py',
    '/enums/',
)


def threshold_for_path(path: str) -> float:
    """Retorna el threshold (0..1) que aplica a ``path`` segun su categoria."""
    if any(p in path for p in CRITICAL_PATHS):
        return CRITICAL_THRESHOLD
    if any(p in path for p in STANDARD_PATHS):
        return STANDARD_THRESHOLD
    if any(p in path for p in EXPERIMENTAL_PATHS):
        return EXPERIMENTAL_THRESHOLD
    # Default: standard (70%) si no esta listado explicitamente
    return STANDARD_THRESHOLD


def category_for_path(path: str) -> str:
    """Retorna ``critical | standard | experimental`` segun la categoria del path."""
    if any(p in path for p in CRITICAL_PATHS):
        return 'critical'
    if any(p in path for p in EXPERIMENTAL_PATHS):
        return 'experimental'
    return 'standard'


def is_excluded(path: str) -> bool:
    """¿``path`` debe excluirse de mutation testing?"""
    return any(frag in path for frag in EXCLUDED_FRAGMENTS)


def all_categories() -> dict[str, tuple[str, ...]]:
    """Mapping completo categoria -> paths para iteracion en el script."""
    return {
        'critical': CRITICAL_PATHS,
        'standard': STANDARD_PATHS,
        'experimental': EXPERIMENTAL_PATHS,
    }
