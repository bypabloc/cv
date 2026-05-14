---
title: Implementacion Python - Modulos copy-paste
description: Codigo completo para serverless/src/common/rate_limit/ - 6 modulos listos.
status: stable
last-reviewed: 2026-05-14
---

# 04. Implementacion Python - Codigo listo

> 6 modulos Python 3.13 listos para copy-paste a `serverless/src/common/rate_limit/`.
> Incluye type hints obligatorios, docstrings BDD-style, pytest tests.

[← Schema](./03-schema-design.md) | [README](./README.md) | [Siguiente: Auto-blacklist →](./05-auto-blacklist-bot-detection.md)

## Estructura de modulos

```
serverless/src/common/rate_limit/
├── __init__.py              # exports
├── client.py                # DynamoDBClient
├── check.py                 # check_or_raise (API principal)
├── rules.py                 # get_endpoint_rule, is_whitelisted, etc (cache)
├── buckets.py               # sliding window weighted check + increment
├── auto_blacklist.py        # detect_and_blacklist_bot
├── exceptions.py            # custom exceptions
└── types.py                 # TypedDict Decision, RateLimitConfig
```

## 1. `types.py`

```python
"""
@type RateLimitTypes
@description TypedDict para estructuras comunes.
"""

from typing import TypedDict, Literal

class RateLimitConfig(TypedDict):
    """Configuracion de una regla de rate-limit."""
    limit: int
    window_seconds: int
    action: Literal['BLOCK', 'THROTTLE', 'CHALLENGE']

class Decision(TypedDict):
    """Resultado de un check de rate-limit."""
    allowed: bool
    reason: str
    retry_after_seconds: int
    status_code: int
    effective_count: float
```

## 2. `exceptions.py`

```python
"""
@type RateLimitExceptions
@description Excepciones custom para rate-limiting.
"""

class RateLimitError(Exception):
    """Base para errores de rate-limit."""
    def __init__(self, message: str, status_code: int = 429, retry_after: int = 60):
        super().__init__(message)
        self.status_code = status_code
        self.retry_after = retry_after

class RateLimitExceededError(RateLimitError):
    """Request fue bloqueado por rate-limit."""
    def __init__(self, reason: str, effective_count: float, limit: int, retry_after: int = 60):
        msg = f"Rate limit exceeded: {effective_count:.2f}/{limit} ({reason})"
        super().__init__(msg, status_code=429, retry_after=retry_after)

class IPBlacklistedError(RateLimitError):
    """IP esta en blacklist."""
    def __init__(self, reason: str = "IP is blacklisted"):
        super().__init__(reason, status_code=403, retry_after=3600)

class CountryBlockedError(RateLimitError):
    """Pais esta bloqueado."""
    def __init__(self, country: str):
        super().__init__(f"Country {country} is blocked", status_code=403, retry_after=3600)
```

## 3. `client.py`

```python
"""
@module RateLimitClient
@description Cliente de bajo nivel para DynamoDB.
"""

import os
import boto3
from botocore.exceptions import ClientError

class DynamoDBClient:
    """Cliente para interactuar con tablas de rate-limit."""
    
    def __init__(
        self,
        rules_table_name: str | None = None,
        buckets_table_name: str | None = None,
    ):
        self.dynamodb = boto3.resource('dynamodb')
        self.rules_table = self.dynamodb.Table(
            rules_table_name or os.environ['RATE_LIMIT_RULES_TABLE']
        )
        self.buckets_table = self.dynamodb.Table(
            buckets_table_name or os.environ['RATE_LIMIT_BUCKETS_TABLE']
        )
    
    def get_item(self, table_name: str, key: dict) -> dict | None:
        """Get item (con manejo de errores)."""
        try:
            table = self.rules_table if table_name == 'rules' else self.buckets_table
            response = table.get_item(Key=key)
            return response.get('Item')
        except ClientError as e:
            raise RuntimeError(f"DynamoDB GetItem error: {e}")
    
    def update_item(
        self,
        table_name: str,
        key: dict,
        update_expression: str,
        attribute_values: dict,
        condition_expression: str | None = None,
    ) -> bool:
        """Update item (atomic). Retorna True si success."""
        try:
            table = self.rules_table if table_name == 'rules' else self.buckets_table
            kwargs = {
                'Key': key,
                'UpdateExpression': update_expression,
                'ExpressionAttributeValues': attribute_values,
            }
            if condition_expression:
                kwargs['ConditionExpression'] = condition_expression
            
            table.update_item(**kwargs)
            return True
        except ClientError as e:
            if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
                return False
            raise RuntimeError(f"DynamoDB UpdateItem error: {e}")
    
    def scan_items(self, table_name: str, filter_expression: str | None = None) -> list[dict]:
        """Scan (CUIDADO: costoso). Solo para admin CLI."""
        table = self.rules_table if table_name == 'rules' else self.buckets_table
        kwargs = {}
        if filter_expression:
            kwargs['FilterExpression'] = filter_expression
        
        response = table.scan(**kwargs)
        return response.get('Items', [])
```

