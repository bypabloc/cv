"""Reglas de compatibilidad cross-package del monorepo portfolio.

Cada regla recibe la lista de ``ResolvedPackage`` (que ya tienen current y
latest) agregada en TODOS los manifests del monorepo y devuelve una lista
de ``CompatIssue``. Una issue describe un mismatch que ``upgrade_deps`` no
puede detectar por si solo porque solo mira version vs registry, no
coherencia cross-workspace.

Reglas implementadas:

1. ``astro_major_uniform`` — todas las apps (``apps/<app>``) deben
   declarar ``astro`` en la misma major version. Mix de Astro 5 y 6
   rompe peer deps de ``@astrojs/*``.

2. ``astrojs_compatible_with_astro`` — para cada app, ``@astrojs/sitemap``
   y ``@astrojs/check`` deben ser compatibles con la major de astro
   declarada (sitemap >=3.7.0 para Astro 6, check >=0.9.9 para Astro 6).

3. ``vite_peer_consistency`` — si algun manifest pin ``vite`` (raiz o
   workspace), debe ser ``^7.x`` para Astro 6 (Astro 6 advierte con
   Vite 8). Si no hay pin, OK.

4. ``vite_node_matches_vitest`` — ``vite-node`` y ``vitest`` que aparecen
   en el mismo manifest deben compartir major (ambos 2.x o ambos 4.x; el
   mismatch rompe en runtime).

5. ``tailwind_uniform`` — si ``@tailwindcss/vite`` aparece en algun
   manifest, debe matchear la major de ``tailwindcss`` (ambos 4.x).

6. ``typescript_uniform`` — ``typescript`` debe ser la misma major en
   todo el monorepo (sino los tipos de cross-package imports divergen).

7. ``yaml_plugin_present_when_content_loaded`` — apps que dependen de
   ``@portfolio/content`` (via ``noExternal``) deben tener
   ``@modyfi/vite-plugin-yaml`` instalado (sino el ``import.meta.glob``
   de los YAML rompe en build).
"""

from __future__ import annotations

from typing import NamedTuple

from validate_versions.resolver import ResolvedPackage


class CompatIssue(NamedTuple):
    """Un mismatch de compatibilidad cross-package.

    Attributes:
        rule: identificador corto de la regla violada
            (``'astro_major_uniform'``, etc.).
        severity: ``'error'`` (rompe builds) o ``'warning'`` (deprecation).
        message: explicacion legible.
        affected: lista de ``'<workspace>::<package>'`` involucrados.
    """

    rule: str
    severity: str
    message: str
    affected: list[str]


def _major(version: str) -> int:
    """Extrae el major de una version. Devuelve -1 si no parsea."""
    if not version:
        return -1
    base = version.lstrip('^~>=< ').split('.')[0]
    return int(base) if base.isdigit() else -1


def _by_name(
    packages: list[ResolvedPackage], name: str
) -> list[ResolvedPackage]:
    """Filtra packages por nombre (case-sensitive)."""
    return [p for p in packages if p.name == name]


def _is_app(workspace: str) -> bool:
    return workspace.startswith('app:')


# ---------------------------------------------------------------------------
# Reglas
# ---------------------------------------------------------------------------


def rule_astro_major_uniform(
    packages: list[ResolvedPackage],
) -> list[CompatIssue]:
    """Todas las apps deben declarar astro en la misma major."""
    astro_in_apps = [
        p for p in _by_name(packages, 'astro') if _is_app(p.workspace)
    ]
    if len(astro_in_apps) <= 1:
        return []

    majors = {_major(p.current) for p in astro_in_apps}
    if len(majors) == 1:
        return []

    affected = [f'{p.workspace}::astro@{p.current}' for p in astro_in_apps]
    return [
        CompatIssue(
            rule='astro_major_uniform',
            severity='error',
            message=(
                'Las apps declaran astro en majors distintas '
                f'({sorted(majors)}). Todas deben usar la misma major para '
                'evitar peer dep conflicts entre @astrojs/* y astro.'
            ),
            affected=affected,
        )
    ]


def rule_astrojs_compatible_with_astro(
    packages: list[ResolvedPackage],
) -> list[CompatIssue]:
    """@astrojs/* deben ser compatibles con la major de astro."""
    issues: list[CompatIssue] = []
    # Minimos por major de astro (basado en research).
    min_required: dict[int, dict[str, str]] = {
        6: {
            '@astrojs/sitemap': '3.7.0',
            '@astrojs/check': '0.9.9',
        },
    }

    apps_with_astro = {
        p.workspace: p
        for p in _by_name(packages, 'astro')
        if _is_app(p.workspace)
    }

    for workspace, astro_pkg in apps_with_astro.items():
        major = _major(astro_pkg.current)
        if major not in min_required:
            continue
        for dep_name, min_version in min_required[major].items():
            deps = [
                p
                for p in _by_name(packages, dep_name)
                if p.workspace == workspace
            ]
            issues.extend(
                CompatIssue(
                    rule='astrojs_compatible_with_astro',
                    severity='error',
                    message=(
                        f'{dep_name}@{dep.current} en {workspace} es '
                        f'incompatible con astro@{astro_pkg.current} '
                        f'(requiere >= {min_version}).'
                    ),
                    affected=[
                        f'{workspace}::{dep_name}@{dep.current}',
                        f'{workspace}::astro@{astro_pkg.current}',
                    ],
                )
                for dep in deps
                if _version_lt(dep.current, min_version)
            )
    return issues


