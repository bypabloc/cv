**01**

# Por qué Oracle Cloud

[← Índice](README.md)

---

### El problema

- Muchos servicios pequeños necesitan una máquina **siempre encendida** con **IP pública**: un bot, un webhook, un servidor de notificaciones, una API interna.
- Las capas gratis de PaaS "duermen" el servicio si no recibe tráfico.
- Las capas gratis de AWS y GCP vencen o cobran la IPv4.

### Lo que ofrece Oracle Always Free

- VM gratis **sin fecha de vencimiento** (no es una prueba de 12 meses).
- IP pública incluida y **10 TB** de tráfico de salida al mes.
- Hasta 2 VM AMD Micro (1 GB) o el equivalente a 2 OCPU y 12 GB en ARM.
- No se apaga por falta de tráfico: queda encendida 24/7.

### Comparación

Precios aproximados a octubre de 2026.

| Opción | Costo mensual | Siempre encendida | Disco persistente | Problema |
| :-- | :-- | :-- | :-- | :-- |
| **Oracle Always Free** | **USD 0** | Sí | Sí (hasta 200 GB) | Reclamo por inactividad; alta engorrosa; A1 sin capacidad |
| Render Free | USD 0 | **No**: duerme a los 15 min sin tráfico | **No** | Arranque de ~1 min; 750 h/mes; reinicios arbitrarios |
| Hetzner (VPS más chico) | ~EUR 4–5 | Sí | Sí | Se paga |
| AWS `t4g.nano` | ~USD 3 + ~USD 3,6 por la IPv4 | Sí | Sí | ~USD 7 por una máquina mínima |
| PC propia | USD 0 | Solo si está encendida | Sí | Sin IP pública fija; depende de tu equipo |

### Render Free en detalle

Fuente: [render.com/docs/free](https://render.com/docs/free).

- Se apaga tras **15 min** sin tráfico entrante y tarda **~1 min** en volver: la primera petición falla o espera.
- **750 h** al mes por workspace: un servicio 24/7 consume 744 h en un mes de 31 días, así que solo cabe uno.
- **Sin disco persistente**: todo lo local se pierde en cada reinicio o redespliegue.
- Puede reiniciar los servicios gratuitos en cualquier momento.

Útil para demos; no para algo que debe responder siempre.

### Cuándo NO usar Oracle Always Free

- **Producción con clientes:** Oracle puede reclamar la instancia y no documenta aviso previo.
- **Datos sin respaldo:** la VM puede desaparecer.
- **Si no quieres administrar un servidor:** parches, firewall y monitoreo son tu responsabilidad.

`oracle-cloud` `always-free` `comparacion` `render` `hetzner` `aws`
