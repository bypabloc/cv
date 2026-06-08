"""Tests del config del portador E2E: URLs por env + emails sinteticos.

Cubre las piezas PURAS de `shared.config`: el origin desplegado de cada
niche (incluido el apex/`generic`), la forma exacta del email sintetico
del SES simulator, y el soporte de bypass por entorno.
"""

import re

from shared.config import niche_origin
from shared.config import synthetic_email
from shared.config import turnstile_bypass_supported


# Email del SES simulator: success+api-e2e-<run_id>-<slot>-<6 hex>@simulator...
_EMAIL_RE = re.compile(
    r'^success\+api-e2e-[0-9a-z]+-[0-9a-z]+-[0-9a-f]{6}'
    r'@simulator\.amazonses\.com$',
)


def test_niche_origin_fintech_dev_returns_subdomain_url() -> None:
    """
    Given el niche 'fintech' y el entorno 'dev',
    When se resuelve niche_origin,
    Then devuelve el subdominio desplegado exacto del niche en dev.
    """
    result = niche_origin('fintech', 'dev')

    assert result == 'https://fintech.portfolio.dev.the-full-stack.com'


def test_niche_origin_generic_dev_resolves_to_apex_base_domain() -> None:
    """
    Given el niche 'generic' (apex) y el entorno 'dev',
    When se resuelve niche_origin,
    Then devuelve el base_domain del env (apex_domain=None en dev/stage,
         segun cloudflare_setup/config.py): portfolio.dev.the-full-stack.com.
    """
    result = niche_origin('generic', 'dev')

    assert result == 'https://portfolio.dev.the-full-stack.com'


def test_niche_origin_hub_dev_returns_subdomain_url() -> None:
    """
    Given el niche 'hub' y el entorno 'dev',
    When se resuelve niche_origin,
    Then devuelve hub.portfolio.dev.the-full-stack.com.
    """
    result = niche_origin('hub', 'dev')

    assert result == 'https://hub.portfolio.dev.the-full-stack.com'


def test_synthetic_email_matches_simulator_format() -> None:
    """
    Given un run_id y un slot,
    When se genera un email sintetico,
    Then matchea EXACTAMENTE el patron del SES simulator con el RUN_TAG
         'api-e2e' embebido y un sufijo de 6 hex.
    """
    email = synthetic_email('r1', 'owner')

    assert _EMAIL_RE.match(email) is not None


def test_synthetic_email_embeds_run_id_and_slot() -> None:
    """
    Given run_id='abc' y slot='owner',
    When se genera el email sintetico,
    Then el local-part contiene el RUN_TAG, run_id y slot en orden.
    """
    email = synthetic_email('abc', 'owner')

    assert email.startswith('success+api-e2e-abc-owner-')
    assert email.endswith('@simulator.amazonses.com')


def test_synthetic_email_is_unique_per_call() -> None:
    """
    Given los mismos run_id y slot,
    When se genera dos veces,
    Then los emails difieren (el sufijo hex es aleatorio por llamada).
    """
    a = synthetic_email('r1', 'owner')
    b = synthetic_email('r1', 'owner')

    assert a != b


def test_turnstile_bypass_supported_dev_is_true() -> None:
    """
    Given el entorno 'dev',
    When se consulta el soporte de bypass de Turnstile,
    Then devuelve True (dev evalua el header X-Turnstile-Bypass-Token).
    """
    assert turnstile_bypass_supported('dev') is True


def test_turnstile_bypass_supported_prod_is_false() -> None:
    """
    Given el entorno 'prod',
    When se consulta el soporte de bypass de Turnstile,
    Then devuelve False (prod NUNCA acepta el bypass).
    """
    assert turnstile_bypass_supported('prod') is False
