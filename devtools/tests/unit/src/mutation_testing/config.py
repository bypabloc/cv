"""Unit tests for ``mutation_testing.config``.

Path mirroring: ``devtools/mutation_testing/config.py`` -> this file.

Politica AI-testing independence: ``.claude/rules/ai-testing-independence.md``.
"""

import pytest

from mutation_testing.config import CRITICAL_PATHS
from mutation_testing.config import CRITICAL_THRESHOLD
from mutation_testing.config import EXCLUDED_FRAGMENTS
from mutation_testing.config import EXPERIMENTAL_PATHS
from mutation_testing.config import EXPERIMENTAL_THRESHOLD
from mutation_testing.config import STANDARD_PATHS
from mutation_testing.config import STANDARD_THRESHOLD
from mutation_testing.config import all_categories
from mutation_testing.config import category_for_path
from mutation_testing.config import is_excluded
from mutation_testing.config import threshold_for_path


pytestmark = pytest.mark.unit


class TestThresholdConstants:
    """Thresholds documentados en ai-testing-independence rule."""

    def test_critical_threshold_is_85_percent(self) -> None:
        """
        Given critical paths cubren codigo con dinero o credenciales,
        When se consulta CRITICAL_THRESHOLD,
        Then es exactamente 0.85 (85% mutation score minimo).
        """
        assert CRITICAL_THRESHOLD == 0.85

    def test_standard_threshold_is_70_percent(self) -> None:
        """
        Given standard paths cubren logica de negocio core,
        When se consulta STANDARD_THRESHOLD,
        Then es exactamente 0.70.
        """
        assert STANDARD_THRESHOLD == 0.70

    def test_experimental_threshold_is_30_percent(self) -> None:
        """
        Given experimental paths cubren features nuevas en exploracion,
        When se consulta EXPERIMENTAL_THRESHOLD,
        Then es exactamente 0.30.
        """
        assert EXPERIMENTAL_THRESHOLD == 0.30


class TestThresholdForPath:
    def test_payments_path_returns_critical_threshold(self) -> None:
        """
        Given un path en apps/payments/services,
        When se consulta el threshold,
        Then retorna 0.85 (categoria critical).
        """
        assert threshold_for_path('apps/payments/services/create.py') == 0.85

    def test_auth_path_returns_critical_threshold(self) -> None:
        """
        Given un path en apps/auth/services,
        When se consulta el threshold,
        Then retorna 0.85 (categoria critical).
        """
        assert threshold_for_path('apps/auth/services/login.py') == 0.85

    def test_security_path_returns_critical_threshold(self) -> None:
        """
        Given un path en common/security,
        When se consulta el threshold,
        Then retorna 0.85 (categoria critical).
        """
        assert threshold_for_path('common/security/tokens.py') == 0.85

    def test_orders_path_returns_standard_threshold(self) -> None:
        """
        Given un path en apps/orders/services,
        When se consulta el threshold,
        Then retorna 0.70 (categoria standard).
        """
        assert threshold_for_path('apps/orders/services/create.py') == 0.70

    def test_unknown_path_returns_standard_default(self) -> None:
        """
        Given un path no listado en ninguna categoria explicita,
        When se consulta el threshold,
        Then retorna 0.70 (default standard, no permite drift a experimental).
        """
        assert threshold_for_path('apps/unknown/services/foo.py') == 0.70


class TestCategoryForPath:
    def test_payments_path_is_critical(self) -> None:
        """
        Given un path en apps/payments/services,
        When se consulta su categoria,
        Then retorna exactamente 'critical'.
        """
        assert category_for_path('apps/payments/services/x.py') == 'critical'

    def test_orders_path_is_standard(self) -> None:
        """
        Given un path en apps/orders/services,
        When se consulta su categoria,
        Then retorna exactamente 'standard'.
        """
        assert category_for_path('apps/orders/services/x.py') == 'standard'

    def test_unknown_path_is_standard_default(self) -> None:
        """
        Given un path no listado,
        When se consulta su categoria,
        Then retorna 'standard' (no 'experimental') para evitar
        que codigo nuevo escape los gates.
        """
        assert category_for_path('apps/foobar/services/x.py') == 'standard'


class TestIsExcluded:
    @pytest.mark.parametrize(
        'path',
        [
            'apps/payments/admin/orders.py',
            'apps/payments/migrations/0001_initial.py',
            'apps/payments/management/commands/seed.py',
            'apps/payments/__init__.py',
            'apps/payments/apps.py',
            'apps/payments/urls.py',
            'apps/payments/constants.py',
            'apps/payments/enums/status.py',
        ],
    )
    def test_infrastructure_paths_are_excluded(self, path: str) -> None:
        """
        Given paths de infraestructura sin logica de negocio (admin,
        migrations, management, __init__, apps, urls, constants, enums),
        When se consulta is_excluded,
        Then retorna True (mutation testing los ignora).
        """
        assert is_excluded(path) is True

    def test_service_path_is_not_excluded(self) -> None:
        """
        Given un path con logica de negocio (services/),
        When se consulta is_excluded,
        Then retorna False (mutation testing aplica).
        """
        assert is_excluded('apps/payments/services/create.py') is False


class TestAllCategories:
    def test_returns_three_categories_with_expected_paths(self) -> None:
        """
        Given el mapping completo de categorias,
        When se invoca all_categories,
        Then retorna las tres categorias con sus tuplas de paths exactas.
        """
        # Arrange / Given
        expected = {
            'critical': CRITICAL_PATHS,
            'standard': STANDARD_PATHS,
            'experimental': EXPERIMENTAL_PATHS,
        }

        # Act / When
        result = all_categories()

        # Assert / Then (asserts EXACTOS)
        assert result == expected
        assert set(result.keys()) == {'critical', 'standard', 'experimental'}


class TestCriticalPathsCoverage:
    """Verifica que los paths criticos esperados esten registrados."""

    def test_payments_services_in_critical(self) -> None:
        """
        Given la politica que apps/payments/services es codigo critico,
        When se inspecciona CRITICAL_PATHS,
        Then contiene 'apps/payments/services'.
        """
        assert 'apps/payments/services' in CRITICAL_PATHS

    def test_auth_services_in_critical(self) -> None:
        """
        Given la politica que apps/auth/services es codigo critico,
        When se inspecciona CRITICAL_PATHS,
        Then contiene 'apps/auth/services'.
        """
        assert 'apps/auth/services' in CRITICAL_PATHS

    def test_security_in_critical(self) -> None:
        """
        Given la politica que common/security es codigo critico (PCI),
        When se inspecciona CRITICAL_PATHS,
        Then contiene 'common/security'.
        """
        assert 'common/security' in CRITICAL_PATHS


class TestExcludedFragments:
    def test_admin_fragment_is_excluded(self) -> None:
        """
        Given que el admin Django no contiene logica testeable por mutmut,
        When se inspecciona EXCLUDED_FRAGMENTS,
        Then '/admin/' esta presente.
        """
        assert '/admin/' in EXCLUDED_FRAGMENTS

    def test_migrations_fragment_is_excluded(self) -> None:
        """
        Given que las migrations son codigo auto-generado,
        When se inspecciona EXCLUDED_FRAGMENTS,
        Then '/migrations/' esta presente.
        """
        assert '/migrations/' in EXCLUDED_FRAGMENTS
