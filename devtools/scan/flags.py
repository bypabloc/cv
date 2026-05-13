import os
import sys
from typing import Any

from utils.describe import ScriptDescribe
from utils.flags_to_dict import set_default_values
from utils.flags_to_dict import validate_allowed_flags


# Anadir el directorio padre al path para poder importar utils
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))


ALLOWED_FLAGS = [
    'include_ignored',
    'excludes_extension',
    'only_extension',
    'only_folders_root',
    'only_list',
    'include_deleted',
    'exclude_empty',
    'ignore_patterns',
    'git_mode',
    'module',
    'purpose',
    'help',
]

DEFAULTS = {
    'include_ignored': False,
    'excludes_extension': [],
    'only_extension': [],
    'only_folders_root': False,
    'only_list': False,
    'include_deleted': False,
    'exclude_empty': False,
    'ignore_patterns': [],
    'git_mode': None,
    'module': None,
    'purpose': None,
    '_invoked_from': 'python',
}


def get_valid_git_modes() -> list[str]:
    """
    Obtiene lista de modos git válidos.

    Returns
    -------
    list[str]
        Lista de modos git válidos como 'changed', 'staged', 'unstaged', etc.
    """
    return ['changed', 'staged', 'unstaged', 'stash', 'unmerged', 'all']


def _clean_extensions(extensions: str | list[str]) -> list[str]:
    """
    Normaliza extensiones: convierte a lista y limpia prefijo punto.

    Parameters
    ----------
    extensions : str | list[str]
        Extensión o lista de extensiones a limpiar.

    Returns
    -------
    list[str]
        Lista de extensiones en minuscula sin punto inicial.
    """
    if isinstance(extensions, str):
        extensions = [extensions]
    return [ext.removeprefix('.').lower() for ext in extensions]


def _validate_git_mode(flags_dict: dict[str, Any]) -> None:
    """Válida que git_mode sea uno de los valores permitidos."""
    git_mode = flags_dict.get('git_mode')
    if not git_mode:
        return

    valid_git_modes = get_valid_git_modes()
    if git_mode not in valid_git_modes:
        raise ValueError(
            f'git_mode debe ser uno de: {", ".join(valid_git_modes)}. '
            f'Recibido: {git_mode}',
        )


def _validate_extensions(flags_dict: dict[str, Any]) -> None:
    """Válida y normaliza excludes_extension y only_extension."""
    if flags_dict.get('excludes_extension'):
        flags_dict['excludes_extension'] = _clean_extensions(
            flags_dict['excludes_extension'],
        )

    if flags_dict.get('only_extension'):
        flags_dict['only_extension'] = _clean_extensions(
            flags_dict['only_extension'],
        )

        if flags_dict.get('excludes_extension'):
            raise ValueError(
                'No se puede usar --only-extensión junto con '
                '--excludes-extensión. Use una u otra.'
            )


def _validate_ignore_patterns(flags_dict: dict[str, Any]) -> None:
    """Válida y normaliza ignore_patterns."""
    if not flags_dict.get('ignore_patterns'):
        return

    if isinstance(flags_dict['ignore_patterns'], str):
        flags_dict['ignore_patterns'] = [
            pattern.strip()
            for pattern in flags_dict['ignore_patterns'].split('|')
            if pattern.strip()
        ]

    flags_dict['ignore_patterns'] = [
        pattern.strip()
        for pattern in flags_dict['ignore_patterns']
        if pattern and pattern.strip()
    ]


def _validate_module(flags_dict: dict[str, Any]) -> None:
    """Válida --module y aplica config del module (extensions, exclude patterns)."""
    if not flags_dict.get('module'):
        return

    from scan.modules import get_module
    from scan.modules import get_module_names

    try:
        module_config = get_module(flags_dict['module'])
    except ValueError:
        valid_modules = ', '.join(get_module_names())
        raise ValueError(
            f'Module inválido: {flags_dict["module"]}. Modules válidos: {valid_modules}'
        ) from None

    # Module sobreescribe extensions y agrega exclude patterns
    if not flags_dict.get('only_extension'):
        flags_dict['only_extension'] = module_config.get('extensions', [])

    module_excludes = module_config.get('exclude_patterns', [])
    existing_patterns = flags_dict.get('ignore_patterns', [])
    flags_dict['ignore_patterns'] = existing_patterns + module_excludes

    # Guardar config del module para uso en main.py
    flags_dict['_module_config'] = module_config


