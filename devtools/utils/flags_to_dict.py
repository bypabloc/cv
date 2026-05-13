"""CLI flag parsing utilities for devtools scripts.

``flags_to_dict`` parsea ``sys.argv`` (sin el script name) en un dict tipado
con strings, ints inferidos por el caller, y bools (`--foo` sin valor).

Comportamiento de listas: por defecto, valores con `|` se devuelven COMO
STRING. Para que un flag se trate como lista (y se haga split por `|`), el
caller debe declararlo en ``list_flags``. Esta opcion explicita reemplaza
el viejo comportamiento de splittear cualquier valor con ``|`` — que era
magia silenciosa: si pasabas ``--name="alice|bob"`` esperando un string
recibias una lista sin saberlo.

Separador POSIX ``--``: cualquier ``--`` aislado en ``args_list`` detiene
el parseo de flags. Lo que sigue se acumula en la key ``_passthrough``
(lista de strings). Esto le permite a comandos como ``docker exec`` o
``docker manage`` pasar flags arbitrarias al subproceso sin que el
validador de flags del propio script las rechace. Ejemplo:

    docker exec --target=server -- python -c 'print(1)'

el parser produce ``{'target': 'server', '_passthrough': ['python', '-c',
'print(1)']}``, y el comando docker concatena ``_passthrough`` a sus
``subcommands`` antes de ejecutar.

Migracion: scripts que dependen de listas (scan: ``excludes_extension``,
``only_extension``, ``ignore_patterns``) ahora normalizan via su propio
validador (ej. ``_clean_extensions``) que ya aceptaba ``str | list[str]``.
"""

from typing import Any


# Set de flags que SI se splitean por '|'. Cada script con flags-lista
# extiende este set via run.py al construir el dict (ver _list_flags_for).
_DEFAULT_LIST_FLAGS: set[str] = set()


def flags_to_dict(
    args_list: list[str],
    *,
    list_flags: set[str] | None = None,
) -> dict[str, str | list[str] | bool]:
    """Parse CLI ``--key=value``/``--flag`` arguments into a typed dict.

    Args:
        args_list: argv slice (without the script name).
        list_flags: optional set of flag names (post hyphen-to-underscore
            normalization) that should be parsed as lists when their value
            contains ``|``. Flags outside this set keep ``|`` as part of
            the string. Defaults to an empty set, so the explicit opt-in
            beats the old "split anything with a pipe" silent behaviour.

    Returns:
        Dict with normalized flag names (hyphens -> underscores). Values
        are bool (presence-only flags), str (default), or list[str] (when
        the flag opted into list parsing and contained ``|``). If ``--``
        appears as a standalone token, everything after is collected into
        the special key ``_passthrough`` (list[str]). The key is omitted
        when no ``--`` is present, to keep the contract minimal for
        callers that don't care.

    Examples:
        >>> flags_to_dict(['--only-folders-root'])
        {'only_folders_root': True}
        >>> flags_to_dict(['--name=alice|bob'])
        {'name': 'alice|bob'}
        >>> flags_to_dict(
        ...     ['--ignore=foo|bar'],
        ...     list_flags={'ignore'},
        ... )
        {'ignore': ['foo', 'bar']}
        >>> flags_to_dict(['--target=server', '--', 'echo', 'hello'])
        {'target': 'server', '_passthrough': ['echo', 'hello']}
    """
    list_flags = list_flags if list_flags is not None else _DEFAULT_LIST_FLAGS
    flags_dict: dict[str, str | list[str] | bool] = {}
    passthrough: list[str] | None = None

    for raw_arg in args_list:
        if passthrough is not None:
            passthrough.append(raw_arg)
            continue

        if raw_arg == '--':
            passthrough = []
            continue

        if not raw_arg.startswith('--'):
            continue

        arg = raw_arg[2:]

        if '=' in arg:
            flag_name, flag_value = arg.split('=', 1)
            flag_name = flag_name.replace('-', '_')

            if (flag_value.startswith('"') and flag_value.endswith('"')) or (
                flag_value.startswith("'") and flag_value.endswith("'")
            ):
                flag_value = flag_value[1:-1]

            if flag_name in list_flags and '|' in flag_value:
                flags_dict[flag_name] = flag_value.split('|')
            else:
                flags_dict[flag_name] = flag_value
        else:
            flag_name = arg.replace('-', '_')
            flags_dict[flag_name] = True

    if passthrough is not None:
        flags_dict['_passthrough'] = passthrough

    return flags_dict


def validate_required_flags(
    flags_dict: dict[str, Any],
    required_flags: list[str],
) -> None:
    """Raise ValueError if any required flag is missing from ``flags_dict``."""
    missing_flags = [flag for flag in required_flags if flag not in flags_dict]

    if missing_flags:
        raise ValueError(
            f'Flags requeridas faltantes: {", ".join(missing_flags)}',
        )


def validate_allowed_flags(
    flags_dict: dict[str, Any],
    allowed_flags: list[str],
) -> None:
    """Raise ValueError if ``flags_dict`` contains flags outside ``allowed_flags``.

    System flags (``_invoked_from``, ``list_commands``, ``list_flags``,
    ``describe``, ``output``) are always valid since they are consumed by
    ``run.py`` before the script's own validator runs.
    """
    system_flags = {
        '_invoked_from',
        '_passthrough',
        'list_commands',
        'list_flags',
        'list_scripts',
        'describe',
        'output',
        'help',
    }

    invalid_flags = [
        flag
        for flag in flags_dict
        if flag not in allowed_flags and flag not in system_flags
    ]

    if invalid_flags:
        raise ValueError(f'Flags no permitidas: {", ".join(invalid_flags)}')


def set_default_values(
    flags_dict: dict[str, Any],
    defaults: dict[str, Any],
) -> dict[str, Any]:
    """Populate ``flags_dict`` with ``defaults`` for any unset flag."""
    for flag, default_value in defaults.items():
        if flag not in flags_dict:
            flags_dict[flag] = default_value

    return flags_dict
