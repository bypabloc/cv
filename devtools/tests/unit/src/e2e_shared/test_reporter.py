"""Tests del Reporter del portador E2E: atribucion del cold start POR-LAMBDA.

El cold start lo paga solo el PRIMER invoke del contenedor de cada Lambda.
El reporter NO debe atribuir un cold a cada caso: el 1er caso de un Lambda se
lleva el cold (elapsed[0]); los casos siguientes corren calientes (cold=None)
y su tiempo cuenta como warm.
"""

from shared.reporter import CaseResult
from shared.reporter import Reporter


def _case(
    lambda_name: str,
    name: str,
    elapsed: list[float],
    *,
    passed: bool = True,
) -> CaseResult:
    """Builder de CaseResult con status/expected triviales (solo importa
    el timing + lambda_name + passed para estos tests)."""
    return CaseResult(
        lambda_name=lambda_name,
        name=name,
        method='GET',
        status_codes=[200] * len(elapsed),
        expected='200',
        passed=passed,
        elapsed=elapsed,
    )


def _reporter(*cases: CaseResult) -> Reporter:
    rep = Reporter()
    rep.results.extend(cases)
    return rep


def test_timing_rows_first_case_of_lambda_carries_cold() -> None:
    """
    Given el PRIMER caso de un Lambda con samples [12.0, 7.0, 9.0],
    When timing_rows clasifica,
    Then ese caso tiene cold=12.0 (sample 1) y warm=8.0 (avg de 7.0 y 9.0).
    """
    rep = _reporter(_case('cv', 'cv.get', [12.0, 7.0, 9.0]))

    rows = rep.timing_rows()

    assert rows[0].cold == 12.0
    assert rows[0].warm == 8.0


def test_timing_rows_second_case_of_lambda_has_no_cold() -> None:
    """
    Given un segundo caso del MISMO Lambda con samples [0.5, 1.5],
    When timing_rows clasifica,
    Then ese caso tiene cold=None (contenedor ya caliente) y warm=1.0
         (promedio de TODOS sus samples, no descarta el primero).
    """
    rep = _reporter(
        _case('cv', 'cv.get', [12.0, 7.0, 9.0]),
        _case('cv', 'cv.profile', [0.5, 1.5]),
    )

    rows = rep.timing_rows()

    assert rows[1].cold is None
    assert rows[1].warm == 1.0


def test_timing_rows_single_sample_first_case_has_cold_no_warm() -> None:
    """
    Given el primer caso de un Lambda con un UNICO sample [14.0],
    When timing_rows clasifica,
    Then cold=14.0 y warm=None (no quedan samples calientes tras el cold).
    """
    rep = _reporter(_case('auth', 'register.start', [14.0]))

    rows = rep.timing_rows()

    assert rows[0].cold == 14.0
    assert rows[0].warm is None


def test_timing_rows_single_sample_later_case_is_warm() -> None:
    """
    Given un caso posterior del mismo Lambda con un UNICO sample [3.9],
    When timing_rows clasifica,
    Then cold=None y warm=3.9 (el sample unico es warm, no cold).
    """
    rep = _reporter(
        _case('auth', 'register.start', [14.0]),
        _case('auth', 'login.start', [3.9]),
    )

    rows = rep.timing_rows()

    assert rows[1].cold is None
    assert rows[1].warm == 3.9


def test_timing_rows_each_lambda_resets_cold_attribution() -> None:
    """
    Given casos de DOS Lambdas distintos intercalados por bloques,
    When timing_rows clasifica,
    Then el primer caso de CADA Lambda se lleva su propio cold.
    """
    rep = _reporter(
        _case('cv', 'cv.get', [12.0, 8.0]),
        _case('cv', 'cv.profile', [1.0, 1.0]),
        _case('auth', 'register.start', [14.0]),
        _case('auth', 'login.start', [4.0, 2.0]),
    )

    rows = rep.timing_rows()

    assert [r.cold for r in rows] == [12.0, None, 14.0, None]
    assert [r.warm for r in rows] == [8.0, 1.0, None, 3.0]


def test_timing_rows_empty_elapsed_yields_none_none() -> None:
    """
    Given un caso sin samples (elapsed vacio),
    When timing_rows clasifica,
    Then cold=None y warm=None y NO marca el Lambda como visto.
    """
    rep = _reporter(
        _case('cv', 'cv.empty', []),
        _case('cv', 'cv.get', [12.0, 8.0]),
    )

    rows = rep.timing_rows()

    assert rows[0].cold is None
    assert rows[0].warm is None
    # El caso vacio NO consumio el cold: el siguiente caso real SI lo lleva.
    assert rows[1].cold == 12.0


