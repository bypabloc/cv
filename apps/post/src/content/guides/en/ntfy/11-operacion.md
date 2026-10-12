**11**

# Operations

[← Index](README.md)

Commands on the server (`ssh mi-vm`).

---

### Status and logs

```bash
systemctl status ntfy caddy --no-pager
journalctl -u ntfy -n 50 --no-pager
journalctl -u caddy -n 50 --no-pager       # certificates, proxy errors
curl -s http://127.0.0.1:2586/v1/health     # ntfy directly, without Caddy
```

### Change the admin password

```bash
sudo ntfy user change-pass admin
```

Update it in the phone app as well.

### Rotate tokens

```bash
sudo ntfy token add --label mi-pc admin        # new
sudo ntfy token list admin
sudo ntfy token remove admin tk_viejo          # revoke
```

For the report token: edit `NTFY_TOKEN` in `/etc/ntfy-report.env` with `sudoedit`.

### Change the configuration

```bash
sudoedit /etc/ntfy/server.yml && sudo systemctl restart ntfy
sudoedit /etc/caddy/Caddyfile && sudo systemctl reload caddy
```

### Update

```bash
sudo apt-get update && sudo apt-get install --only-upgrade ntfy caddy
```

`unattended-upgrades` covers the system's security patches; ntfy and Caddy come from external repositories and are worth checking now and then. If the report says "reboot required": `sudo reboot` (everything starts on its own).

### Backup

| File | Contents |
| :-- | :-- |
| `/var/lib/ntfy/user.db` | Users and tokens |
| `/etc/ntfy/server.yml` | ntfy configuration |
| `/etc/caddy/Caddyfile` | Proxy and TLS |
| `/etc/ntfy-report.env` | Report token (secret) |

```bash
ssh mi-vm 'sudo tar czf - /var/lib/ntfy/user.db /etc/ntfy /etc/caddy/Caddyfile' > ntfy-respaldo-$(date +%F).tgz
```

The message cache (24 h) does not need a backup.

### Move to another server

1. Run `setup-ntfy.sh` on the new one ([chapter 05](05-instalacion.md)).
2. Copy `user.db` (existing tokens keep working):

```bash
ssh mi-vm 'sudo cat /var/lib/ntfy/user.db' | ssh nuevo-vm \
  'sudo systemctl stop ntfy && sudo tee /var/lib/ntfy/user.db >/dev/null && sudo chown ntfy:ntfy /var/lib/ntfy/user.db && sudo systemctl start ntfy'
```

3. Point the DNS record to the new IP; Caddy obtains the certificate once DNS points to it.

### Remove ntfy from the server

```bash
sudo systemctl disable --now ntfy caddy ntfy-report.timer
sudo apt-get purge -y ntfy caddy
sudo rm -rf /etc/ntfy /var/lib/ntfy /var/cache/ntfy /etc/caddy /etc/ntfy-report.env \
  /usr/local/bin/ntfy-report /etc/systemd/system/ntfy-report.*
```

And delete the DNS record ([chapter 04](04-dns.md)).

`ntfy` `operations` `maintenance` `backup`
