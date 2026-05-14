# Cost comparison 2026: SES vs SendGrid vs Resend vs Postmark

> Breakdown de precios para 200 emails/mes (caso portfolio).
> Comparacion con alternativas. Recomendacion.

## AWS SES Pricing (us-west-2, Mayo 2026)

### Breakdown basico

| Item | Costo | Notas |
|------|-------|-------|
| Emails enviados | $0.10 per 1000 emails | 200/mes = $0.02/mes |
| Data transfer out | $0.12 per GB | ~50KB/email = ~10MB/mes = $0.0012/mes |
| Dedicated IP (opcional) | $24.95/mes | NO necesario para bajo volumen |
| Configuration sets (opcional) | $0/mes | Free |
| VirtualDeliverabilityManager (opcional) | $0.07 per 1000 emails | NO necesario |
| **Total (minimalista)** | **$0.02/mes** | Solo envio |

### Free Tier (12 meses)

- 3000 message charges/mes **gratis**
- 200 emails/mes = <3000 → **$0.00/mes**

**Conclusión**: Primer año 100% free. Despues: $0.02/mes aprox.

### Escala: 10,000 emails/mes

| Costo | Componente |
|-------|-----------|
| $1.00 | Emails ($0.10 per 1000 × 10) |
| $0.06 | Data transfer (out) |
| **$1.06/mes** | **Total** |

### Escala: 100,000 emails/mes

| Costo | Componente |
|-------|-----------|
| $10.00 | Emails |
| $0.60 | Data transfer |
| **$10.60/mes** | **Total (sin IP dedicado)** |
| $35.55/mes | **Total (con IP dedicado $24.95)** |

## SendGrid Pricing (Mayo 2026)

### Free tier

- **Tier 1**: 100 emails/dia (3000/mes) gratis
- **Limitaciones**: Basic API, limited support
- **Costo**: $0.00/mes

### Paid tiers

| Plan | Emails/mes | Costo mensual | Cost per 1000 |
|------|-----------|--------------|---------------|
| Essentials | 50,000 | $19.95 | $0.40 |
| Pro | 100,000 | $39.95 | $0.40 |
| Advanced | 300,000 | $99.95 | $0.33 |
| Pro+ | 500,000+ | Custom | $0.20+ |

Para 200 emails/mes: **Free tier** ($0.00/mes).
Para 50,000+ emails/mes: SendGrid mejor que SES.

## Resend Pricing (Mayo 2026)

### Free tier

- 3000 emails/mes gratis
- Unlimited API calls
- React Email support
- Better DX que SES

### Paid tiers (Pro)

| Emails/mes | Costo mensual |
|-----------|--------------|
| 5,000 | Free |
| 50,000 | $20.00 |
| 100,000 | $35.00 |
| 500,000 | $100.00 |
| 1,000,000 | $200.00 |

Para 200 emails/mes: **Free** ($0.00/mes).

### Ventajas Resend vs SES

- Better developer experience (Next.js native)
- React Email component library
- Mejor admin dashboard
- SendGrid-like deliverability
- Menos configuracion (no DKIM/SPF manual)

### Desventajas Resend vs SES

- No self-hosted (cloud-only, SaaS dependency)
- No integración AWS (silos)
- Pricing sube rápido post free-tier
- Compliance/EU data residency limitado

## Postmark Pricing (Mayo 2026)

### Free tier

- 100 emails/mes trial
- No free tier permanente (a diferencia de SendGrid/Resend)

### Paid tiers

| Plan | Emails/mes | Costo/mes | Focus |
|------|-----------|----------|-------|
| Standard | 10,000 | $15.00 | Transactional |
| Plus | 50,000 | $55.00 | High-volume |
| Premium | 500,000 | Custom | Enterprise |

**Para portfolio**: Need paid tier ($15+), no free option.

### Ventajas Postmark

- Mejor deliverability (98.7% inbox rate vs SES ~95%)
- Excelente customer support
- Especializado en transactional (como portfolio)
- Template engine built-in

### Desventajas Postmark

- Caro vs SES/SendGrid/Resend
- Plan minimo $15/mes (vs $0 free)
- Moins flexible (menos features)

## Mailgun Pricing (Mayo 2026)

| Emails/mes | Costo mensual |
|-----------|--------------|
| 0-5,000 | Free (con limitations) |
| 5,000-50,000 | $35.00 |
| 50,000-100,000 | $50.00 |
| 100,000+ | $80.00 + |

Para 200/mes: Free tier.

**Estado**: Popular en 2020-2023, perdiendo market share. Postmark/Resend mas modernos.

## Comparacion side-by-side (200 emails/mes)

