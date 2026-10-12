# VM gratis para siempre en Oracle Cloud (y cómo no perderla)

> Guía completa para crear, por CLI, una máquina virtual **Always Free** de Oracle Cloud con IP pública, mantenerla encendida 24/7 sin pagar y evitar que Oracle la **reclame por inactividad**.

**Costo:** USD 0 al mes · **Tiempo:** ~1 h la primera vez · **Nivel:** intermedio (terminal Linux, SSH)

---

## TL;DR

- **Qué obtienes:** una VM Ubuntu 24.04 con IP pública, firewall abierto en 22/80/443 y sin fecha de vencimiento.
- **Formas gratis:** ARM `A1.Flex` (hasta 2 OCPU y 12 GB) o AMD `E2.1.Micro` (1/8 OCPU, 1 GB). A1 suele estar **sin capacidad**; la Micro casi siempre está disponible.
- **El riesgo:** Oracle puede reclamar las instancias cuyo **percentil 95 de CPU** queda bajo 20 % durante 7 días (si la red y, solo en A1, la memoria también quedan bajo 20 %).
- **La solución:** en A1, instancia chica (la RAM usada supera el 20 %); en Micro, un **keepalive de CPU** de prioridad mínima.
- **Monitoreo:** la VM registra su CPU cada minuto, calcula el p95 igual que Oracle y envía un reporte cada 45 min a un webhook.

Sirve para cualquier servicio liviano: un bot, una API pequeña, un servidor de notificaciones, un proxy, un cron.

---

## Índice

| # | Capítulo | Qué resuelve |
| :-- | :-- | :-- |
| 01 | [Por qué Oracle Cloud](01-por-que-oracle.md) | Comparación con Render, Hetzner, AWS y cuándo no usarlo |
| 02 | [Qué incluye la capa gratuita](02-capa-gratuita.md) | Free Trial vs. Always Free, cifras oficiales, duración |
| 03 | [Alta de la cuenta y región](03-alta-y-region.md) | La decisión irreversible: la región principal |
| 04 | [API key y CLI `oci`](04-api-key-y-cli.md) | Trabajar todo desde la terminal |
| 05 | [Red: compartment, VCN, subred y firewall](05-red.md) | Script de red con puertos 22, 80 y 443 |
| 06 | [Crear la instancia](06-instancia.md) | Script con reintentos para A1 y plan B Micro |
| 07 | [Primer arranque de la VM](07-primer-arranque.md) | SSH, swap, `iptables` de Oracle, actualizaciones |
| 08 | [Reclamo por inactividad](08-reclamo-por-inactividad.md) | La regla exacta y el keepalive |
| 09 | [Medir la CPU y reporte de estado](09-monitoreo.md) | p95 como Oracle, reporte cada 45 min |
| 10 | [Operación y borrado](10-operacion-y-borrado.md) | Encender, apagar, respaldar, borrar todo |
| 11 | [Migrar de Micro a A1](11-migrar-a-a1.md) | Cuando aparezca capacidad ARM |
| 12 | [Problemas y soluciones](12-problemas-y-soluciones.md) | Todo lo que falló y cómo se resolvió |

---

## Convenciones

- **Valores de ejemplo:** IP `203.0.113.10` (rango de documentación), región `sa-santiago-1`, nombre del proyecto `mi-vm`. Cámbialos por los tuyos.
- **Placeholders:** `<TENANCY_OCID>`, `<USER_OCID>`, `<FINGERPRINT>`. Los OCID no son secretos; la API key privada sí.
- **Terminal:** Linux o WSL2 con `bash`, `curl`, `jq` y `uv` (o `pipx`).
- **Fecha de los datos:** octubre de 2026. Los capítulos enlazan la fuente oficial cuando existe.

`oracle-cloud` `always-free` `oci-cli` `vm` `self-hosting`
