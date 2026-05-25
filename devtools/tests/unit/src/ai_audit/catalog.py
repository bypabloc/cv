"""Unit tests for ai_audit.catalog.

Path mirroring: devtools/ai_audit/catalog.py -> this file.
"""

import pytest

from ai_audit.catalog import resolve_targets
from ai_audit.catalog import resolve_url


pytestmark = pytest.mark.unit


def test_resolve_url_when_prod_generic_then_apex() -> None:
    """
    Given env=prod, niche=generic,
    When resolve_url('/'),
    Then https://the-full-stack.com/.
    """
    assert resolve_url('prod', 'generic', '/') == 'https://the-full-stack.com/'


def test_resolve_url_when_prod_niche_then_portfolio_subdomain() -> None:
    """
    Given env=prod, niche=hub,
    When resolve_url('/'),
    Then https://hub.portfolio.the-full-stack.com/.
    """
    assert (
        resolve_url('prod', 'hub', '/')
        == 'https://hub.portfolio.the-full-stack.com/'
    )


def test_resolve_url_when_stage_with_custom_path_then_includes_path() -> None:
    """
    Given env=stage, niche=generic, path='/projects',
    When resolve_url,
    Then https://generic.portfolio.stage.the-full-stack.com/projects.
    """
    assert (
        resolve_url('stage', 'generic', '/projects')
        == 'https://generic.portfolio.stage.the-full-stack.com/projects'
    )


def test_resolve_url_when_dev_then_dev_subdomain() -> None:
    """
    Given env=dev, niche=fintech,
    When resolve_url('/'),
    Then https://fintech.portfolio.dev.the-full-stack.com/.
    """
    assert (
        resolve_url('dev', 'fintech', '/')
        == 'https://fintech.portfolio.dev.the-full-stack.com/'
    )


def test_resolve_url_when_local_generic_then_localhost_apex() -> None:
    """
    Given env=local, niche=generic,
    When resolve_url('/'),
    Then http://localhost:9970/.
    """
    assert resolve_url('local', 'generic', '/') == 'http://localhost:9970/'


def test_resolve_url_when_local_niche_then_subdomain_localhost() -> None:
    """
    Given env=local, niche=hub,
    When resolve_url('/'),
    Then http://hub.localhost:9970/.
    """
    assert resolve_url('local', 'hub', '/') == 'http://hub.localhost:9970/'


def test_resolve_url_when_unknown_niche_then_raises() -> None:
    """
    Given niche='unknown',
    When resolve_url,
    Then raises ValueError.
    """
    with pytest.raises(ValueError, match='unknown niche'):
        resolve_url('prod', 'unknown', '/')


def test_resolve_url_when_path_without_leading_slash_then_raises() -> None:
    """
    Given path='projects' (sin /),
    When resolve_url,
    Then raises ValueError.
    """
    with pytest.raises(ValueError, match='path must start with'):
        resolve_url('prod', 'hub', 'projects')


def test_resolve_url_when_unknown_env_then_raises() -> None:
    """
    Given env='qa',
    When resolve_url,
    Then raises ValueError.
    """
    with pytest.raises(ValueError, match='unknown env'):
        resolve_url('qa', 'hub', '/')


def test_resolve_targets_when_no_override_then_one_url_per_niche() -> None:
    """
    Given env=prod, niches=[generic, hub], sin targets_override,
    When resolve_targets,
    Then dos URLs raiz (una por niche).
    """
    result = resolve_targets(env='prod', niches=['generic', 'hub'])

    assert result == [
        'https://the-full-stack.com/',
        'https://hub.portfolio.the-full-stack.com/',
    ]


def test_resolve_targets_when_override_then_override_wins() -> None:
    """
    Given targets_override = [{niche: hub, path: /projects}],
    When resolve_targets (niches ignorados),
    Then una sola URL con el path custom.
    """
    result = resolve_targets(
        env='prod',
        niches=['generic', 'hub', 'fintech'],
        targets_override=[{'niche': 'hub', 'path': '/projects'}],
    )

    assert result == ['https://hub.portfolio.the-full-stack.com/projects']
