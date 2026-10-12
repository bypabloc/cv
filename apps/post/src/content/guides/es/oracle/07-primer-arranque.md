**07**

# Primer arranque de la VM

[← Índice](README.md)

---

### 1. Primer SSH

```bash
ssh -i ~/.ssh/oci_mi_vm ubuntu@203.0.113.10
```

- Los primeros 1–2 minutos responde `Connection refused`: cloud-init aún está arrancando. Reintenta.
- El usuario de la imagen Ubuntu es `ubuntu` (con `sudo` sin contraseña).

Atajo en `~/.ssh/config`:

```
Host mi-vm
  HostName 203.0.113.10
  User ubuntu
  IdentityFile ~/.ssh/oci_mi_vm
```

### 2. Lo que trae la imagen

En una Micro recién creada:

```
x86_64 · Ubuntu 24.04.5 LTS · 954 MB de RAM (~400 MB usados al arrancar) · sin swap
-P INPUT ACCEPT
-A INPUT -m state --state RELATED,ESTABLISHED -j ACCEPT
-A INPUT -p icmp -j ACCEPT
-A INPUT -i lo -j ACCEPT
-A INPUT -p tcp -m state --state NEW -m tcp --dport 22 -j ACCEPT
-A INPUT -j REJECT --reject-with icmp-host-prohibited
```

El `REJECT` final de `iptables` **bloquea 80 y 443 aunque la Security List los permita**. Es el error más común en Oracle.

### 3. Script: `vm-base.sh`

Swap, puertos 80/443 en `iptables` y parches de seguridad automáticos. Idempotente.

```bash
#!/usr/bin/env bash
# Preparación base de una VM Ubuntu 24.04 de Oracle. Se ejecuta EN LA VM con sudo.
# Uso desde tu PC: ssh mi-vm 'sudo bash -s' < vm-base.sh
set -euo pipefail
export DEBIAN_FRONTEND=noninteractive
PORTS="${PORTS:-80 443}"

# 1. Swap de 1 GB (la Micro tiene 1 GB de RAM; apt y otros procesos pueden quedarse sin memoria)
if ! swapon --show | grep -q /swapfile; then
  fallocate -l 1G /swapfile && chmod 600 /swapfile && mkswap /swapfile && swapon /swapfile
  grep -q /swapfile /etc/fstab || echo '/swapfile none swap sw 0 0' >> /etc/fstab
fi

# 2. iptables: abrir los puertos ANTES del REJECT final (posición 5) y persistir
for p in $PORTS; do
  iptables -C INPUT -p tcp -m state --state NEW --dport "$p" -j ACCEPT 2>/dev/null \
    || iptables -I INPUT 5 -p tcp -m state --state NEW --dport "$p" -j ACCEPT
done
netfilter-persistent save

# 3. Parches de seguridad automáticos
apt-get update -q
apt-get install -y -q unattended-upgrades

iptables -S INPUT
swapon --show
```

Uso:

```bash
ssh mi-vm 'sudo bash -s' < vm-base.sh
ssh mi-vm 'sudo env PORTS="80 443 8080" bash -s' < vm-base.sh   # otros puertos
```

> Cada puerto nuevo también debe abrirse en la Security List ([capítulo 05](05-red.md)).

### 4. Comprobar desde afuera

Con cualquier servicio escuchando en el puerto (por ejemplo `sudo python3 -m http.server 80`):

```bash
curl -I http://203.0.113.10
```

Si se queda colgado: revisa la Security List y `iptables`. Si responde `Connection refused`: el firewall está bien, pero no hay nada escuchando.

`oracle-cloud` `ssh` `iptables` `swap` `ubuntu`
