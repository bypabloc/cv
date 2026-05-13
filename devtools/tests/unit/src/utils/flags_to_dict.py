"""Unit tests for utils.flags_to_dict.

Path mirroring: devtools/utils/flags_to_dict.py -> this file.

Cubre el cambio de comportamiento de Fase 6: el split por ``|`` ahora es
opt-in via el parámetro ``list_flags``. Antes cualquier valor con ``|``
se convertia silenciosamente en lista, lo cual sorprendia cuando el
flag esperaba un string.
"""

import pytest


pytestmark = pytest.mark.unit


# ---------------------------------------------------------------------------
# flags_to_dict — basic parsing
# ---------------------------------------------------------------------------


class TestBasicParsing:
    def test_boolean_flag(self):
        from utils.flags_to_dict import flags_to_dict

        assert flags_to_dict(['--verbose']) == {'verbose': True}

    def test_string_value(self):
        from utils.flags_to_dict import flags_to_dict

        assert flags_to_dict(['--env=local']) == {'env': 'local'}

    def test_hyphen_to_underscore(self):
        from utils.flags_to_dict import flags_to_dict

        assert flags_to_dict(['--git-mode=staged']) == {'git_mode': 'staged'}

    def test_quoted_value_strips_quotes(self):
        from utils.flags_to_dict import flags_to_dict

        assert flags_to_dict(['--name="alice"']) == {'name': 'alice'}
        assert flags_to_dict(["--name='bob'"]) == {'name': 'bob'}

    def test_non_dash_args_ignored(self):
        from utils.flags_to_dict import flags_to_dict

        assert flags_to_dict(['positional', '--env=local']) == {
            'env': 'local',
        }


# ---------------------------------------------------------------------------
# Pipe-separated lists — Fase 6 opt-in
# ---------------------------------------------------------------------------


class TestListFlagsOptIn:
    """Por default, ``|`` en un valor se preserva como string."""

    def test_pipe_in_value_stays_string_by_default(self):
        from utils.flags_to_dict import flags_to_dict

        assert flags_to_dict(['--name=alice|bob']) == {'name': 'alice|bob'}

    def test_list_flags_splits_on_pipe(self):
        from utils.flags_to_dict import flags_to_dict

        result = flags_to_dict(
            ['--ignore=foo|bar|baz'],
            list_flags={'ignore'},
        )
        assert result == {'ignore': ['foo', 'bar', 'baz']}

    def test_list_flags_without_pipe_stays_string(self):
        # Si la flag opto-in pero no hay pipe, sigue siendo string.
        # Validators downstream (ej. _clean_extensions) lo normalizan.
        from utils.flags_to_dict import flags_to_dict

        result = flags_to_dict(
            ['--ignore=onlyone'],
            list_flags={'ignore'},
        )
        assert result == {'ignore': 'onlyone'}

    def test_unrelated_flag_with_pipe_stays_string(self):
        from utils.flags_to_dict import flags_to_dict

        # ``name`` no esta en list_flags -> el pipe se preserva.
        result = flags_to_dict(
            ['--name=alice|bob', '--ignore=foo|bar'],
            list_flags={'ignore'},
        )
        assert result == {
            'name': 'alice|bob',
            'ignore': ['foo', 'bar'],
        }

    def test_empty_list_flags_means_no_split(self):
        from utils.flags_to_dict import flags_to_dict

        result = flags_to_dict(
            ['--anything=a|b|c'],
            list_flags=set(),
        )
        assert result == {'anything': 'a|b|c'}


# ---------------------------------------------------------------------------
# validate_allowed_flags
# ---------------------------------------------------------------------------


class TestValidateAllowedFlags:
    def test_allowed_flag_passes(self):
        from utils.flags_to_dict import validate_allowed_flags

        validate_allowed_flags({'env': 'local'}, ['env'])

    def test_disallowed_flag_raises(self):
        from utils.flags_to_dict import validate_allowed_flags

        with pytest.raises(ValueError, match='Flags no permitidas: foo'):
            validate_allowed_flags({'foo': 'x'}, ['env'])

    def test_system_flags_always_allowed(self):
        # _invoked_from, list_commands, list_flags, list_scripts, describe,
        # output, help son consumidos por run.py antes del validador del
        # script.
        from utils.flags_to_dict import validate_allowed_flags

        validate_allowed_flags(
            {
                '_invoked_from': 'cli',
                'list_commands': True,
                'list_flags': True,
                'list_scripts': True,
                'describe': True,
                'output': 'json',
                'help': True,
            },
            allowed_flags=[],
        )


class TestSetDefaultValues:
    def test_unset_flag_gets_default(self):
        from utils.flags_to_dict import set_default_values

        result = set_default_values({}, {'env': 'local'})
        assert result == {'env': 'local'}

    def test_set_flag_keeps_value(self):
        from utils.flags_to_dict import set_default_values

        result = set_default_values({'env': 'prod'}, {'env': 'local'})
        assert result == {'env': 'prod'}


# ---------------------------------------------------------------------------
# POSIX double-dash separator (`--`) — pass-through args
# ---------------------------------------------------------------------------


class TestDoubleDashPassthrough:
    """`--` aislado detiene el parseo y deja el resto en `_passthrough`.

    Esto permite que comandos pass-through como ``docker exec`` o
    ``docker manage`` reciban flags arbitrarias sin que el validador
    del CLI las rechace. El orden POSIX importa: ``foo --bar -- baz
    --quux`` parsea ``--bar`` como flag normal y ``baz --quux`` como
    passthrough.
    """

    def test_no_double_dash_omits_passthrough_key(self):
        from utils.flags_to_dict import flags_to_dict

        result = flags_to_dict(['--env=local'])
        assert '_passthrough' not in result

    def test_double_dash_alone_creates_empty_passthrough(self):
        from utils.flags_to_dict import flags_to_dict

        result = flags_to_dict(['--env=local', '--'])
        assert result == {'env': 'local', '_passthrough': []}

    def test_args_after_double_dash_go_to_passthrough(self):
        from utils.flags_to_dict import flags_to_dict

        result = flags_to_dict(
            ['--target=server', '--', 'echo', 'hello'],
        )
        assert result == {
            'target': 'server',
            '_passthrough': ['echo', 'hello'],
        }

    def test_flags_after_double_dash_kept_verbatim(self):
        # Esto es el caso clave: '--list' después del '--' NO se parsea
        # como flag CLI; va al subproceso tal cual.
        from utils.flags_to_dict import flags_to_dict

        result = flags_to_dict(
            ['--', 'showmigrations', '--list', '--verbosity=2'],
        )
        assert result == {
            '_passthrough': ['showmigrations', '--list', '--verbosity=2'],
        }

    def test_double_dash_inside_value_not_treated_as_separator(self):
        # '--foo=--bar' contiene '--' pero no es el token POSIX. Debe
        # parsearse como flag normal con valor '--bar'.
        from utils.flags_to_dict import flags_to_dict

        result = flags_to_dict(['--foo=--bar'])
        assert result == {'foo': '--bar'}

    def test_passthrough_is_system_flag_in_validate(self):
        # El validador no debe rechazar '_passthrough' como flag
        # desconocida, sino tratarla como system flag.
        from utils.flags_to_dict import validate_allowed_flags

        validate_allowed_flags({'_passthrough': ['echo', 'hi']}, ['env'])
