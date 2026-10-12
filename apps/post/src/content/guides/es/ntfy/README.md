# Tu propio servidor de notificaciones push con ntfy

> Guía completa para montar ntfy con dominio propio, HTTPS automático y acceso privado, recibir notificaciones en el celular desde cualquier script con un `curl`, e integrarlo con Claude Code y con un reporte de estado del servidor.

**Costo:** el de tu VM (puede ser USD 0) · **Tiempo:** ~45 min · **Nivel:** intermedio (Linux, SSH, DNS)

---

## TL;DR

- **Qué obtienes:** `https://ntfy.tu-dominio.com`, privado (usuario y token), con TLS de Let's Encrypt renovado solo.
- **Qué necesitas:** una VM Ubuntu 24.04 con IP pública (cualquier proveedor), un dominio y acceso a su DNS.
- **Cómo publicas:** `curl -H "Authorization: Bearer $TOKEN" -d "Hola" https://ntfy.tu-dominio.com/alertas`.
- **Respaldo:** ntfy.sh gratis recibe el aviso de falla si tu servidor cae.
- **Monitoreo:** el servidor envía cada 45 min su estado (servicios, RAM, disco, días de TLS).

---

## Índice

| # | Capítulo | Qué resuelve |
| :-- | :-- | :-- |
| 01 | [Qué es ntfy y cuándo montar el tuyo](01-que-es-ntfy.md) | Arquitectura y alternativas (ntfy.sh gratis, Supporter, servidor propio) |
| 02 | [ntfy.sh gratis y sus límites](02-ntfy-sh-limites.md) | Cuándo basta la instancia pública |
| 03 | [Requisitos del servidor](03-requisitos.md) | VM, puertos, firewall del proveedor |
| 04 | [DNS](04-dns.md) | Registro `A` sin proxy; Cloudflare por API |
| 05 | [Instalar ntfy + Caddy](05-instalacion.md) | Script idempotente con TLS automático |
| 06 | [Usuarios, permisos y tokens](06-usuarios-y-tokens.md) | `deny-all`, admin, un token por sistema |
| 07 | [Configurar la app del celular](07-app-movil.md) | Android, iOS y el error del tópico con `/` |
| 08 | [Publicar con curl](08-publicar-con-curl.md) | Título, prioridad, emojis, programados |
| 09 | [Avisos desde Claude Code](09-claude-code.md) | Hook `Notification` y script de avisos |
| 10 | [Reporte de estado cada 45 min](10-reporte-de-estado.md) | El servidor informa su salud |
| 11 | [Operación](11-operacion.md) | Contraseñas, tokens, logs, actualizaciones, borrar |
| 12 | [Problemas y soluciones](12-problemas-y-soluciones.md) | Todo lo que falló y cómo se resolvió |

---

## Convenciones

- **Valores de ejemplo:** dominio `ntfy.tu-dominio.com`, IP `203.0.113.10`, usuario `admin`, tópico `alertas`, alias SSH `mi-vm`.
- **Placeholders:** `<TU_TOKEN>`, `<tema-aleatorio>`. Nunca publiques tokens ni contraseñas.
- **Terminal:** Linux o WSL2 con `bash`, `curl` y `jq`.
- **Fecha de los datos:** octubre de 2026.

`ntfy` `push-notifications` `caddy` `self-hosting` `claude-code`