def _validate_purpose(flags_dict: dict[str, Any]) -> None:
    """Válida --purpose y agrega sus exclude patterns."""
    if not flags_dict.get('purpose'):
        return

    from scan.modules import VALID_PURPOSES

    if flags_dict['purpose'] not in VALID_PURPOSES:
        raise ValueError(
            f'Purpose inválido: {flags_dict["purpose"]}. '
            f'Válidos: {", ".join(VALID_PURPOSES)}'
        )

    if not flags_dict.get('module'):
        raise ValueError(
            '--purpose requiere --module. '
            'Ejemplo: --module=server --purpose=conformance'
        )

    # Agregar excludes de purpose a ignore_patterns
    from scan.modules import get_purpose_excludes

    purpose_excludes = get_purpose_excludes(
        flags_dict['module'],
        flags_dict['purpose'],
    )
    flags_dict['ignore_patterns'] = (
        flags_dict.get('ignore_patterns', []) + purpose_excludes
    )


def _print_processed_flags(flags_dict: dict[str, Any]) -> None:
    """Muestra informacion de las flags procesadas (excepto en modo lista)."""
    if flags_dict.get('only_list', False):
        return

    print('Flags procesadas:')
    for flag_name, flag_value in flags_dict.items():
        if not flag_value or flag_name == 'help' or flag_name.startswith('_'):
            continue

        if isinstance(flag_value, list) and flag_value:
            print(f'  --{flag_name.replace("_", "-")}: {", ".join(flag_value)}')
        elif flag_value is True:
            print(f'  --{flag_name.replace("_", "-")}')
        elif flag_value:
            print(f'  --{flag_name.replace("_", "-")}: {flag_value}')


def flag(flags_dict: dict[str, Any]) -> dict[str, Any]:
    """
    Procesa y válida las flags para el script scan.

    Parameters
    ----------
    flags_dict : dict
        Diccionario de flags ya procesado por run.py

    Returns
    -------
    dict
        Diccionario con las flags procesadas y validadas con valores por defecto

    Raises
    ------
    ValueError
        Si se usan flags no permitidas o valores inválidos
    """
    validate_allowed_flags(flags_dict, ALLOWED_FLAGS)
    flags_dict = set_default_values(flags_dict, DEFAULTS)

    _validate_git_mode(flags_dict)
    _validate_extensions(flags_dict)
    _validate_ignore_patterns(flags_dict)
    _validate_module(flags_dict)
    _validate_purpose(flags_dict)
    _print_processed_flags(flags_dict)

    return flags_dict


def describe() -> ScriptDescribe:
    """Machine-readable inventory of scan flags."""
    return {
        'name': 'scan',
        'kind': 'monocommand',
        'summary': 'Lista archivos del repo (git-aware) con filtros y contenido',
        'commands': [],
        'flags': {
            'git_mode': {
                'type': 'choice',
                'choices': get_valid_git_modes(),
                'summary': 'Filtra por estado git',
            },
            'module': {
                'type': 'choice',
                'choices': ['server', 'dashboard', 'landing', 'devtools'],
                'summary': 'Limita a un módulo del proyecto',
            },
            'purpose': {
                'type': 'choice',
                'choices': ['conformance', 'coverage'],
                'summary': 'Aplica excludes especificos del proposito',
            },
            'include_ignored': {
                'type': 'bool',
                'default': False,
                'summary': 'Incluye archivos ignorados por git',
            },
            'excludes_extension': {
                'type': 'list',
                'summary': 'Extensiones a excluir (separadas por |)',
            },
            'only_extension': {
                'type': 'list',
                'summary': 'Solo extensiones (separadas por |)',
            },
            'only_folders_root': {
                'type': 'bool',
                'default': False,
                'summary': 'Solo lista carpetas raíz del proyecto',
            },
            'only_list': {
                'type': 'bool',
                'default': False,
                'summary': 'Output ; -separado (machine-readable)',
            },
            'include_deleted': {
                'type': 'bool',
                'default': False,
                'summary': 'Incluye archivos eliminados (modo unmerged)',
            },
            'exclude_empty': {
                'type': 'bool',
                'default': False,
                'summary': 'Omite archivos vacíos',
            },
            'ignore_patterns': {
                'type': 'list',
                'summary': 'Patterns glob/regex a excluir',
            },
        },
    }
