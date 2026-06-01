"""Tests de config de api_e2e: IpRotator, emails sinteticos, env helpers."""

from api_e2e.config import IpRotator
from api_e2e.config import api_base
from api_e2e.config import synthetic_email
from api_e2e.config import turnstile_bypass_supported


def test_ip_rotator_yields_distinct_ips_consecutively() -> None:
    """
    Given un IpRotator,
    When se piden 3 IPs seguidas,
    Then las 3 son distintas (no se repite IP en requests consecutivos).
    """
    rot = IpRotator()

    ips = [rot.next(), rot.next(), rot.next()]

    assert len(set(ips)) == 3


def test_ip_rotator_first_ip_is_testnet() -> None:
    """
    Given un IpRotator nuevo,
    When se pide la primera IP,
    Then es del rango TEST-NET RFC 5737 (198.51.100.x).
    """
    rot = IpRotator()

    assert rot.next() == '198.51.100.1'


def test_synthetic_email_uses_ses_simulator_domain() -> None:
    """
    Given un run_id y un slot,
    When synthetic_email,
    Then el email usa el dominio del SES mailbox simulator.
    """
    email = synthetic_email('abcd', 'auth')

    assert email.endswith('@simulator.amazonses.com')
    assert email.startswith('success+api-e2e-abcd-auth-')


def test_synthetic_email_is_unique_per_call() -> None:
    """
    Given el mismo run_id y slot,
    When synthetic_email se llama 2 veces,
    Then los emails difieren (suffix random embebido).
    """
    first = synthetic_email('run1', 'auth')
    second = synthetic_email('run1', 'auth')

    assert first != second


def test_api_base_dev_is_dev_subdomain() -> None:
    """
    Given env=dev,
    When api_base,
    Then la URL es el subdominio dev del API Gateway.
    """
    assert api_base('dev') == 'https://api.portfolio.dev.the-full-stack.com'


def test_turnstile_bypass_supported_dev_and_stage() -> None:
    """
    Given los entornos dev y stage,
    When turnstile_bypass_supported,
    Then ambos soportan el bypass firmado (prod NUNCA, pero el harness no
    corre contra prod).
    """
    assert turnstile_bypass_supported('dev') is True
    assert turnstile_bypass_supported('stage') is True
