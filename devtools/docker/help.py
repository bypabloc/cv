"""Coloured help text for ``docker help``.

This is the long-form help with sections and ANSI colours. It is distinct
from ``docker --help`` which dumps the README. Both stay around because
they target different consumers: README for newcomers reading docs, the
colourised version for terminal users who already know the shape.
"""

from __future__ import annotations

from typing import Any

from shared.console import BOLD
from shared.console import CYAN
from shared.console import DIM
from shared.console import GREEN
from shared.console import YELLOW
from shared.console import _c
from shared.project_config import PROJECT_NAME_DISPLAY


def cmd_help(flags: dict[str, Any]) -> int:
    """Display help text with all available commands."""
    print()
    print(f'{_c(BOLD, f"{PROJECT_NAME_DISPLAY} - Docker CLI")}')
    print(f'{_c(DIM, "Uso: python devtools/run.py docker <comando> [flags]")}')

    sections = [
        (
            'Lifecycle',
            [
                ('up', 'Iniciar servicios', '--detach --build --env=<env>'),
                ('down', 'Detener servicios', '--volumes'),
                ('build', 'Construir imágenes', '--no-cache'),
                (
                    'rebuild',
                    'Reconstruir desde cero',
                    '(down + build --no-cache + up)',
                ),
                (
                    'logs',
                    'Ver logs de servicios',
                    '--tail=N --follow [servicio]',
                ),
                ('shell', 'Bash interactivo en server', ''),
                (
                    'exec',
                    'Ejecutar comando en container',
                    '[--target=<service>] -- <cmd> [args]',
                ),
                ('ps', 'Listar containers', ''),
                ('restart', 'Reiniciar servicios', '[servicio...]'),
                (
                    'refresh',
                    'Refresh completo',
                    '--keep-volumes --skip-cache',
                ),
            ],
        ),
        (
            'Quality',
            [
                (
                    'lint',
                    'Lint (Biome apps/packages, Ruff devtools)',
                    '--module=<app|pkg-*|devtools>',
                ),
                (
                    'lint-fix',
                    'Lint auto-fix (Biome/Ruff)',
                    '--module=<app|pkg-*|devtools>',
                ),
                (
                    'format',
                    'Format (Biome/Ruff)',
                    '--module=<app|pkg-*|devtools>',
                ),
            ],
        ),
        (
            'Database',
            [
                ('db-shell', 'Abrir psql interactivo', ''),
                ('db-tables', 'Listar tablas', ''),
                ('db-describe', 'Describir tabla', '<nombre_tabla>'),
                ('db-count', 'Conteo de filas por tabla', ''),
                ('db-seed', 'Ejecutar seeds', '--clear --only=<name>'),
                ('db-reset', 'Reset completo de DB', '(destructivo)'),
            ],
        ),
        (
            'Setup',
            [
                (
                    'setup',
                    'Setup inicial completo',
                    '--no-seed --no-superuser',
                ),
                ('clean', 'Eliminar todo', '(destructivo)'),
                ('help', 'Mostrar esta ayuda', ''),
            ],
        ),
        (
            'Cache',
            [
                ('cache-clear-all', 'Limpiar todos los caches', ''),
                ('cache-status', 'Ver estado de caches', ''),
            ],
        ),
    ]

    for section_name, commands in sections:
        print()
        print(f'  {_c(CYAN, section_name)}')
        print(f'  {"-" * 56}')
        for cmd_name, description, usage in commands:
            line = f'    {_c(GREEN, cmd_name):<30s} {description}'
            if usage:
                line += f'  {_c(DIM, usage)}'
            print(line)

    print()
    print(f'  {_c(YELLOW, "Flags globales:")}')
    print(
        f'    {_c(GREEN, "--env=<env>"):<30s} '
        'Ambiente (local|dev|test|stage|prod, default: local)'
    )
    print(
        f'    {_c(GREEN, "--output=json"):<30s} '
        'Output estructurado para comandos que lo soportan'
    )
    print(
        f'    {_c(GREEN, "--dry-run"):<30s} '
        'Imprime acciones sin ejecutar (rebuild, clean, db-reset, refresh)'
    )
    print()
    print(f'  {_c(DIM, "Para tests, usa: python devtools/run.py test_runner")}')
    print()

    return 0
