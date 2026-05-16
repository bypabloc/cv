"""Unit tests para devtools/verify/main.py."""

from __future__ import annotations

from typing import Any

import pytest
from verify.main import build_reports
from verify.main import classify_file
from verify.main import collect_changed_files
from verify.main import deduplicate_commands
from verify.main import verifications_for


pytestmark = pytest.mark.unit


class TestClassifyFile:
    """Clasificación correcta de archivos por path."""

    @pytest.mark.parametrize(
        'path,expected',
        [
            ('server/apps/products/models/product.py', 'server_model'),
            ('server/apps/products/models.py', 'server_model'),
            ('server/apps/products/services/creation.py', 'server_service'),
            ('server/apps/products/selectors/queries.py', 'server_selector'),
            ('server/apps/products/views/list.py', 'server_view'),
            ('server/apps/products/views.py', 'server_view'),
            ('server/apps/products/serializers/input.py', 'server_serializer'),
            ('server/apps/products/serializers.py', 'server_serializer'),
            ('server/apps/products/tasks/process.py', 'server_task'),
            ('server/apps/products/utils.py', 'server_python'),
            ('dashboard/app/components/foo.vue', 'dashboard_typescript'),
            ('dashboard/stores/useFoo.ts', 'dashboard_typescript'),
            ('dashboard/biome.json', 'dashboard_other'),
            ('landing/src/pages/index.astro', 'landing_typescript'),
            ('landing/src/components/Foo.ts', 'landing_typescript'),
            ('landing/biome.json', 'landing_other'),
            ('devtools/scan/main.py', 'devtools_python'),
            ('.claude/settings.json', 'claude_json'),
            ('.claude/hooks/foo.sh', 'claude_shell'),
            ('.claude/agents/foo.md', 'claude_other'),
            ('docs/guide/01.md', 'other'),
        ],
    )
    def test_classify_known_paths(self, path: str, expected: str) -> None:
        """Cada path debe clasificarse en su categoria correcta."""
        assert classify_file(path) == expected

    @pytest.mark.parametrize(
        'path',
        [
            'server/tests/unit/src/foo.py',
            'server/apps/products/migrations/0001_initial.py',
            'server/apps/products/__init__.py',
            'server/apps/products/services/__init__.py',
        ],
    )
    def test_test_migration_init_skipped(self, path: str) -> None:
        """Tests, migrations, __init__: clasificados como skip."""
        assert classify_file(path) == 'test_or_migration_or_init'


class TestVerificationsFor:
    """Reglas de verificación por clasificación."""

    def test_server_model_includes_makemigrations(self) -> None:
        verifs = verifications_for('server_model')
        cmds = [v.cmd for v in verifs]
        assert any('makemigrations --dry-run' in c for c in cmds)

    def test_server_view_includes_integration(self) -> None:
        verifs = verifications_for('server_view')
        cmds = [v.cmd for v in verifs]
        assert any('--type=integration' in c for c in cmds)

    def test_dashboard_typescript_includes_typecheck(self) -> None:
        verifs = verifications_for('dashboard_typescript')
        cmds = [v.cmd for v in verifs]
        assert any('typecheck' in c and '--module=dashboard' in c for c in cmds)

    def test_landing_typescript_includes_typecheck(self) -> None:
        verifs = verifications_for('landing_typescript')
        cmds = [v.cmd for v in verifs]
        assert any('typecheck' in c and '--module=landing' in c for c in cmds)

    def test_claude_json_includes_json_validation(self) -> None:
        verifs = verifications_for('claude_json')
        cmds = [v.cmd for v in verifs]
        assert any('json.tool' in c for c in cmds)

    def test_claude_shell_includes_bash_syntax(self) -> None:
        verifs = verifications_for('claude_shell')
        cmds = [v.cmd for v in verifs]
        assert any('bash -n' in c for c in cmds)

    @pytest.mark.parametrize(
        'classification',
        [
            'test_or_migration_or_init',
            'server_other',
            'dashboard_other',
            'landing_other',
            'other',
        ],
    )
    def test_skip_classifications_return_empty(
        self,
        classification: str,
    ) -> None:
        """Clasificaciones de skip retornan lista vacía."""
        assert verifications_for(classification) == []


class TestBuildReports:
    """Construcción de reportes a partir de lista de archivos."""

    def test_builds_one_report_per_file(self) -> None:
        files = [
            'server/apps/foo/models/bar.py',
            'dashboard/app/foo.vue',
        ]
        reports = build_reports(files)
        assert len(reports) == 2
        assert reports[0].file == files[0]
        assert reports[0].classification == 'server_model'
        assert reports[1].classification == 'dashboard_typescript'

    def test_empty_files_returns_empty(self) -> None:
        assert build_reports([]) == []

    def test_skipped_file_has_empty_verifications(self) -> None:
        reports = build_reports(['server/tests/unit/src/foo.py'])
        assert reports[0].verifications == []