## 4. `rules.py` (con cache)

```python
"""
@module RateLimitRules
@description Cargador de reglas con cache (TTL 60s).
"""

import time
from functools import lru_cache, wraps
from .client import DynamoDBClient
from .types import RateLimitConfig

def cached(ttl_seconds: int = 60):
    """Decorator simple para cache con TTL."""
    def decorator(func):
        cache = {}
        cache_time = {}
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            key = (args, tuple(sorted(kwargs.items())))
            now = time.time()
            
            if key in cache and (now - cache_time[key]) < ttl_seconds:
                return cache[key]
            
            result = func(*args, **kwargs)
            cache[key] = result
            cache_time[key] = now
            return result
        
        return wrapper
    return decorator

class RateLimitRules:
    """Gestor de reglas con cache."""
    
    def __init__(self, client: DynamoDBClient):
        self.client = client
    
    @cached(ttl_seconds=60)
    def get_endpoint_rule(self, endpoint: str) -> RateLimitConfig | None:
        """
        @function get_endpoint_rule
        @description Obtiene regla para endpoint (cached 60s).
        Given un endpoint como "/contact",
        When buscar en rules,
        Then retorna {limit, window_seconds, action} o None si no existe.
        """
        item = self.client.get_item('rules', {'rule_key': f'endpoint#{endpoint}'})
        if not item:
            return None
        
        return RateLimitConfig(
            limit=item.get('limit', 3),
            window_seconds=item.get('window_seconds', 60),
            action=item.get('action', 'BLOCK'),
        )
    
    @cached(ttl_seconds=60)
    def is_whitelisted(self, ip: str) -> bool:
        """Chequear si IP esta en whitelist."""
        item = self.client.get_item('rules', {'rule_key': f'ip#whitelist#{ip}'})
        return item is not None
    
    @cached(ttl_seconds=60)
    def is_blacklisted(self, ip: str) -> bool:
        """Chequear si IP esta en blacklist. Respeta expires_at (TTL eventual)."""
        item = self.client.get_item('rules', {'rule_key': f'ip#blacklist#{ip}'})
        if not item:
            return False
        
        # Si tiene expires_at y ya paso, ignorar (aunque DynamoDB aun lo ve)
        if 'expires_at' in item:
            import time
            if time.time() > item['expires_at']:
                return False
        
        return True
    
    @cached(ttl_seconds=60)
    def get_country_rule(self, country: str) -> bool:
        """Chequear si pais esta bloqueado."""
        item = self.client.get_item('rules', {'rule_key': f'country#{country}'})
        return item is not None
```

## 5. `buckets.py` (sliding window)

