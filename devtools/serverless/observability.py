"""Observability commands for the SAM backend.

Wrappers de aws CloudWatch CLI para metricas + alarmas. Util en
post-deploy y debugging de incidentes (429 anomalo, 5XX spike, etc).
"""

from __future__ import annotations

import shutil
import subprocess
from typing import Any

from shared.console import CYAN
from shared.console import GREEN
from shared.console import RED
from shared.console import YELLOW
from shared.console import _c
from shared.console import _err


def _ensure_aws_cli() -> bool:
    if shutil.which('aws') is None:
        _err('AWS CLI no instalado')
        return False
    return True


def cmd_metrics(flags: dict[str, Any]) -> int:
    """Resumen de CloudWatch metrics del stack (Lambdas + API GW + WAF)."""
    if not _ensure_aws_cli():
        return 1

    stage = flags.get('stage', 'dev')
    output = flags.get('output', 'text')

    # Suma de invocations en la ultima hora
    print(_c(CYAN, 'Metricas ultima hora (us-west-2):'))
    print()

    namespaces = [
        ('AWS/Lambda', 'Invocations'),
        ('AWS/Lambda', 'Errors'),
        ('AWS/Lambda', 'Throttles'),
        ('AWS/ApiGateway', 'Count'),
        ('AWS/ApiGateway', '4XXError'),
        ('AWS/ApiGateway', '5XXError'),
        ('AWS/WAFV2', 'BlockedRequests'),
    ]

    for namespace, metric in namespaces:
        args = [
            'aws',
            'cloudwatch',
            'get-metric-statistics',
            '--namespace',
            namespace,
            '--metric-name',
            metric,
            '--start-time',
            '-PT1H',
            '--end-time',
            'now',
            '--period',
            '3600',
            '--statistics',
            'Sum',
            '--region',
            'us-west-2',
            '--output',
            'text',
            '--query',
            'Datapoints[0].Sum',
        ]
        result = subprocess.run(
            args, capture_output=True, text=True, check=False
        )
        value = result.stdout.strip() or '0'
        if value == 'None':
            value = '0'
        print(f'  {_c(CYAN, namespace):<35} {metric:<25} {value}')

    print()
    return 0


def cmd_alarms(flags: dict[str, Any]) -> int:
    """Lista alarmas CloudWatch + estado."""
    if not _ensure_aws_cli():
        return 1

    output = flags.get('output', 'text')

    args = [
        'aws',
        'cloudwatch',
        'describe-alarms',
        '--region',
        'us-west-2',
        '--alarm-name-prefix',
        'portfolio-',
        '--query',
        'MetricAlarms[].[AlarmName,StateValue,StateReason]',
        '--output',
        output if output == 'json' else 'table',
    ]

    print(
        _c(
            CYAN,
            '$ aws cloudwatch describe-alarms --alarm-name-prefix portfolio-',
        )
    )
    result = subprocess.run(args, check=False)
    return result.returncode
