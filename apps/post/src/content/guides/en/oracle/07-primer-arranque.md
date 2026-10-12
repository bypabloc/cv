**07**

# First VM boot

[← Index](README.md)

---

### 1. First SSH

```bash
ssh -i ~/.ssh/oci_my_vm ubuntu@203.0.113.10
```

- For the first 1–2 minutes it responds with `Connection refused`: cloud-init is still starting up. Retry.
- The Ubuntu image user is `ubuntu` (with passwordless `sudo`).

Shortcut in `~/.ssh/config`:

```
Host my-vm
  HostName 203.0.113.10
  User ubuntu
  IdentityFile ~/.ssh/oci_my_vm
```

### 2. What the image ships with

On a freshly created Micro:

```
x86_64 · Ubuntu 24.04.5 LTS · 954 MB RAM (~400 MB used at boot) · no swap
-P INPUT ACCEPT
-A INPUT -m state --state RELATED,ESTABLISHED -j ACCEPT
-A INPUT -p icmp -j ACCEPT
-A INPUT -i lo -j ACCEPT
-A INPUT -p tcp -m state --state NEW -m tcp --dport 22 -j ACCEPT
-A INPUT -j REJECT --reject-with icmp-host-prohibited
```

The final `iptables` `REJECT` **blocks 80 and 443 even if the Security List allows them**. It's the most common mistake on Oracle.

### 3. Script: `vm-base.sh`

Swap, ports 80/443 in `iptables`, and automatic security patches. Idempotent.

```bash
#!/usr/bin/env bash
# Base setup for an Oracle Ubuntu 24.04 VM. Runs ON THE VM with sudo.
# Usage from your PC: ssh my-vm 'sudo bash -s' < vm-base.sh
set -euo pipefail
export DEBIAN_FRONTEND=noninteractive
PORTS="${PORTS:-80 443}"

# 1. 1 GB swap (the Micro has 1 GB RAM; apt and other processes can run out of memory)
if ! swapon --show | grep -q /swapfile; then
  fallocate -l 1G /swapfile && chmod 600 /swapfile && mkswap /swapfile && swapon /swapfile
  grep -q /swapfile /etc/fstab || echo '/swapfile none swap sw 0 0' >> /etc/fstab
fi

# 2. iptables: open the ports BEFORE the final REJECT (position 5) and persist
for p in $PORTS; do
  iptables -C INPUT -p tcp -m state --state NEW --dport "$p" -j ACCEPT 2>/dev/null \
    || iptables -I INPUT 5 -p tcp -m state --state NEW --dport "$p" -j ACCEPT
done
netfilter-persistent save

# 3. Automatic security patches
apt-get update -q
apt-get install -y -q unattended-upgrades

iptables -S INPUT
swapon --show
```

Usage:

```bash
ssh my-vm 'sudo bash -s' < vm-base.sh
ssh my-vm 'sudo env PORTS="80 443 8080" bash -s' < vm-base.sh   # other ports
```

> Every new port must also be opened in the Security List ([chapter 05](05-red.md)).

### 4. Check from outside

With any service listening on the port (for example `sudo python3 -m http.server 80`):

```bash
curl -I http://203.0.113.10
```

If it hangs: check the Security List and `iptables`. If it responds with `Connection refused`: the firewall is fine, but nothing is listening.

`oracle-cloud` `ssh` `iptables` `swap` `ubuntu`
