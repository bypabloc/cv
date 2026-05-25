"""Unit tests for ai_audit.report.

Path mirroring: devtools/ai_audit/report.py -> este archivo.
"""

from datetime import UTC
from datetime import datetime
import json
from pathlib import Path

import pytest

from ai_audit import report
from ai_audit.tools.base import Fix
from ai_audit.tools.base import Severity
from ai_audit.tools.base import Status
from ai_audit.tools.base import ToolResult


pytestmark = pytest.mark.unit


def _result(
    *,
    tool: str = 'isitagentready',
    target: str = 'https://the-full-stack.com/',
    status: Status = Status.OK,
    score: int | None = 78,
    categories: dict | None = None,
    fixes: tuple[Fix, ...] = (),
    skipped_reason: str | None = None,
) -> ToolResult:
    return ToolResult(
        tool=tool,
        target=target,
        status=status,
        score=score,
        categories=categories or {},
        fixes=fixes,
        raw_log_path=None,
        skipped_reason=skipped_reason,
    )


def test_write_snapshot_when_ok_result_then_json_has_all_fields(
    tmp_path: Path,
) -> None:
    """
    Given un OK result con categorias y 1 fix,
    When write_snapshot,
    Then el JSON tiene env, ranAt, targets, tools, results con los
    campos exactos.
    """
    r = _result(
        categories={'Discoverability': 90},
        fixes=(
            Fix(
                severity=Severity.HIGH,
                category='Bot Access Control',
                issue='robots.txt missing GPTBot',
                fix='Add allow rule',
                file='public/robots.txt',
                reach=8,
            ),
        ),
    )
    ran_at = datetime(2026, 5, 25, 10, 30, 0, tzinfo=UTC)
    path = tmp_path / 'snapshot.json'

    report.write_snapshot(
        results=[r],
        env='prod',
        ran_at=ran_at,
        path=path,
    )

    data = json.loads(path.read_text())
    assert data['env'] == 'prod'
    assert data['ranAt'] == '2026-05-25T10:30:00Z'
    assert data['targets'] == ['https://the-full-stack.com/']
    assert data['tools'] == ['isitagentready']
    assert data['interrupted'] is False
    assert len(data['results']) == 1
    assert data['results'][0]['score'] == 78
    assert data['results'][0]['status'] == 'OK'
    assert data['results'][0]['fixes'][0]['severity'] == 'high'


def test_render_markdown_when_6_targets_then_table_rows_alphabetical(
    tmp_path: Path,
) -> None:
    """
    Given 2 targets x 1 tool con scores,
    When render_markdown,
    Then la tabla resumen tiene filas ordenadas por target.
    """
    results = [
        _result(target='https://b.example.com/', score=50),
        _result(target='https://a.example.com/', score=80),
    ]
    snap = tmp_path / 'snapshot.json'
    report.write_snapshot(
        results=results,
        env='prod',
        ran_at=datetime(2026, 5, 25, tzinfo=UTC),
        path=snap,
    )
    out = tmp_path / 'report.md'

    report.render_markdown(snapshot_path=snap, output_path=out)

    md = out.read_text()
    # Las filas tienen el formato '| <target> | ... |'; el orden por target
    # ascendente coloca a.example antes que b.example.
    a_pos = md.index('https://a.example.com/')
    b_pos = md.index('https://b.example.com/')
    assert a_pos < b_pos
    assert '80/100' in md
    assert '50/100' in md


def test_render_markdown_when_no_fixes_then_section_says_empty(
    tmp_path: Path,
) -> None:
    """
    Given 1 result sin fixes,
    When render_markdown,
    Then la seccion "Top 5 fixes" dice "No hay fixes pendientes".
    """
    snap = tmp_path / 'snapshot.json'
    report.write_snapshot(
        results=[_result()],
        env='prod',
        ran_at=datetime(2026, 5, 25, tzinfo=UTC),
        path=snap,
    )
    out = tmp_path / 'report.md'

    report.render_markdown(snapshot_path=snap, output_path=out)

    md = out.read_text()
    assert 'No hay fixes pendientes' in md