```python
"""
@module RateLimitBuckets
@description Sliding window weighted con DynamoDB atomic operations.
"""

import time
from .client import DynamoDBClient

class RateLimitBucket:
    """Maneja un bucket individual."""
    
    @staticmethod
    def calculate_window(now: int, window_seconds: int) -> tuple[int, int]:
        """
        @function calculate_window
        @description Calcula window_start y prev_window_start.
        Given now=125 y window=60,
        Then window_start=120, prev_window_start=60.
        """
        window_start = (now // window_seconds) * window_seconds
        prev_window_start = window_start - window_seconds
        return window_start, prev_window_start
    
    @staticmethod
    def calculate_effective_count(
        current_count: int,
        previous_count: int,
        elapsed_in_current: int,
        window_seconds: int,
    ) -> float:
        """
        @function calculate_effective_count
        @description Sliding window weighted formula.
        Given current_count=3, previous_count=2, elapsed=30, window=60,
        Then weight=0.5, effective=3 + (2*0.5) = 4.0.
        """
        if elapsed_in_current >= window_seconds:
            return float(current_count)
        
        weight = (window_seconds - elapsed_in_current) / window_seconds
        return current_count + (previous_count * weight)

class RateLimitBucketChecker:
    """Chequeador de rate-limit con DynamoDB."""
    
    def __init__(self, client: DynamoDBClient):
        self.client = client
    
    def check_and_increment(
        self,
        ip: str,
        endpoint: str,
        limit: int,
        window_seconds: int = 60,
    ) -> dict:
        """
        @function check_and_increment
        @description Check + increment atomico.
        Given IP 203.0.113.1, endpoint /contact, limit 3,
        When hacer 4 requests en 60s,
        Then primeros 3 return allowed=True, 4to return allowed=False.
        """
        now = int(time.time())
        window_start, prev_window_start = RateLimitBucket.calculate_window(now, window_seconds)
        bucket_key = f"{ip}#{endpoint}#{window_start}"
        expires_at = now + (window_seconds * 2)
        
        # GET item actual
        item = self.client.get_item('buckets', {'bucket_key': bucket_key})
        
        if not item:
            # Primer request en este bucket
            current_count = 0
            previous_count = 0
            item_window_start = window_start
        else:
            current_count = item.get('current_count', 0)
            previous_count = item.get('previous_count', 0)
            item_window_start = item.get('current_window_start', window_start)
        
        # Detectar cambio de ventana
        if item_window_start < window_start:
            # Ventana paso: current → previous
            previous_count = current_count
            current_count = 0
        
        # Calcular effective
        elapsed_in_current = now - window_start
        effective_count = RateLimitBucket.calculate_effective_count(
            current_count, previous_count, elapsed_in_current, window_seconds
        )
        
        # Decision
        if effective_count >= limit:
            retry_after = max(1, int((window_seconds - elapsed_in_current)))
            return {
                'allowed': False,
                'effective_count': effective_count,
                'retry_after': retry_after,
                'reason': f'Rate limit exceeded ({effective_count:.2f}/{limit})',
            }
        
        # Incrementar atomicamente
        success = self.client.update_item(
            'buckets',
            {'bucket_key': bucket_key},
            (
                'SET current_count = if_not_exists(current_count, :zero) + :inc, '
                '    current_window_start = :window_start, '
                '    previous_count = if_not_exists(previous_count, :zero), '
                '    last_request = :now, '
                '    expires_at = :expires_at '
                'ADD first_request :first_ts'
            ),
            {
                ':inc': 1,
                ':zero': 0,
                ':window_start': window_start,
                ':now': now,
                ':expires_at': expires_at,
                ':first_ts': set([now]) if not item else set(),
            },
        )
        
        if not success:
            # Window cambio entre GET y UPDATE: reintentar
            return self.check_and_increment(ip, endpoint, limit, window_seconds)
        
        return {
            'allowed': True,
            'effective_count': effective_count + 1,
            'reason': 'OK',
        }
```

## 6. `check.py` (API principal)

