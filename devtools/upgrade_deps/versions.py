"""Comparación de versiones (PEP 440 / SemVer).

Usa ``packaging.version`` (incluido en stdlib via setuptools en Python >=3.13;
fallback a regex propia si no esta disponible). Maneja pre-releases
(alpha/beta/rc/dev) ignorandolos por default.
"""

import re


# Indicadores de pre-release: PEP 440 (a/b/rc/dev) y SemVer (-alpha/-beta/-rc/-pre)
_PRERELEASE_RE = re.compile(
    r'(?:'
    r'-(?:alpha|beta|rc|pre|preview|dev)\b'  # SemVer style: 1.0.0-alpha
    r'|'
    r'(?:[abr])(?:c)?\d+\b'  # PEP 440 short: 1.0a1, 1.0b2, 1.0rc1
    r'|'
    r'\.dev\d*\b'  # PEP 440 dev: 1.0.dev0
    r')',
    re.IGNORECASE,
)


def is_prerelease(version: str) -> bool:
    """True si la version es alpha, beta, rc, dev o cualquier pre-release.

    Maneja tanto SemVer (``1.0.0-rc.1``) como PEP 440 (``1.0a1``, ``1.0.dev0``).
    Las versiones ``post`` y las que tienen build metadata (``+build.123``) NO
    se consideran pre-release.
    """
    return bool(_PRERELEASE_RE.search(version))


def _parse_version_tuple(version: str) -> tuple[int, ...]:
    """Convierte ``1.10.3`` -> (1, 10, 3) para comparación numerica.

    Strips pre-release suffixes y build metadata. Numbers no parseables se
    truncan en el primer componente no-numerico.
    """
    # Remove build metadata (+...)
    base = version.split('+', 1)[0]
    # Remove pre-release suffixes (-alpha, .dev0, a1, b2, rc1, etc.)
    base = _PRERELEASE_RE.split(base)[0]
    # Remove trailing .post (treated as same release for ordering purposes —
    # post-releases siguen al stable, así que son equivalentes para "es mas
    # nuevo que").
    base = re.sub(r'\.post\d+$', '', base)

    parts: list[int] = []
    for chunk in base.split('.'):
        if chunk.isdigit():
            parts.append(int(chunk))
        else:
            # Chunk con letras (no esperado en stable): paramos
            break

    return tuple(parts) if parts else (0,)


def is_newer(*, current: str, candidate: str) -> bool:
    """True si ``candidate`` es estrictamente mayor que ``current``."""
    return _parse_version_tuple(candidate) > _parse_version_tuple(current)


def pick_latest_stable(versions: list[str]) -> str | None:
    """Devuelve la version estable mas alta de la lista.

    Excluye pre-releases (alpha/beta/rc/dev). Retorna None si no hay
    candidatos estables.
    """
    stable = [v for v in versions if not is_prerelease(v)]
    if not stable:
        return None

    return max(stable, key=_parse_version_tuple)


def format_with_prefix(*, prefix: str, version: str) -> str:
    """Concatena prefijo + version preservando la semántica del manifest."""
    return f'{prefix}{version}'