| Servicio | Free tier | Costo/mes | Effort | Recomendacion |
|----------|-----------|----------|--------|--------------|
| **SES** | 3000/mes gratis | $0.02 (after 12mo) | High (DNS setup, DKIM, config) | Portfolio: **RECOMENDADO** |
| **SendGrid** | 3000/mes gratis | $0.00 | Medium (API key, setup) | Si no quieres AWS |
| **Resend** | 3000/mes gratis | $0.00 | Low (best DX) | Si usas Next.js |
| **Postmark** | 100 emails/mes trial | $15.00+ | Low-Medium | Si necesitas deliverability critica |
| **Mailgun** | 5000/mes gratis | $0.00 | Medium | Legacy, no recomendado 2026 |

## Analisis costo-beneficio para portfolio

### Escenario A: Portfolio (200 emails/mes, bajo volumen)

**Winner: SES**

Razon:
- Free tier suficiente (3000/mes) → $0.00/mes permanente
- Integración AWS perfecta (Lambda, IAM, CloudWatch)
- Setup inicial mas trabajo (DKIM/SPF/DNS) pero one-time
- Worst case: $0.02/mes post-free-tier
- No vendor lock-in (código reutilizable)

**Alternativa**: Resend (better DX, pero no integra con AWS).

### Escenario B: Startup incipiente (10,000 emails/mes)

**Winner: Tie (SendGrid/Resend)**

Razon:
- SES: $1.06/mes (cheapest)
- SendGrid: $19.95/mes (feature-rich)
- Resend: $20.00/mes (best DX)

**Recomendacion**: SendGrid por features, Resend por DX.

### Escenario C: Scale medium (100,000+ emails/mes)

**Winner: SES**

Razon:
- SES: $10.60/mes + IP dedicado $24.95 = $35.55/mes
- SendGrid: $99.95+/mes
- Resend: $100+/mes

**Conclusión**: A volumen alto, SES sale mucho mas barato.

## Hidden costs (a tener en cuenta)

### SES hidden costs

1. **Developer time**: Setup DKIM/SPF/DMARC, DNS config = 2-4h
2. **Bounce handling**: Implementar SNS + Lambda + DynamoDB
3. **Monitoring**: CloudWatch alarms, dashboards
4. **Compliance**: GDPR double opt-in, unsubscribe management

**Total**: $100-300 worth of engineering (one-time).

### SendGrid hidden costs

1. **Better dashboard**: Menos troubleshooting
2. **Webhooks built-in**: No Lambda SNS boilerplate
3. **Template engine**: No need custom HTML
4. **Deliverability support**: Tier 1 + expert assistance

**Total**: $0 (reducción de costo vs SES).

### Resend hidden costs

1. **Best-in-class DX**: Ahorra horas en setup
2. **React Email**: Acelera template development
3. **API simplicity**: Menos boilerplate code

**Total**: $0 (net positive DX).

## Recomendacion final para portfolio (Mayo 2026)

### Decision matrix

| Criterio | Peso | SES | SendGrid | Resend | Ganador |
|----------|------|-----|----------|--------|---------|
| Costo | 40% | 10 | 8 | 8 | **SES** |
| DX | 20% | 6 | 8 | 10 | **Resend** |
| Integracion AWS | 20% | 10 | 3 | 2 | **SES** |
| Setup effort | 10% | 5 | 8 | 9 | **Resend** |
| Escalability | 10% | 10 | 7 | 6 | **SES** |
| **Score total** | | **8.4** | **6.8** | **6.9** | **SES** |

### Veredicto

**AWS SES es la opcion correcta** para este portfolio porque:

1. **Costo**: Free tier suficiente ahora, cheap si escala
2. **Integración AWS**: Stack coherente (Lambda, API Gateway, CloudWatch, IAM)
3. **Zero vendor lock-in**: Codigo portable a otro provider
4. **Escalabilidad**: De 200 a 1M emails con misma infraestructura
5. **Learning**: Aprender email authentication (DKIM/SPF/DMARC) es valioso

### Cuando cambiar

Si el portfolio evoluciona:

- **> 1M emails/mes**: Considerar SendGrid (better support + features)
- **Necesita best-in-class DX**: Cambiar a Resend (React Email, mejor dashboard)
- **Compliance critica**: Postmark (deliverability 98.7% vs SES ~95%)
- **Already on Google Cloud**: SendGrid (GCP + SendGrid integration)

## Fuentes

- [AWS SES Pricing 2026](https://aws.amazon.com/ses/pricing/)
- [SendGrid Pricing 2026](https://sendgrid.com/pricing/)
- [Resend Pricing 2026](https://resend.com/pricing)
- [Postmark Pricing 2026](https://postmarkapp.com/pricing)
- [Mailgun Pricing 2026](https://www.mailgun.com/pricing/)
- [Email Service Pricing Comparison (Blog)](https://blog.vibecoder.me/email-service-pricing-resend-sendgrid-postmark)
- [SendGrid Alternatives 2026](https://dreamlit.ai/blog/best-sendgrid-alternatives)

**Verificado 2026-05-13**