def test_cold_start_by_lambda_one_entry_per_lambda() -> None:
    """
    Given dos casos por Lambda en dos Lambdas distintos,
    When cold_start_by_lambda,
    Then devuelve exactamente un cold por Lambda (el primer invoke).
    """
    rep = _reporter(
        _case('cv', 'cv.get', [12.0, 8.0]),
        _case('cv', 'cv.profile', [1.0, 1.0]),
        _case('auth', 'register.start', [14.0]),
        _case('auth', 'login.start', [4.0, 2.0]),
    )

    cold = rep.cold_start_by_lambda()

    assert cold == {'cv': 12.0, 'auth': 14.0}


def test_cold_start_by_lambda_excludes_failed_first_invoke() -> None:
    """
    Given que el PRIMER invoke de un Lambda FALLO (passed=False),
    When cold_start_by_lambda,
    Then ese Lambda NO aporta cold (timing de un fallo no es confiable) y el
         segundo caso tampoco lo aporta (el contenedor ya estaba caliente).
    """
    rep = _reporter(
        _case('cv', 'cv.get', [12.0, 8.0], passed=False),
        _case('cv', 'cv.profile', [1.0, 1.0], passed=True),
    )

    cold = rep.cold_start_by_lambda()

    assert cold == {}


def test_print_timing_summary_groups_cold_and_shows_dash(capsys) -> None:
    """
    Given dos Lambdas con cold 12.0 y 14.0 + casos calientes,
    When print_timing_summary,
    Then imprime el bloque agrupado por Lambda con COLD avg=13.0 y la tabla
         por caso muestra '-' en cold para los casos del Lambda ya caliente.
    """
    rep = _reporter(
        _case('cv', 'cv.get', [12.0, 8.0]),
        _case('cv', 'cv.profile', [1.0, 1.0]),
        _case('auth', 'register.start', [14.0]),
    )

    rep.print_timing_summary()
    out = capsys.readouterr().out

    assert 'COLD START POR LAMBDA' in out
    assert 'TIEMPOS POR CASO' in out
    # cold avg = (12.0 + 14.0) / 2 = 13.000
    assert '13.000' in out
    # el bloque agrupado nombra el primer caso de cada Lambda
    assert 'cv.get' in out
    assert 'register.start' in out
    # la tabla por caso muestra cold '-' para el caso del Lambda ya caliente
    assert '-' in out


def test_print_timing_summary_empty_reporter_does_not_crash(capsys) -> None:
    """
    Given un reporter sin resultados,
    When print_timing_summary,
    Then imprime los encabezados sin filas y sin lanzar excepcion.
    """
    rep = Reporter()

    rep.print_timing_summary()
    out = capsys.readouterr().out

    assert 'COLD START POR LAMBDA' in out
    assert 'GLOBAL' in out


def test_passed_count_and_all_passed_with_mixed_results() -> None:
    """
    Given 2 casos passed y 1 failed,
    When passed_count / all_passed,
    Then passed_count==2 y all_passed==False.
    """
    rep = _reporter(
        _case('cv', 'cv.get', [1.0]),
        _case('cv', 'cv.profile', [1.0]),
        _case('auth', 'login.start', [1.0], passed=False),
    )

    assert rep.passed_count() == 2
    assert rep.all_passed() is False


def test_print_final_lists_failures(capsys) -> None:
    """
    Given un caso fallido,
    When print_final,
    Then imprime el veredicto N/total y la seccion FALLOS con el caso.
    """
    rep = _reporter(
        _case('cv', 'cv.get', [1.0]),
        _case('auth', 'login.start', [1.0], passed=False),
    )

    rep.print_final()
    out = capsys.readouterr().out

    assert 'RESULTADO: 1/2 casos PASS' in out
    assert 'FALLOS:' in out
    assert 'auth.login.start' in out


def test_print_final_all_passed_omits_failures_section(capsys) -> None:
    """
    Given todos los casos passed,
    When print_final,
    Then imprime el veredicto completo y NO imprime la seccion FALLOS.
    """
    rep = _reporter(_case('cv', 'cv.get', [1.0]))

    rep.print_final()
    out = capsys.readouterr().out

    assert 'RESULTADO: 1/1 casos PASS' in out
    assert 'FALLOS:' not in out