def test_prioritize_fixes_when_mixed_severities_then_high_first() -> None:
    """
    Given 10 fixes con severities mezcladas,
    When prioritize_fixes(top=5),
    Then retorna 5 ordenados HIGH primero, luego MEDIUM, luego LOW.
    """
    high_high = Fix(
        severity=Severity.HIGH,
        category='A',
        issue='ih',
        fix='x',
        reach=10,
    )
    high_low = Fix(
        severity=Severity.HIGH,
        category='A',
        issue='il',
        fix='x',
        reach=1,
    )
    medium = Fix(
        severity=Severity.MEDIUM,
        category='A',
        issue='m',
        fix='x',
        reach=5,
    )
    low_high = Fix(
        severity=Severity.LOW,
        category='A',
        issue='lh',
        fix='x',
        reach=10,
    )
    low_low = Fix(
        severity=Severity.LOW,
        category='A',
        issue='ll',
        fix='x',
        reach=1,
    )
    r = _result(fixes=(high_low, low_high, medium, low_low, high_high))

    result = report.prioritize_fixes([r], top=5)

    assert result[0] is high_high
    assert result[1] is high_low
    assert result[2] is medium
    assert result[3] is low_high
    assert result[4] is low_low


def test_render_markdown_when_blocked_then_section_present(
    tmp_path: Path,
) -> None:
    """
    Given 1 result SKIPPED con razon,
    When render_markdown,
    Then la seccion "Audits BLOCKED / ERROR / SKIPPED" lista el target.
    """
    skipped = _result(
        tool='ahrefs',
        status=Status.SKIPPED,
        score=None,
        skipped_reason='storageState MISSING',
    )
    snap = tmp_path / 'snapshot.json'
    report.write_snapshot(
        results=[skipped],
        env='prod',
        ran_at=datetime(2026, 5, 25, tzinfo=UTC),
        path=snap,
    )
    out = tmp_path / 'report.md'

    report.render_markdown(snapshot_path=snap, output_path=out)

    md = out.read_text()
    assert 'Audits BLOCKED / ERROR / SKIPPED' in md
    assert 'storageState MISSING' in md


def test_render_markdown_when_called_twice_then_idempotent(
    tmp_path: Path,
) -> None:
    """
    Given un snapshot,
    When render_markdown 2 veces,
    Then ambos producen el mismo report.md (idempotente, AC-5).
    """
    snap = tmp_path / 'snapshot.json'
    report.write_snapshot(
        results=[_result()],
        env='prod',
        ran_at=datetime(2026, 5, 25, tzinfo=UTC),
        path=snap,
    )
    out = tmp_path / 'report.md'

    report.render_markdown(snapshot_path=snap, output_path=out)
    first = out.read_text()
    report.render_markdown(snapshot_path=snap, output_path=out)
    second = out.read_text()

    assert first == second


def test_write_snapshot_when_ahrefs_then_score_kept_as_is(
    tmp_path: Path,
) -> None:
    """
    Given un result de Ahrefs con score=3 (de 5 max),
    When write_snapshot,
    Then el JSON guarda score=3 (sin normalizar — normalizacion vive
    en el render).
    """
    r = _result(tool='ahrefs', score=3)
    path = tmp_path / 'snapshot.json'

    report.write_snapshot(
        results=[r],
        env='prod',
        ran_at=datetime(2026, 5, 25, tzinfo=UTC),
        path=path,
    )

    data = json.loads(path.read_text())
    assert data['results'][0]['score'] == 3


def test_render_markdown_when_ahrefs_then_table_shows_normalized_avg(
    tmp_path: Path,
) -> None:
    """
    Given un result de Ahrefs score=3 (max 5),
    When render_markdown,
    Then la tabla muestra '3/5' y avg normalizado 60.
    """
    r = _result(tool='ahrefs', score=3)
    snap = tmp_path / 'snapshot.json'
    report.write_snapshot(
        results=[r],
        env='prod',
        ran_at=datetime(2026, 5, 25, tzinfo=UTC),
        path=snap,
    )
    out = tmp_path / 'report.md'

    report.render_markdown(snapshot_path=snap, output_path=out)

    md = out.read_text()
    assert '3/5' in md
    # Avg para una sola tool con score 3/5 = 60
    assert '| 60 |' in md