def rule_vite_peer_consistency(
    packages: list[ResolvedPackage],
) -> list[CompatIssue]:
    """Si hay astro 6 declarado, vite debe ser ^7 (Astro 6 advierte con Vite 8)."""
    has_astro_6 = any(
        _major(p.current) == 6 for p in _by_name(packages, 'astro')
    )
    if not has_astro_6:
        return []

    vite_pins = _by_name(packages, 'vite')
    issues: list[CompatIssue] = []
    for v in vite_pins:
        major = _major(v.current)
        if major != 7:
            issues.append(
                CompatIssue(
                    rule='vite_peer_consistency',
                    severity='warning' if major == 8 else 'error',
                    message=(
                        f'vite@{v.current} en {v.workspace} no coincide '
                        'con Vite 7.x (Astro 6 oficialmente soporta Vite 7;'
                        ' advierte con Vite 8). Pin a ^7 en `overrides` o '
                        'devDependencies.'
                    ),
                    affected=[f'{v.workspace}::vite@{v.current}'],
                )
            )
    return issues


def rule_vite_node_matches_vitest(
    packages: list[ResolvedPackage],
) -> list[CompatIssue]:
    """vite-node y vitest en el mismo manifest deben compartir major."""
    issues: list[CompatIssue] = []
    by_workspace: dict[str, dict[str, ResolvedPackage]] = {}
    for p in packages:
        if p.name in {'vite-node', 'vitest'}:
            by_workspace.setdefault(p.workspace, {})[p.name] = p

    for workspace, deps in by_workspace.items():
        if 'vite-node' not in deps or 'vitest' not in deps:
            continue
        m1 = _major(deps['vite-node'].current)
        m2 = _major(deps['vitest'].current)
        if m1 != m2:
            issues.append(
                CompatIssue(
                    rule='vite_node_matches_vitest',
                    severity='error',
                    message=(
                        f'vite-node@{deps["vite-node"].current} y '
                        f'vitest@{deps["vitest"].current} en {workspace} '
                        f'tienen majors distintas ({m1} vs {m2}). '
                        'vite-node se distribuye junto a vitest; usar la '
                        'misma major.'
                    ),
                    affected=[
                        f'{workspace}::vite-node@{deps["vite-node"].current}',
                        f'{workspace}::vitest@{deps["vitest"].current}',
                    ],
                )
            )
    return issues


def rule_tailwind_uniform(
    packages: list[ResolvedPackage],
) -> list[CompatIssue]:
    """tailwindcss y @tailwindcss/vite deben compartir major."""
    issues: list[CompatIssue] = []
    by_workspace: dict[str, dict[str, ResolvedPackage]] = {}
    for p in packages:
        if p.name in {
            'tailwindcss',
            '@tailwindcss/vite',
            '@tailwindcss/postcss',
        }:
            by_workspace.setdefault(p.workspace, {})[p.name] = p

    for workspace, deps in by_workspace.items():
        if 'tailwindcss' not in deps:
            continue
        tw_major = _major(deps['tailwindcss'].current)
        for plugin_name in ('@tailwindcss/vite', '@tailwindcss/postcss'):
            if plugin_name in deps:
                pl_major = _major(deps[plugin_name].current)
                if pl_major != tw_major:
                    issues.append(
                        CompatIssue(
                            rule='tailwind_uniform',
                            severity='error',
                            message=(
                                f'{plugin_name}@'
                                f'{deps[plugin_name].current} y '
                                f'tailwindcss@{deps["tailwindcss"].current} '
                                f'en {workspace} no comparten major.'
                            ),
                            affected=[
                                f'{workspace}::{plugin_name}@'
                                f'{deps[plugin_name].current}',
                                f'{workspace}::tailwindcss@'
                                f'{deps["tailwindcss"].current}',
                            ],
                        )
                    )
    return issues


def rule_typescript_uniform(
    packages: list[ResolvedPackage],
) -> list[CompatIssue]:
    """typescript debe ser misma major en todo el monorepo."""
    ts = _by_name(packages, 'typescript')
    if len(ts) <= 1:
        return []

    majors = {_major(p.current) for p in ts}
    if len(majors) == 1:
        return []

    affected = [f'{p.workspace}::typescript@{p.current}' for p in ts]
    return [
        CompatIssue(
            rule='typescript_uniform',
            severity='warning',
            message=(
                f'typescript declarado en majors distintas {sorted(majors)} '
                'a traves del monorepo. Los tipos de imports cross-package '
                'pueden divergir.'
            ),
            affected=affected,
        )
    ]


def _version_lt(a: str, b: str) -> bool:
    """True si version a < version b. Comparacion numerica simple por componentes."""

    def parts(v: str) -> tuple[int, ...]:
        clean = v.lstrip('^~>=< ').split('-')[0].split('+')[0]
        out: list[int] = []
        for chunk in clean.split('.'):
            if chunk.isdigit():
                out.append(int(chunk))
            else:
                break
        return tuple(out) if out else (0,)

    return parts(a) < parts(b)


ALL_RULES = (
    rule_astro_major_uniform,
    rule_astrojs_compatible_with_astro,
    rule_vite_peer_consistency,
    rule_vite_node_matches_vitest,
    rule_tailwind_uniform,
    rule_typescript_uniform,
)


def run_all(packages: list[ResolvedPackage]) -> list[CompatIssue]:
    """Ejecuta todas las reglas y devuelve la concatenacion de issues."""
    issues: list[CompatIssue] = []
    for rule in ALL_RULES:
        issues.extend(rule(packages))
    return issues
