# Comparativa: Neon vs RDS vs Supabase vs PlanetScale (2026)

> Justificar Neon como eleccion para este portfolio. Comparativa honesta con
> alternativas. Verificado 2026-05-14.

## Matriz rapida

| Criterio | Neon | RDS Postgres | Supabase | PlanetScale |
|----------|------|--------------|----------|-------------|
| **Tipo DB** | PostgreSQL | PostgreSQL | PostgreSQL | MySQL Vitess |
| **Serverless** | ✓ (scale-to-zero) | ✗ (min cost) | ❌ (7d pause) | ❌ (always-on) |
| **Costo portfolio** | $0 (free) | $15-50/mes | $25/mes (auth) | $30/mes |
| **Branching** | ✓✓ (best-in-class) | ✗ (snapshots lento) | ✓ (beta) | ✓ (excellent) |
| **Cold start Lambda** | 150-300ms | 200-500ms (RDS Proxy) | 150-300ms | 200-500ms |
| **Recomendacion** | ✓✓ para este portfolio | ✗ expensive idle | △ si necesitas auth | ✗ not Postgres |

## Neon (RECOMENDADO)

### Ventajas
- **$0 forever**: Free tier perpetuo (cambio post-Databricks 2025)
- **Scale-to-zero**: no pagar en idle (portfolio 95% idle)
- **Branching git-style**: testing a nivel de DB
- **PG18 GA**: asynchronous I/O, features modernas
- **Pooling included**: `-pooler` endpoint built-in
- **PITR**: point-in-time recovery (7-30 dias)

### Desventajas
- **Cold start Lambda**: 150-300ms vs RDS 200-500ms (neutral)
- **Max connections**: RDS Proxy alternativa (RDS Proxy es costoso)
- **Nuevos**: Neon es mas joven que RDS (mas madurez en RDS, pero Neon 2025+ es stable)

### Pricing para portfolio

```
Volumen:          200 contacts, 15k events/mes
Free tier:        100 CU-hours/mes
Usage:            ~0.003 CU-hours/mes (ver doc 01)
Cost:             $0/mes (forever)
Storage:          <100 MB (dentro 0.5 GB free)
Total:            $0/mes
```

**Conclusion**: Neon gana por costo en idle.

---

## RDS Postgres (NO recomendado para esto)

### Ventajas
- **Battle-tested**: AWS, 99.95% uptime SLA
- **Performance predictable**: compute siempre disponible
- **Global coverage**: eu-west-1, us-east-1, ap-*
- **Automated backup**: built-in, encryption

### Desventajas
- **Minimo costo**: db.t4g.micro ~$15/mes (idle o no)
- **SIN scale-to-zero**: costo fijo aunque no lo uses
- **Snapshots lentos**: backup = horas (vs Neon instant branches)
- **Max connections**: RDS Proxy add-on (~$0.015/ho) para Lambda pooling
- **Menos features**: PITR limit 7 dias, no branching native

### Pricing para portfolio

```
db.t4g.micro:             $15-20/mes (always-on)
RDS Proxy:                $7-10/mes (recomendado para Lambda)
Backup storage:           $1-2/mes
Monitoring:               free (CloudWatch)
Total:                    $23-32/mes (minimum)

Idle cost: FULL (no reduction)
```

**Conclusion**: RDS es 23x mas caro que Neon para este portfolio.

---

## Supabase (ALTERNATIVA si necesitas auth/storage)

### Que es
Backend-as-a-Service: PostgreSQL + auth + file storage + realtime + edge functions.

### Ventajas
- **All-in-one**: auth, storage, realtime (vs Neon solo DB)
- **Free tier 500MB DB**: $0 inicial
- **Auth ready**: JWT, OAuth integrado
- **Realtime**: WebSocket subscriptions (para live updates)
- **Edge functions**: serverless functions junto a la DB

### Desventajas
- **NO scale-to-zero**: Free tier pausa despues 7 dias inactivity (peor que Neon)
- **Retencion**: 7 dias (vs Neon 7-30)
- **Costo auth/storage**: paid tiers caros ($25/mes Pro para unlimited auth)
- **Branching beta**: no production-ready (Neon branching es stable)
- **Lock-in**: menos control que Neon directo

### Pricing para portfolio

```
Free tier:        $0 (pero pausa despues 7 dias)
Pro tier:         $25/mes (auth + storage ilimitado)
```

**Conclusion**: Supabase bueno si necesitas auth. Portfolio NO necesita auth (publico). Supabase overkill.

---

## PlanetScale (NO recomendado - not Postgres)

