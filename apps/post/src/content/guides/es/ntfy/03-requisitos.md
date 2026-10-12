**03**

# Requisitos del servidor

[← Índice](README.md)

---

### La máquina

| Requisito | Mínimo | Nota |
| :-- | :-- | :-- |
| Sistema | Ubuntu 24.04 (amd64 o arm64) | Los comandos usan `apt` y `systemd` |
| RAM | 1 GB | ntfy + Caddy usan ~100 MB; agrega swap si tienes 1 GB |
| CPU | Cualquiera | Una fracción de vCPU sobra |
| Disco | ~2 GB libres | Caché de mensajes y logs |
| Red | IP pública fija | Debe estar encendida 24/7 |
| Acceso | SSH con un usuario con `sudo` | Los ejemplos usan el alias `mi-vm` |

Sirve cualquier proveedor: Hetzner, DigitalOcean, AWS, la capa gratuita de algún proveedor de nube, un servidor en casa con IP fija.

Alias SSH recomendado en `~/.ssh/config`:

```
Host mi-vm
  HostName 203.0.113.10
  User ubuntu
  IdentityFile ~/.ssh/mi_clave
```

### Puertos

| Puerto | Para qué |
| :-- | :-- |
| 22 | SSH |
| 80 | Validación de Let's Encrypt (HTTP-01) y redirección a HTTPS |
| 443 | ntfy por HTTPS |

Ábrelos en **todas** las capas que tenga tu proveedor:

1. El firewall de la nube (Security Group, Security List, Firewall de Hetzner…).
2. El firewall **dentro** de la VM. Algunas imágenes traen `iptables` con un `REJECT` final que bloquea todo salvo SSH; el script de instalación lo resuelve.

### Comprobar antes de instalar

```bash
ssh mi-vm 'lsb_release -ds; dpkg --print-architecture; free -m | sed -n 2p; sudo iptables -S INPUT'
```

Si ves `-A INPUT -j REJECT` al final, el script de instalación abre 80 y 443 antes de esa regla.

### Dominio

- Un subdominio (`ntfy.tu-dominio.com`) con acceso para crear un registro `A` ([capítulo 04](04-dns.md)).
- El registro debe existir **antes** de instalar Caddy.

`ntfy` `requisitos` `vps` `firewall`
