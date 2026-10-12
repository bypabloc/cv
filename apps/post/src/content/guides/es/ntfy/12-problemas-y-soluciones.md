**12**

# Problemas y soluciones

[← Índice](README.md)

---

### Instalación y red

| Problema | Causa | Solución |
| :-- | :-- | :-- |
| `curl https://...` se queda colgado | Puerto 443 cerrado en el firewall de la nube o en `iptables` | Abrir en ambas capas ([capítulo 03](03-requisitos.md)) |
| Error de certificado | El DNS aún no apunta a la IP cuando arrancó Caddy | Esperar la propagación; `journalctl -u caddy -n 50`; `sudo systemctl restart caddy` |
| 502 Bad Gateway | ntfy caído | `systemctl status ntfy` |
| `apt` muere en un servidor de 1 GB | Sin swap | El script crea 1 GB de swap |

### Publicar y recibir

| Problema | Causa | Solución |
| :-- | :-- | :-- |
| 403 al publicar | `auth-default-access: deny-all` sin credenciales | `-H "Authorization: Bearer tk_..."` |
| 401 con token | Token revocado o mal copiado | `sudo ntfy token list admin` |
| Mensajes publicados pero no recibidos | Nadie suscrito a ese tópico | Suscribirse al tópico; al hacerlo solo verás lo publicado en las últimas 24 h |
| App "reconectando…" con ⚠ | Tópico con `/` (se pegó una URL) | Solo el nombre del tópico |
| Notificaciones que no suenan | Permisos u optimización de batería | Permitir notificaciones y "Sin restricciones" de batería |
| iOS no recibe | Falta el relay | `upstream-base-url: "https://ntfy.sh"` |

### Claude Code

| Problema | Causa | Solución |
| :-- | :-- | :-- |
| La notificación nativa dice "Not sent — this terminal is active" | Se omite si estás en la terminal | Hook propio con ntfy ([capítulo 09](09-claude-code.md)) |
| El hook no se dispara | Configuración no recargada | Abrir `/hooks` una vez o iniciar otra sesión |
| `settings.json` deja de cargar | JSON inválido | `jq -e . ~/.claude/settings.json` |

### Reporte de estado

| Problema | Causa | Solución |
| :-- | :-- | :-- |
| "Cada 45 min" con cron dispara a :00 y :45 | `*/45` no es un intervalo real | Timer de systemd con `OnUnitActiveSec=45min` |
| El servidor caído no avisa | No puede reportar si está muerto | La **ausencia** de reporte por más de 45 min es la alarma |
| Demasiados avisos con sonido | Todos con prioridad alta | "OK" con `low`, "FALLO" con `high` |

`troubleshooting` `ntfy`
