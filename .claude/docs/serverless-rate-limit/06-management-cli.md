---
title: CLI de Gestion - devtools/serverless/rate_limit
description: Subcomandos para gestionar reglas, whitelist, blacklist, stats.
status: stable
last-reviewed: 2026-05-14
---

# 06. CLI de Gestion - rate-limit

> Subcomandos para gestionar reglas de rate-limit desde CLI. Integrar en devtools.

[← Auto-blacklist](./05-auto-blacklist-bot-detection.md) | [README](./README.md) | [Siguiente: Observability →](./07-observability.md)

## Ubicacion

`devtools/serverless/rate_limit/main.py` + `flags.py`

## Subcomandos

### 1. `rate-limit list`

```bash
# Listar todas las reglas
python devtools/run.py rate-limit list

# Output:
# endpoint#/contact       limit=3  window=60  action=BLOCK  created=2026-05-14
# endpoint#/track         limit=30 window=60  action=BLOCK  created=2026-05-14
# ip#whitelist#203.0.113.1        reason="Pablo personal IP"
# ip#blacklist#198.51.100.42      expires=2026-05-15 reason="Bot detected"
# country#CN              reason="High attack volume from China"
```

### 2. `rate-limit show <key>`

```bash
# Ver detalle de una regla
python devtools/run.py rate-limit show endpoint#/contact

# Output:
# rule_key: endpoint#/contact
# kind: endpoint
# limit: 3
# window_seconds: 60
# action: BLOCK
# created_at: 2026-05-14T00:00:00Z
# created_by: admin
```

### 3. `rate-limit set <flags>`

```bash
# Crear o actualizar regla de endpoint
python devtools/run.py rate-limit set \
  --endpoint=/contact \
  --limit=5 \
  --window=300 \
  --action=BLOCK

# Crear regla de pais
python devtools/run.py rate-limit set \
  --country=CN \
  --action=BLOCK \
  --reason="Attack volume"
```

### 4. `rate-limit allow <ip>`

```bash
# Whitelist IP (permitir sin limite)
python devtools/run.py rate-limit allow --ip=203.0.113.1 --reason="Pablo personal"

# Output:
# Added whitelist: 203.0.113.1
```

### 5. `rate-limit block <ip> [--ttl=86400]`

```bash
# Blacklist IP con TTL opcional (default 24h)
python devtools/run.py rate-limit block \
  --ip=198.51.100.42 \
  --reason="Manual block" \
  --ttl=86400

# Output:
# Added blacklist: 198.51.100.42 (expires 2026-05-15)
```

### 6. `rate-limit unblock <ip>`

```bash
# Remover blacklist
python devtools/run.py rate-limit unblock --ip=198.51.100.42

# Output:
# Removed blacklist: 198.51.100.42
```

### 7. `rate-limit stats [--since=1h] [--top=10]`

```bash
# Ver estadisticas (top IPs bloqueadas, etc)
python devtools/run.py rate-limit stats --since=1h --top=10

# Output:
# Top blocked IPs (last 1 hour):
# 198.51.100.42      15 blocked requests
# 203.0.113.99       8 blocked requests
# 192.0.2.10         3 blocked requests
#
# Auto-blacklist triggers: 2
# Rate-limit blocks: 50
# Total requests: 1024
```

### 8. `rate-limit clear-buckets [--confirm]`

```bash
# DESTRUCTIVO: borrar todos los buckets de contadores (debugging)
python devtools/run.py rate-limit clear-buckets --confirm

# Output:
# Deleted 342 rate-limit buckets.
# WARNING: Esta operacion no se puede revertir.
```

## Implementacion (skeleton)

