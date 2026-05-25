"""Unit tests para devtools/shared/scan_helper.py."""

from __future__ import annotations

from typing import Any

import pytest

from shared.scan_helper import files_changed
from shared.scan_helper import files_for_module


pytestmark = pytest.mark.unit


class TestFilesChanged:
    """``files_changed`` envuelve ``scan.main.get_project_structure``."""

    @pytest.fixture
    def fake_structure(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> dict[str, Any]:
        """Replace ``get_project_structure`` capturing flags + returning fake data."""
        captured: dict[str, Any] = {'calls': []}

        def fake_get_project_structure(flags: dict[str, Any]) -> dict[str, Any]:
            captured['calls'].append(dict(flags))
            return captured.get('return_value', {'files': {}})

        import scan.main as scan_main

        monkeypatch.setattr(
            scan_main,
            'get_project_structure',
            fake_get_project_structure,
        )
        return captured

    def test_passes_git_mode_to_scan(
        self,
        fake_structure: dict[str, Any],
    ) -> None:
        """El git_mode pasado debe llegar tal cual a scan."""
        fake_structure['return_value'] = {
            'files': {'a.py': {}, 'b.ts': {}},
        }

        files_changed(git_mode='staged')

        assert len(fake_structure['calls']) == 1
        assert fake_structure['calls'][0]['git_mode'] == 'staged'

    def test_default_mode_is_changed(
        self,
        fake_structure: dict[str, Any],
    ) -> None:
        """Sin git_mode explicito, default 'changed' (staged+unstaged+untracked)."""
        fake_structure['return_value'] = {'files': {}}

        files_changed()

        assert fake_structure['calls'][0]['git_mode'] == 'changed'

    def test_does_not_pass_module_filters(
        self,
        fake_structure: dict[str, Any],
    ) -> None:
        """``files_changed`` no debe limitar por módulo ni extensiones.

        Así captura archivos de .claude/, docs/, root: todo lo cambiado.
        """
        fake_structure['return_value'] = {'files': {}}

        files_changed(git_mode='staged')

        flags = fake_structure['calls'][0]
        assert '_module_config' not in flags
        assert flags.get('only_extension') in (None, [])
        assert flags.get('ignore_patterns', []) == []

    def test_returns_sorted_file_paths(
        self,
        fake_structure: dict[str, Any],
    ) -> None:
        """Resultado ordenado para output deterministico."""
        fake_structure['return_value'] = {
            'files': {
                'z.py': {},
                'a.py': {},
                'm.py': {},
            },
        }

        result = files_changed(git_mode='changed')

        assert result == ['a.py', 'm.py', 'z.py']

    def test_empty_structure_returns_empty(
        self,
        fake_structure: dict[str, Any],
    ) -> None:
        """Estructura vacía o ``None`` -> lista vacía, sin excepciones."""
        fake_structure['return_value'] = {}

        assert files_changed(git_mode='staged') == []

    def test_disables_include_ignored(
        self,
        fake_structure: dict[str, Any],
    ) -> None:
        """No incluir archivos en .gitignore (igual que en hooks)."""
        fake_structure['return_value'] = {'files': {}}

        files_changed(git_mode='changed')

        assert fake_structure['calls'][0]['include_ignored'] is False

    def test_disables_include_deleted(
        self,
        fake_structure: dict[str, Any],
    ) -> None:
        """Filtrar archivos eliminados es la mejora clave vs git directo."""
        fake_structure['return_value'] = {'files': {}}

        files_changed(git_mode='changed')

        assert fake_structure['calls'][0]['include_deleted'] is False


class TestFilesForModule:
    """``files_for_module`` filtra por root + extensiones del módulo."""

    @pytest.fixture
    def fake_structure(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> dict[str, Any]:
        captured: dict[str, Any] = {'calls': []}

        def fake_get_project_structure(flags: dict[str, Any]) -> dict[str, Any]:
            captured['calls'].append(dict(flags))
            return captured.get('return_value', {'files': {}})

        import scan.main as scan_main

        monkeypatch.setattr(
            scan_main,
            'get_project_structure',
            fake_get_project_structure,
        )
        return captured

    def test_passes_module_config_and_extensions(
        self,
        fake_structure: dict[str, Any],
    ) -> None:
        """``_module_config`` + ``only_extension`` deben llegar a scan."""
        fake_structure['return_value'] = {'files': {}}

        files_for_module(module='server', git_mode='staged')

        flags = fake_structure['calls'][0]
        assert flags['module'] == 'server'
        assert flags['git_mode'] == 'staged'
        assert flags['only_extension'] == ['py']
        assert flags['_module_config']['root'] == 'server/'

    def test_filters_by_extension_suffix(
        self,
        fake_structure: dict[str, Any],
    ) -> None:
        """Solo archivos con extension valida del modulo deben volver."""
        fake_structure['return_value'] = {
            'files': {
                'server/x.py': {},
                'server/x.pyi': {},  # .pyi NO esta en extensions
                'server/y.txt': {},
                'server/z.md': {},
            },
        }

        result = files_for_module(module='server', git_mode='changed')

        # 'server' modulo solo permite 'py' (no 'pyi'/'txt'/'md').
        assert sorted(result) == ['server/x.py']

    def test_purpose_appends_excludes(
        self,
        fake_structure: dict[str, Any],
    ) -> None:
        """``purpose='coverage'`` debe sumar los excludes especificos.

        El modulo 'server' tiene purpose_excludes['coverage']=[] (es stub).
        Probamos con 'generic' (app Astro) que SI tiene coverage excludes
        documentados ('tests/**', '*.config.ts').
        """
        fake_structure['return_value'] = {'files': {}}

        files_for_module(
            module='generic',
            git_mode='staged',
            purpose='coverage',
        )

        flags = fake_structure['calls'][0]
        # ignore_patterns debe contener los exclude_patterns base + los
        # purpose_excludes para coverage (apps/generic/tests/** + *.config.ts).
        assert any(
            'apps/generic/tests/**' in p for p in flags['ignore_patterns']
        )
        assert any('*.config.ts' in p for p in flags['ignore_patterns'])
