"""Generacion del SAM template desde lambda.yaml.

El manifiesto `lambda.yaml` es la unica fuente de verdad versionada. El
`template.yaml` SAM se genera a partir de el y es **efimero** (esta en
.gitignore). devtools lo regenera antes de cada build / deploy / local.

Alcance esencial: un solo `AWS::Serverless::Function` con runtime,
handler, memoria, timeout, env vars por stage, layers e IAM policies.
Sin triggers / VPC / alarmas (ver el plan, decision 3).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from serverless.resolve import ManifestError
from serverless.resolve import ResolvedLambda


# Stages validos del manifiesto (la clave 'default' aplica a todos).
_VALID_ENV_STAGES = ('default', 'dev', 'stage', 'prod')


def _logical_id(name: str) -> str:
    """Convierte el name del manifiesto a un LogicalId SAM PascalCase.

    Ejemplo: 'payment-router' -> 'PaymentRouterFunction'.
    """
    parts = name.replace('_', '-').split('-')
    return ''.join(p.capitalize() for p in parts if p) + 'Function'


def _resolve_env(manifest: dict[str, Any], stage: str) -> dict[str, str]:
    """Combina environment.default + environment.<stage> del manifiesto.

    Las claves del stage especifico sobrescriben las de default.
    """
    env_block = manifest.get('environment') or {}
    if not isinstance(env_block, dict):
        raise ManifestError("'environment' debe ser un mapa por stage")

    for key in env_block:
        if key not in _VALID_ENV_STAGES:
            raise ManifestError(
                f'environment.{key} no es un stage valido. '
                f'Validos: {", ".join(_VALID_ENV_STAGES)}',
            )

    merged: dict[str, str] = {}
    merged.update(env_block.get('default') or {})
    if stage in env_block:
        merged.update(env_block.get(stage) or {})
    # SAM exige strings en las env vars.
    return {k: str(v) for k, v in merged.items()}


def build_template(
    manifest: dict[str, Any],
    *,
    stage: str = 'dev',
) -> dict[str, Any]:
    """Construye el dict del SAM template desde el manifiesto.

    Parameters
    ----------
    manifest : dict[str, Any]
        Manifiesto lambda.yaml ya validado y con defaults aplicados.
    stage : str
        Stage objetivo; selecciona el bloque de env vars.

    Returns
    -------
    dict[str, Any]
        Estructura del SAM template lista para volcar a YAML.
    """
    name = manifest['name']
    logical_id = _logical_id(name)

    function_props: dict[str, Any] = {
        'FunctionName': f'{name}-{stage}',
        'CodeUri': '.',
        'Handler': manifest['handler'],
        'Runtime': manifest['runtime'],
        'MemorySize': int(manifest['memory']),
        'Timeout': int(manifest['timeout']),
    }

    env_vars = _resolve_env(manifest, stage)
    if env_vars:
        function_props['Environment'] = {'Variables': env_vars}

    layers = manifest.get('layers') or []
    if layers:
        if not isinstance(layers, list):
            raise ManifestError("'layers' debe ser una lista de ARNs")
        function_props['Layers'] = list(layers)

    iam_policies = manifest.get('iam_policies') or []
    if iam_policies:
        if not isinstance(iam_policies, list):
            raise ManifestError("'iam_policies' debe ser una lista")
        function_props['Policies'] = list(iam_policies)

    return {
        'AWSTemplateFormatVersion': '2010-09-09',
        'Transform': 'AWS::Serverless-2016-10-31',
        'Description': (
            f'Lambda {name} (stage {stage}) - generado por devtools '
            f'desde lambda.yaml. NO editar a mano.'
        ),
        'Resources': {
            logical_id: {
                'Type': 'AWS::Serverless::Function',
                'Properties': function_props,
            },
        },
        'Outputs': {
            f'{logical_id}Arn': {
                'Description': f'ARN de la funcion {name}',
                'Value': {'Fn::GetAtt': [logical_id, 'Arn']},
            },
        },
    }


def generate_sam_file(
    resolved: ResolvedLambda,
    *,
    stage: str = 'dev',
) -> Path:
    """Genera <root>/template.yaml desde el manifiesto del lambda.

    Parameters
    ----------
    resolved : ResolvedLambda
        Lambda objetivo (modo lambda-controller).
    stage : str
        Stage objetivo del template.

    Returns
    -------
    Path
        Ruta del template.yaml generado.

    Raises
    ------
    ManifestError
        Si el lambda no es lambda-controller (modo legacy no genera SAM).
    """
    if not resolved.is_lambda_controller:
        raise ManifestError(
            'sam-generate solo aplica a lambdas con lambda.yaml. '
            'El backend SAM del portfolio ya tiene su template.yaml.',
        )

    try:
        import yaml
    except ImportError as exc:  # pragma: no cover - PyYAML esta en devtools
        raise ManifestError('PyYAML no esta instalado') from exc

    template = build_template(resolved.manifest, stage=stage)
    out_path = resolved.root / 'template.yaml'

    header = (
        '# ARCHIVO GENERADO por devtools desde lambda.yaml. NO EDITAR.\n'
        '# Regenerar: python devtools/run.py serverless sam-generate '
        f'--path=<dir> --stage={stage}\n'
    )
    body = yaml.safe_dump(template, sort_keys=False, allow_unicode=True)
    out_path.write_text(header + body, encoding='utf-8')
    return out_path
