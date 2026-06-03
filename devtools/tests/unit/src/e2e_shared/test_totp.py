"""Tests del generador TOTP del portador E2E (RFC 6238, HMAC-SHA1, 6 digitos).

Ancla el algoritmo contra los vectores de prueba oficiales de la RFC 6238
(Appendix B), usando el seed ASCII '12345678901234567890' (base32
'GEZDGNBVGY3TQOJQGEZDGNBVGY3TQOJQ'). Los vectores de la RFC son de 8
digitos; nuestra implementacion usa 6, asi que comparamos contra los 6
ultimos digitos de cada vector. Asi un cambio accidental en el algoritmo
(periodo, hash, truncado) rompe estos tests.
"""

from shared.totp import totp_now


# Seed RFC 6238 (ASCII '12345678901234567890') en base32 sin padding. NO es
# un secreto: es el vector de prueba PUBLICO de la RFC 6238, Appendix B.
_RFC_SECRET_B32 = 'GEZDGNBVGY3TQOJQGEZDGNBVGY3TQOJQ'  # noqa: S105 -- RFC vector


def test_totp_now_rfc_vector_at_59s() -> None:
    """
    Given el seed RFC 6238 y el instante at=59,
    When se genera el code TOTP de 6 digitos,
    Then es '287082' (6 ultimos del vector RFC 8-digitos '94287082').
    """
    assert totp_now(_RFC_SECRET_B32, at=59) == '287082'


def test_totp_now_rfc_vector_at_1111111109s() -> None:
    """
    Given el seed RFC 6238 y el instante at=1111111109,
    When se genera el code TOTP de 6 digitos,
    Then es '081804' (6 ultimos del vector RFC '07081804').
    """
    assert totp_now(_RFC_SECRET_B32, at=1111111109) == '081804'


def test_totp_now_rfc_vector_at_1234567890s() -> None:
    """
    Given el seed RFC 6238 y el instante at=1234567890,
    When se genera el code TOTP de 6 digitos,
    Then es '005924' (6 ultimos del vector RFC '89005924'), con el
         zero-padding del primer digito preservado.
    """
    assert totp_now(_RFC_SECRET_B32, at=1234567890) == '005924'


def test_totp_now_rfc_vector_at_2000000000s() -> None:
    """
    Given el seed RFC 6238 y el instante at=2000000000,
    When se genera el code TOTP de 6 digitos,
    Then es '279037' (6 ultimos del vector RFC '69279037').
    """
    assert totp_now(_RFC_SECRET_B32, at=2000000000) == '279037'


def test_totp_now_same_period_yields_same_code() -> None:
    """
    Given dos instantes dentro del MISMO periodo de 30s (60 y 89),
    When se generan ambos codes,
    Then son identicos (el counter = at // 30 no cambio).
    """
    assert totp_now(_RFC_SECRET_B32, at=60) == totp_now(_RFC_SECRET_B32, at=89)


def test_totp_now_next_period_changes_code() -> None:
    """
    Given dos instantes en periodos consecutivos (59 y 90),
    When se generan ambos codes,
    Then difieren (el counter avanzo de 1 a 3).
    """
    assert totp_now(_RFC_SECRET_B32, at=59) != totp_now(_RFC_SECRET_B32, at=90)


def test_totp_now_always_six_digits() -> None:
    """
    Given un at que produce un code con primer digito 0,
    When se genera,
    Then el code tiene exactamente 6 caracteres (zero-padded).
    """
    code = totp_now(_RFC_SECRET_B32, at=1234567890)

    assert len(code) == 6
    assert code == '005924'