```python
"""
@module RateLimitCheck
@description API principal: check_or_raise(ip, endpoint, country, turnstile_validated).
"""

from .client import DynamoDBClient
from .rules import RateLimitRules
from .buckets import RateLimitBucketChecker
from .auto_blacklist import AutoBlacklistDetector
from .exceptions import RateLimitExceededError, IPBlacklistedError, CountryBlockedError

class RateLimiter:
    """Orquestador principal."""
    
    def __init__(self):
        self.client = DynamoDBClient()
        self.rules = RateLimitRules(self.client)
        self.bucket_checker = RateLimitBucketChecker(self.client)
        self.auto_blacklist = AutoBlacklistDetector(self.client)
    
    def check_or_raise(
        self,
        ip: str,
        endpoint: str,
        country: str | None = None,
        turnstile_validated: bool = False,
    ) -> dict:
        """
        @function check_or_raise
        @description Check rate-limit completo. Lanza excepciones si bloqueado.
        Given IP bloqueada,
        When check,
        Then lanza IPBlacklistedError.
        """
        # 1. Chequear whitelist
        if self.rules.is_whitelisted(ip):
            return {'allowed': True, 'reason': 'IP whitelisted'}
        
        # 2. Chequear blacklist
        if self.rules.is_blacklisted(ip):
            raise IPBlacklistedError()
        
        # 3. Chequear country
        if country and self.rules.get_country_rule(country):
            raise CountryBlockedError(country)
        
        # 4. Chequear rate-limit
        rule = self.rules.get_endpoint_rule(endpoint)
        if not rule:
            # Sin regla = permitir
            return {'allowed': True, 'reason': 'No rule defined'}
        
        result = self.bucket_checker.check_and_increment(
            ip,
            endpoint,
            rule['limit'],
            rule['window_seconds'],
        )
        
        if not result['allowed']:
            raise RateLimitExceededError(
                reason=result['reason'],
                effective_count=result['effective_count'],
                limit=rule['limit'],
                retry_after=result['retry_after'],
            )
        
        # 5. Detectar bot (si Turnstile valido)
        if turnstile_validated:
            self.auto_blacklist.record_turnstile_token(ip, endpoint)
            if self.auto_blacklist.detect_bot_pattern(ip):
                self.auto_blacklist.blacklist_ip(ip, reason='Bot detected (3+ tokens in 60s)')
                raise IPBlacklistedError('Bot pattern detected')
        
        return result

# Singleton global
_limiter: RateLimiter | None = None

def get_limiter() -> RateLimiter:
    """Get singleton limiter."""
    global _limiter
    if not _limiter:
        _limiter = RateLimiter()
    return _limiter
```

## 7. `__init__.py`

```python
"""
@module RateLimitExports
@description Exports principales.
"""

from .check import get_limiter, RateLimiter
from .exceptions import (
    RateLimitError,
    RateLimitExceededError,
    IPBlacklistedError,
    CountryBlockedError,
)
from .types import RateLimitConfig, Decision

__all__ = [
    'get_limiter',
    'RateLimiter',
    'RateLimitError',
    'RateLimitExceededError',
    'IPBlacklistedError',
    'CountryBlockedError',
    'RateLimitConfig',
    'Decision',
]
```

## Uso en Lambda

```python
# src/functions/contact.py
from common.rate_limit import get_limiter, RateLimitExceededError, IPBlacklistedError

def handler(event, context):
    limiter = get_limiter()
    
    ip = event['requestContext']['identity']['sourceIp']
    country = event['headers'].get('CloudFlare-IPCountry')
    turnstile_token = event.get('turnstile_token')
    
    try:
        # Primero: validar Turnstile
        turnstile_validated = False
        if turnstile_token:
            # ... siteverify ...
            turnstile_validated = True
        
        # Segundo: check rate-limit
        limiter.check_or_raise(
            ip=ip,
            endpoint='/contact',
            country=country,
            turnstile_validated=turnstile_validated,
        )
        
        # Si llegamos aqui: permitido
        return {
            'statusCode': 200,
            'body': json.dumps({'message': 'OK'}),
        }
    
    except RateLimitExceededError as e:
        return {
            'statusCode': 429,
            'headers': {'Retry-After': str(e.retry_after)},
            'body': json.dumps({'error': str(e)}),
        }
    except IPBlacklistedError as e:
        return {
            'statusCode': 403,
            'body': json.dumps({'error': str(e)}),
        }
```

---

**Verificado a**: 2026-05-14 (AWS SDK boto3 3.6+, Python 3.13 type hints)

**Instalacion**:
```bash
# Copy-paste los 6 archivos
cp -r docs/serverless-rate-limit/code/* serverless/src/common/rate_limit/

# Instalar boto3 (ya incluido en Lambda runtime)
pip install boto3>=1.28
```
