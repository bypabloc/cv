**11**

# Operación

[← Índice](README.md)

Comandos en el servidor (`ssh mi-vm`).

---

### Estado y logs

```bash
systemctl status ntfy caddy --no-pager
journalctl -u ntfy -n 50 --no-pager
journalctl -u caddy -n 50 --no-pager       # certificados, errores de proxy
curl -s http://127.0.0.1:2586/v1/health     # ntfy directo, sin Caddy
```

### Cambiar la contraseña del admin

```bash
sudo ntfy user change-pass admin
```

Actualízala también en la app del celular.

### Rotar tokens

```bash
sudo ntfy token add --label mi-pc admin        # nuevo
sudo ntfy token list admin
sudo ntfy token remove admin tk_viejo          # revocar
```

Para el token del reporte: edita `NTFY_TOKEN` en `/etc/ntfy-report.env` con `sudoedit`.

### Cambiar configuración

```bash
sudoedit /etc/ntfy/server.yml && sudo systemctl restart ntfy
sudoedit /etc/caddy/Caddyfile && sudo systemctl reload caddy
```

### Actualizar

```bash
sudo apt-get update && sudo apt-get install --only-upgrade ntfy caddy
```

`unattended-upgrades` cubre los parches de seguridad del sistema; ntfy y Caddy vienen de repositorios externos y conviene revisarlos de vez en cuando. Si el reporte dice "requiere reinicio": `sudo reboot` (todo arranca solo).

### Respaldo

| Archivo | Contenido |
| :-- | :-- |
| `/var/lib/ntfy/user.db` | Usuarios y tokens |
| `/etc/ntfy/server.yml` | Configuración de ntfy |
| `/etc/caddy/Caddyfile` | Proxy y TLS |
| `/etc/ntfy-report.env` | Token del reporte (secreto) |

```bash
ssh mi-vm 'sudo tar czf - /var/lib/ntfy/user.db /etc/ntfy /etc/caddy/Caddyfile' > ntfy-respaldo-$(date +%F).tgz
```

La caché de mensajes (24 h) no necesita respaldo.

### Mudar a otro servidor

1. Ejecuta `setup-ntfy.sh` en el nuevo ([capítulo 05](05-instalacion.md)).
2. Copia `user.db` (los tokens existentes siguen sirviendo):

```bash
ssh mi-vm 'sudo cat /var/lib/ntfy/user.db' | ssh nuevo-vm \
  'sudo systemctl stop ntfy && sudo tee /var/lib/ntfy/user.db >/dev/null && sudo chown ntfy:ntfy /var/lib/ntfy/user.db && sudo systemctl start ntfy'
```

3. Cambia el registro DNS a la nueva IP; Caddy obtiene el certificado cuando el DNS ya apunta a él.

### Borrar ntfy del servidor

```bash
sudo systemctl disable --now ntfy caddy ntfy-report.timer
sudo apt-get purge -y ntfy caddy
sudo rm -rf /etc/ntfy /var/lib/ntfy /var/cache/ntfy /etc/caddy /etc/ntfy-report.env \
  /usr/local/bin/ntfy-report /etc/systemd/system/ntfy-report.*
```

Y borra el registro DNS ([capítulo 04](04-dns.md)).

`ntfy` `operacion` `mantenimiento` `backup`
