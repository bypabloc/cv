"""Unit tests for serverless.change_detector - detector de lambdas afectados.

Path mirroring: devtools/serverless/change_detector.py -> this file.

Verifica:
- classify_path detecta cambios de service / shared / ignore con sus
  excepciones (tests/, events/, build/, core/seeds/data/).
- detect_affected_lambdas combina cambios directos + cierre transitivo
  via shared_resolver real.
- cmd_detect_changes imprime JSON y maneja errores de CLI.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from serverless.change_detector import ChangeKind
from serverless.change_detector import classify_path
from serverless.change_detector import detect_affected_lambdas


pytestmark = pytest.mark.unit


# ---------------------------------------------------------------------------
# classify_path
# ---------------------------------------------------------------------------


class TestClassifyPath:
    """classify_path mapea un path a service / shared / ignore."""

    def test_service_core_dispara_redeploy(self):
        """
        Given un path 'serverless/lambda/services/cv/core/handler.py',
        When invoco classify_path,
        Then devuelve ChangeKind(kind='service', name='cv').
        """
        assert classify_path(
            'serverless/lambda/services/cv/core/handler.py'
        ) == ChangeKind(kind='service', name='cv')

    def test_service_pyproject_dispara_redeploy(self):
        """
        Given un path 'serverless/lambda/services/cv/pyproject.toml',
        When invoco classify_path,
        Then devuelve ChangeKind(kind='service', name='cv').
        """
        assert classify_path(
            'serverless/lambda/services/cv/pyproject.toml'
        ) == ChangeKind(kind='service', name='cv')

    def test_service_tests_no_dispara(self):
        """
        Given un path tests/ del lambda,
        When invoco classify_path,
        Then devuelve kind='ignore' (tests no van al zip).
        """
        assert classify_path(
            'serverless/lambda/services/cv/tests/unit/test_x.py'
        ) == ChangeKind(kind='ignore')

    def test_service_events_no_dispara(self):
        """
        Given un path events/ del lambda,
        When invoco classify_path,
        Then devuelve kind='ignore' (eventos son input local).
        """
        assert classify_path(
            'serverless/lambda/services/db/events/migrate.json'
        ) == ChangeKind(kind='ignore')

    def test_service_build_no_dispara(self):
        """
        Given un path build/ del lambda (artefacto efimero),
        When invoco classify_path,
        Then devuelve kind='ignore'.
        """
        assert classify_path(
            'serverless/lambda/services/cv/build/index.html'
        ) == ChangeKind(kind='ignore')

    def test_service_seeds_data_no_dispara(self):
        """
        Given un path core/seeds/data/ del lambda db,
        When invoco classify_path,
        Then devuelve kind='ignore' (seeds requieren re-run manual).
        """
        assert classify_path(
            'serverless/lambda/services/db/core/seeds/data/foo.yaml'
        ) == ChangeKind(kind='ignore')

    def test_shared_subpackage_dispara_redeploy_de_consumers(self):
        """
        Given un path 'serverless/lambda/shared/core/__init__.py',
        When invoco classify_path,
        Then devuelve ChangeKind(kind='shared', name='core').
        """
        assert classify_path(
            'serverless/lambda/shared/core/__init__.py'
        ) == ChangeKind(kind='shared', name='core')

    def test_shared_tests_no_dispara(self):
        """
        Given un path tests/ de shared/,
        When invoco classify_path,
        Then devuelve kind='ignore'.
        """
        assert classify_path(
            'serverless/lambda/shared/tests/unit/shared/core/test_x.py'
        ) == ChangeKind(kind='ignore')

    def test_non_serverless_path_no_dispara(self):
        """
        Given un path fuera de serverless/,
        When invoco classify_path,
        Then devuelve kind='ignore'.
        """
        assert classify_path('apps/generic/src/pages/index.astro') == (
            ChangeKind(kind='ignore')
        )
        assert classify_path('docs/specs/x/README.md') == (
            ChangeKind(kind='ignore')
        )

    def test_short_path_no_dispara(self):
        """
        Given un path con menos de 4 partes,
        When invoco classify_path,
        Then devuelve kind='ignore' sin crashear.
        """
        assert classify_path('serverless/lambda/shared/') == (
            ChangeKind(kind='ignore')
        )
        assert classify_path('serverless/lambda/services') == (
            ChangeKind(kind='ignore')
        )


# ---------------------------------------------------------------------------
# detect_affected_lambdas (con files inyectados)
# ---------------------------------------------------------------------------


def _lambdas_root() -> Path:
    """Resuelve la raiz REAL de los lambdas del repo."""
    return (
        Path(__file__).resolve().parents[5]
        / 'serverless'
        / 'lambda'
        / 'services'
    )


class TestDetectAffectedLambdas:
    """detect_affected_lambdas combina cambios directos + cierre shared."""

    def test_cambio_solo_en_cv_returns_only_cv(self):
        """
        Given files con solo cambios en services/cv/core/,
        When invoco detect_affected_lambdas,
        Then devuelve {'cv'} (no propaga a otros lambdas).
        """
        result = detect_affected_lambdas(
            base_sha='_unused',
            head_sha='_unused',
            lambdas_root=_lambdas_root(),
            files=['serverless/lambda/services/cv/core/services/foo.py'],
        )
        assert result == {'cv'}

    def test_solo_tests_returns_empty(self):
        """
        Given files con solo cambios en tests/ de un lambda,
        When invoco detect_affected_lambdas,
        Then devuelve set() (no dispara redeploy).
        """
        result = detect_affected_lambdas(
            base_sha='_unused',
            head_sha='_unused',
            lambdas_root=_lambdas_root(),
            files=[
                'serverless/lambda/services/cv/tests/unit/test_foo.py',
                'serverless/lambda/services/db/events/migrate.json',
            ],
        )
        assert result == set()

    def test_seeds_data_no_dispara_db(self):
        """
        Given files con cambios solo en core/seeds/data/ del lambda db,
        When invoco detect_affected_lambdas,
        Then devuelve set() (los seeds no van al deploy automatico).
        """
        result = detect_affected_lambdas(
            base_sha='_unused',
            head_sha='_unused',
            lambdas_root=_lambdas_root(),
            files=[
                'serverless/lambda/services/db/core/seeds/data/profile.yaml'
            ],
        )
        assert result == set()

    def test_cambio_en_shared_db_dispara_consumers(self):
        """
        Given un cambio en shared/db/__init__.py,
        When invoco detect_affected_lambdas con los lambdas reales del repo,
        Then devuelve los lambdas cuyo cierre transitivo incluye shared.db
             (segun el shared_resolver real). Para el portfolio esto incluye
             db, cv y stream_processor.
        """
        result = detect_affected_lambdas(
            base_sha='_unused',
            head_sha='_unused',
            lambdas_root=_lambdas_root(),
            files=['serverless/lambda/shared/db/__init__.py'],
        )
        # Cualquier lambda que importe shared.db debe estar en el resultado.
        # db (Lambda db), cv (cv_repository) y stream_processor (writes).
        assert {'db', 'cv', 'stream_processor'}.issubset(result)

    def test_combinacion_de_service_y_shared(self):
        """
        Given un cambio en services/contact_form/ + shared/db/__init__.py,
        When invoco detect_affected_lambdas,
        Then devuelve la union: contact_form + los consumers de shared.db.
        """
        result = detect_affected_lambdas(
            base_sha='_unused',
            head_sha='_unused',
            lambdas_root=_lambdas_root(),
            files=[
                'serverless/lambda/services/contact_form/core/services/x.py',
                'serverless/lambda/shared/db/__init__.py',
            ],
        )
        # contact_form esta porque su path cambio directo.
        # Los consumers de shared.db (db, cv, stream_processor) tambien.
        assert 'contact_form' in result
        assert {'db', 'cv', 'stream_processor'}.issubset(result)

    def test_archivos_irrelevantes_returns_empty(self):
        """
        Given files con solo cambios en docs/ y apps/,
        When invoco detect_affected_lambdas,
        Then devuelve set() (sin cambios que afecten lambdas).
        """
        result = detect_affected_lambdas(
            base_sha='_unused',
            head_sha='_unused',
            lambdas_root=_lambdas_root(),
            files=[
                'docs/specs/x/README.md',
                'apps/generic/src/pages/index.astro',
                '.github/workflows/ci.yml',
            ],
        )
        assert result == set()


# ---------------------------------------------------------------------------
# cmd_detect_changes (CLI wrapper)
# ---------------------------------------------------------------------------


class TestCmdDetectChanges:
    """cmd_detect_changes imprime JSON y maneja errores de CLI."""

    def test_fails_without_base(self, capsys):
        """
        Given un dict de flags sin --base,
        When invoco cmd_detect_changes,
        Then exit 1 y stderr incluye 'ERROR: --base'.
        """
        from serverless.change_detector import cmd_detect_changes

        rc = cmd_detect_changes({})

        assert rc == 1
        captured = capsys.readouterr()
        assert '--base' in captured.err

    def test_imprime_json_payload(self, capsys, monkeypatch):
        """
        Given un dict de flags con --base y --head reales (HEAD~1..HEAD),
        When invoco cmd_detect_changes,
        Then exit 0 y stdout es un JSON con la clave 'affected'.
        """
        import json

        from serverless.change_detector import cmd_detect_changes

        # Mockear detect_affected_lambdas para no depender del git real
        # de los tests (puede ser unstable).
        from serverless import change_detector

        monkeypatch.setattr(
            change_detector,
            'detect_affected_lambdas',
            lambda **_kw: {'cv', 'db'},
        )

        rc = cmd_detect_changes({'base': 'HEAD~1', 'head': 'HEAD'})

        assert rc == 0
        captured = capsys.readouterr()
        payload = json.loads(captured.out)
        assert payload == {'affected': ['cv', 'db']}