```python
# devtools/serverless/rate_limit/main.py

import json
import argparse
from datetime import datetime, timedelta
from .flags import parse_rate_limit_flags
from common.rate_limit.client import DynamoDBClient

class RateLimitCLI:
    def __init__(self, env: str = 'prod'):
        self.env = env
        self.client = DynamoDBClient()
    
    def list(self):
        """List all rules."""
        items = self.client.scan_items('rules')
        for item in sorted(items, key=lambda x: x['rule_key']):
            rule_key = item['rule_key']
            kind = item.get('kind', 'unknown')
            
            if kind == 'endpoint':
                print(f"{rule_key:<30} limit={item['limit']:<3} window={item['window_seconds']}")
            elif 'whitelist' in rule_key or 'blacklist' in rule_key:
                expires = ""
                if 'expires_at' in item:
                    expires = f" expires={datetime.fromtimestamp(item['expires_at']).date()}"
                print(f"{rule_key:<30} {item.get('reason', '')}{expires}")
            else:
                print(f"{rule_key:<30} {item.get('reason', '')}")
    
    def show(self, key: str):
        """Show detail of a rule."""
        item = self.client.get_item('rules', {'rule_key': key})
        if not item:
            print(f"Not found: {key}")
            return
        
        for field, value in item.items():
            print(f"{field}: {value}")
    
    def set(self, flags: dict):
        """Create or update rule."""
        if 'endpoint' in flags:
            rule_key = f"endpoint#{flags['endpoint']}"
            kind = 'endpoint'
        elif 'country' in flags:
            rule_key = f"country#{flags['country']}"
            kind = 'country_block'
        else:
            print("ERROR: --endpoint or --country required")
            return
        
        import time
        now = int(time.time())
        
        self.client.update_item(
            'rules',
            {'rule_key': rule_key},
            (
                'SET kind = :kind, '
                '    limit = if_not_exists(limit, :limit), '
                '    window_seconds = if_not_exists(window_seconds, :window), '
                '    action = :action, '
                '    created_at = if_not_exists(created_at, :now), '
                '    created_by = if_not_exists(created_by, :creator), '
                '    reason = :reason'
            ),
            {
                ':kind': kind,
                ':limit': flags.get('limit', 3),
                ':window': flags.get('window', 60),
                ':action': flags.get('action', 'BLOCK'),
                ':now': now,
                ':creator': flags.get('created_by', 'admin'),
                ':reason': flags.get('reason', ''),
            },
        )
        print(f"Updated: {rule_key}")
    
    def allow(self, ip: str, reason: str = ""):
        """Whitelist IP."""
        import time
        
        rule_key = f"ip#whitelist#{ip}"
        self.client.update_item(
            'rules',
            {'rule_key': rule_key},
            (
                'SET kind = :kind, '
                '    created_at = :now, '
                '    created_by = :creator, '
                '    reason = :reason'
            ),
            {
                ':kind': 'ip_whitelist',
                ':now': int(time.time()),
                ':creator': 'admin',
                ':reason': reason,
            },
        )
        print(f"Added whitelist: {ip}")
    
    def block(self, ip: str, ttl_hours: int = 24, reason: str = ""):
        """Blacklist IP."""
        import time
        
        rule_key = f"ip#blacklist#{ip}"
        now = int(time.time())
        expires_at = now + (ttl_hours * 3600)
        
        self.client.update_item(
            'rules',
            {'rule_key': rule_key},
            (
                'SET kind = :kind, '
                '    expires_at = :expires_at, '
                '    created_at = :now, '
                '    created_by = :creator, '
                '    reason = :reason, '
                '    ttl_hours = :ttl'
            ),
            {
                ':kind': 'ip_blacklist',
                ':expires_at': expires_at,
                ':now': now,
                ':creator': 'admin',
                ':reason': reason,
                ':ttl': ttl_hours,
            },
        )
        expire_date = datetime.fromtimestamp(expires_at).date()
        print(f"Added blacklist: {ip} (expires {expire_date})")
    
    def unblock(self, ip: str):
        """Remove blacklist."""
        rule_key = f"ip#blacklist#{ip}"
        # DynamoDB no tiene DELETE directo via UpdateItem
        # Usar client.delete_item() (simplificado aqui)
        try:
            self.client.dynamodb.Table(
                self.client.buckets_table.name
                if 'bucket' in rule_key
                else self.client.rules_table.name
            ).delete_item(Key={'rule_key': rule_key})
            print(f"Removed blacklist: {ip}")
        except Exception as e:
            print(f"Error: {e}")
    
    def stats(self, since_hours: int = 1, top_n: int = 10):
        """Show stats."""
        import time
        
        # Buscar en CloudWatch logs (simplificado)
        # En prod: usar CloudWatch Insights
        print(f"Rate-limit stats (last {since_hours}h):")
        print("(Implementar queryCloudWatch Insights)")

def main(action: str, flags: dict):
    cli = RateLimitCLI()
    
    if action == 'list':
        cli.list()
    elif action == 'show':
        cli.show(flags['key'])
    elif action == 'set':
        cli.set(flags)
    elif action == 'allow':
        cli.allow(flags['ip'], flags.get('reason', ''))
    elif action == 'block':
        cli.block(flags['ip'], flags.get('ttl', 86400), flags.get('reason', ''))
    elif action == 'unblock':
        cli.unblock(flags['ip'])
    elif action == 'stats':
        cli.stats(flags.get('since', 1), flags.get('top', 10))
    else:
        print(f"Unknown action: {action}")
```

```python
# devtools/serverless/rate_limit/flags.py

import argparse

def parse_rate_limit_flags(action: str) -> dict:
    parser = argparse.ArgumentParser(description='Rate-limit CLI')
    
    if action == 'list':
        pass  # No flags
    elif action == 'show':
        parser.add_argument('key', help='rule_key')
    elif action == 'set':
        parser.add_argument('--endpoint', help='Endpoint path')
        parser.add_argument('--country', help='Country code (CN, RU, etc)')
        parser.add_argument('--limit', type=int, default=3, help='Request limit')
        parser.add_argument('--window', type=int, default=60, help='Window seconds')
        parser.add_argument('--action', default='BLOCK', help='BLOCK or THROTTLE')
        parser.add_argument('--reason', default='', help='Rule reason')
    elif action in ['allow', 'block']:
        parser.add_argument('--ip', required=True, help='IP address')
        parser.add_argument('--reason', default='', help='Reason for block/allow')
        if action == 'block':
            parser.add_argument('--ttl', type=int, default=86400, help='TTL seconds')
    elif action == 'unblock':
        parser.add_argument('--ip', required=True, help='IP address')
    elif action == 'stats':
        parser.add_argument('--since', type=int, default=1, help='Last N hours')
        parser.add_argument('--top', type=int, default=10, help='Top N results')
    
    args = parser.parse_args()
    return vars(args)
```

## Integracion en devtools

```python
# devtools/run.py (actualizar)

from serverless.rate_limit import main, parse_rate_limit_flags

if script == 'rate-limit':
    action = args[0] if args else 'list'
    flags = parse_rate_limit_flags(action)
    main(action, flags)
```

---

**Verificado a**: 2026-05-14

**Fuentes**: Implementacion propia basada en AWS SDK boto3