### Que es
MySQL Vitess managed (serverless MySQL, no PostgreSQL).

### Ventajas
- **Branching excellent**: git-style branches (mejor que MySQL estandar)
- **Serverless MySQL**: scale-to-zero como Neon
- **Query insights**: built-in performance monitoring

### Desventajas
- **NOT PostgreSQL**: MySQL Vitess (diferente dialect SQL, features faltantes)
- **Portfolio requiere Postgres**: DynamoDB Streams + Lambda processor written for Postgres
- **Sharding complexity**: Vitess requiere sharding key thinking (Neon/RDS estandar Postgres)

### Pricing

```
Hobby plan:       $0 (pero limitado)
Pro plan:         $30/mes
```

**Conclusion**: PlanetScale es excelente para MySQL apps. Portfolio requiere PostgreSQL → Neon gana.

---

## Aiven for PostgreSQL (NO recomendado)

Managed Postgres en Aiven (EU-focused).

- Costo: $14+/mes minimo
- NO scale-to-zero
- Sin branching
- vs Neon: mas caro, menos features

**Conclusion**: Neon es mejor en cada dimensione.

---

## Vercel Postgres (ya no existe)

Vercel anuncio que migro todos sus PostgreSQL databases a Neon (2024-2025).

- Vercel Postgres: deprecated
- Users: moverse a Neon directo (mejor control) o Vercel-managed Neon integration
- Recomendacion portfolio: Neon directo (sin Vercel lock-in)

---

## Decision tree

```
¿Necesitas authentication (login)?
  ├─ Yes → Supabase (auth + PG)
  └─ No → continue
  
¿Necesitas serverless con scale-to-zero?
  ├─ Yes → Neon (PG) o PlanetScale (MySQL)
  └─ No → RDS (stability-first)
  
¿Usa PostgreSQL o MySQL?
  ├─ PostgreSQL → Neon ✓ (o RDS)
  └─ MySQL → PlanetScale ✓ (o RDS MySQL)
  
¿Presupuesto < $20/mes?
  ├─ Yes → Neon Free tier ✓
  └─ No → cualquiera
```

**Para este portfolio**: PostgreSQL + serverless + <$20/mes → **Neon Free tier (ganador claro)**.

---

## Performance comparison (query latency)

Benchmark aproximado (single query, 10-100 rows):

| Provider | Cold | Warm | Suspended resume |
|----------|------|------|------------------|
| Neon | 50-100ms | 10-30ms | ~250-500ms |
| RDS + Proxy | 50-100ms | 10-30ms | always-on |
| Supabase | 50-100ms | 10-30ms | 250-500ms (7d pause) |
| PlanetScale | 50-100ms | 10-30ms | always-on |

**Query execution**: todos equivalentes. Diferencia es network + connection overhead.

---

## Storage comparison

Escenario: 200 contacts + 15k events = ~100 MB.

| Provider | Free storage | Cost/GB |
|----------|--------------|---------|
| Neon | 0.5 GB | $0.35/mes (post-free) |
| RDS | 20 GB | $0.10/mes (GP2) + backup |
| Supabase | 500 MB | $0.84/GB pro plan |
| PlanetScale | 10 GB | $0.15/GB |

**Para 100 MB**: todos fit free tier (excepto RDS que no tiene free).

---

## Summary

| Caso | Recomendacion | Razon |
|------|---------------|-------|
| Portfolio (este) | **Neon Free** | $0/mes, scale-to-zero, branching, Postgres |
| Startup + auth required | Supabase Pro | All-in-one BaaS, auth ready |
| Enterprise scale | RDS | Stability, SLA, AWS support |
| MySQL + serverless | PlanetScale | Best MySQL serverless (pero no Postgres) |
| Hobbyist + minimal budget | Neon Free | Best free tier 2026 |

**Conclusion**: Neon post-Databricks (May 2025 pricing) es el clear winner para portfolio. Free tier perpetuo, scale-to-zero, branching, PG18, sin sorpresas de costo.

## Referencias

- [Neon vs RDS Comparison](https://vantage.sh/blog/neon-vs-aws-aurora-serverless-postgres-cost-scale-to-zero)
- [Neon vs Supabase Detailed](https://vela.simplyblock.io/neon-vs-supabase)
- [Best PostgreSQL Hosting 2026](https://dev.to/philip_mcclarence_2ef9475/best-postgresql-hosting-in-2026-rds-vs-supabase-vs-neon-vs-self-hosted-5fkp)
- [PlanetScale Official](https://planetscale.com)
- [Supabase vs Neon](https://www.bytebase.com/blog/neon-vs-supabase)
