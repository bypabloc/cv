**03**

# Server requirements

[← Index](README.md)

---

### The machine

| Requirement | Minimum | Note |
| :-- | :-- | :-- |
| OS | Ubuntu 24.04 (amd64 or arm64) | The commands use `apt` and `systemd` |
| RAM | 1 GB | ntfy + Caddy use ~100 MB; add swap if you have 1 GB |
| CPU | Any | A fraction of a vCPU is plenty |
| Disk | ~2 GB free | Message cache and logs |
| Network | Static public IP | Must be on 24/7 |
| Access | SSH with a `sudo` user | The examples use the alias `mi-vm` |

Any provider works: Hetzner, DigitalOcean, AWS, a cloud free tier, a home server with a static IP.

Recommended SSH alias in `~/.ssh/config`:

```
Host mi-vm
  HostName 203.0.113.10
  User ubuntu
  IdentityFile ~/.ssh/mi_clave
```

### Ports

| Port | Purpose |
| :-- | :-- |
| 22 | SSH |
| 80 | Let's Encrypt validation (HTTP-01) and redirect to HTTPS |
| 443 | ntfy over HTTPS |

Open them in **every** layer your provider has:

1. The cloud firewall (Security Group, Security List, Hetzner Firewall…).
2. The firewall **inside** the VM. Some images ship `iptables` with a final `REJECT` that blocks everything except SSH; the install script handles it.

### Check before installing

```bash
ssh mi-vm 'lsb_release -ds; dpkg --print-architecture; free -m | sed -n 2p; sudo iptables -S INPUT'
```

If you see `-A INPUT -j REJECT` at the end, the install script opens 80 and 443 before that rule.

### Domain

- A subdomain (`ntfy.your-domain.com`) with access to create an `A` record ([chapter 04](04-dns.md)).
- The record must exist **before** installing Caddy.

`ntfy` `requirements` `vps` `firewall`