class TestDeduplicateCommands:
    """Deduplicacion: el mismo cmd de varios files solo aparece una vez."""

    def test_duplicate_cmds_collapsed(self) -> None:
        files = [
            'server/apps/foo/services/a.py',
            'server/apps/foo/services/b.py',
            'server/apps/foo/services/c.py',
        ]
        reports = build_reports(files)
        unique = deduplicate_commands(reports)
        # Los 3 services activan los mismos 2 cmds (lint + unit tests).
        assert len(unique) == 2

    def test_different_cmds_not_collapsed(self) -> None:
        files = [
            'server/apps/foo/models/a.py',
            'dashboard/app/b.vue',
        ]
        reports = build_reports(files)
        unique = deduplicate_commands(reports)
        # Server model: 3 cmds. App TS: 2 cmds. Lint server compartido entre los models.
        # Total únicos esperado: makemigrations + lint server + unit tests + typecheck dashboard + lint dashboard = 5.
        assert len(unique) == 5

    def test_empty_reports_returns_empty(self) -> None:
        assert deduplicate_commands([]) == []


class TestCollectChangedFilesUsesScan:
    """``collect_changed_files`` debe delegar en ``scan_helper.files_changed``.

    Estos tests aseguran el contrato del refactor: verify ya no invoca git
    directo, sino que pasa por scan (la fuente canonica). El mapeo flag ->
    git_mode es la única lógica que vive en verify.
    """

    @pytest.fixture
    def fake_scan(self, monkeypatch: pytest.MonkeyPatch) -> dict[str, Any]:
        """Reemplaza ``files_changed`` capturando el ``git_mode`` recibido."""
        captured: dict[str, Any] = {'calls': []}

        def fake_files_changed(*, git_mode: str) -> list[str]:
            captured['calls'].append(git_mode)
            return captured.get('return_value', [])

        # Importamos dentro del fixture para asegurar que el monkeypatch
        # afecta al módulo correcto cuando ``verify.main`` lo importa lazy.
        import verify.main as verify_main

        monkeypatch.setattr(
            verify_main,
            'files_changed',
            fake_files_changed,
        )
        return captured

    def test_staged_maps_to_scan_staged(
        self,
        fake_scan: dict[str, Any],
    ) -> None:
        """``--staged`` -> ``files_changed(git_mode='staged')``."""
        fake_scan['return_value'] = ['server/apps/x/models/y.py']

        result = collect_changed_files({'staged': True})

        assert fake_scan['calls'] == ['staged']
        assert result == ['server/apps/x/models/y.py']

    def test_modified_maps_to_scan_unstaged(
        self,
        fake_scan: dict[str, Any],
    ) -> None:
        """``--modified`` -> ``files_changed(git_mode='unstaged')``."""
        fake_scan['return_value'] = ['dashboard/app/foo.vue']

        result = collect_changed_files({'modified': True})

        assert fake_scan['calls'] == ['unstaged']
        assert result == ['dashboard/app/foo.vue']

    def test_default_maps_to_scan_changed(
        self,
        fake_scan: dict[str, Any],
    ) -> None:
        """Sin flag (all_changed) -> ``files_changed(git_mode='changed')``."""
        fake_scan['return_value'] = [
            '.claude/settings.json',
            'server/apps/x/services/y.py',
        ]

        result = collect_changed_files({})

        assert fake_scan['calls'] == ['changed']
        # collect_changed_files debe retornar lista ordenada.
        assert result == sorted(result)

    def test_all_changed_explicit_maps_to_scan_changed(
        self,
        fake_scan: dict[str, Any],
    ) -> None:
        """``--all-changed`` explicito también mapea a ``changed``."""
        fake_scan['return_value'] = []

        result = collect_changed_files({'all_changed': True})

        assert fake_scan['calls'] == ['changed']
        assert result == []

    def test_empty_scan_returns_empty(
        self,
        fake_scan: dict[str, Any],
    ) -> None:
        """Si scan no detecta nada, verify retorna lista vacía (sin error)."""
        fake_scan['return_value'] = []

        result = collect_changed_files({'staged': True})

        assert result == []

    def test_includes_paths_outside_modules(
        self,
        fake_scan: dict[str, Any],
    ) -> None:
        """Archivos fuera de módulos de scan (.claude/, root) deben aparecer.

        Como ``files_changed`` no filtra por módulo, archivos en ``.claude/``,
        ``docs/`` o root del proyecto pasan. verify los clasifica luego.
        """
        fake_scan['return_value'] = [
            '.claude/settings.json',
            'docs/guide/01.md',
            'server/apps/x/views.py',
        ]

        result = collect_changed_files({'staged': True})

        assert '.claude/settings.json' in result
        assert 'docs/guide/01.md' in result
        assert 'server/apps/x/views.py' in result
