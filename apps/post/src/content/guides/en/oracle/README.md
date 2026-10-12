# Free-forever VM on Oracle Cloud (and how not to lose it)

> A complete guide to creating an Oracle Cloud **Always Free** virtual machine with a public IP from the CLI, keeping it running 24/7 at no cost, and preventing Oracle from **reclaiming it for being idle**.

**Cost:** USD 0 per month · **Time:** ~1 h the first time · **Level:** intermediate (Linux terminal, SSH)

---

## TL;DR

- **What you get:** an Ubuntu 24.04 VM with a public IP, firewall open on 22/80/443, and no expiration date.
- **Free shapes:** ARM `A1.Flex` (up to 2 OCPU and 12 GB) or AMD `E2.1.Micro` (1/8 OCPU, 1 GB). A1 is usually **out of capacity**; the Micro is almost always available.
- **The risk:** Oracle reclaims instances whose **95th percentile CPU** stays below 20% for 7 days (plus network and, on A1 only, memory).
- **The fix:** on A1, a small instance (used RAM exceeds 20%); on Micro, a lowest-priority **CPU keepalive**.
- **Monitoring:** the VM logs its CPU every minute, computes the p95 the same way Oracle does, and sends a report to a webhook every 45 min.

Works for any lightweight service: a bot, a small API, a notification server, a proxy, a cron job.

---

## Index

| # | Chapter | What it covers |
| :-- | :-- | :-- |
| 01 | [Why Oracle Cloud](01-por-que-oracle.md) | Comparison with Render, Hetzner, AWS, and when not to use it |
| 02 | [What the free tier includes](02-capa-gratuita.md) | Free Trial vs. Always Free, official figures, duration |
| 03 | [Account signup and region](03-alta-y-region.md) | The irreversible decision: the home region |
| 04 | [API key and the `oci` CLI](04-api-key-y-cli.md) | Doing everything from the terminal |
| 05 | [Networking: VCN, subnet, and firewall](05-red.md) | Network script with ports 22, 80, and 443 |
| 06 | [Creating the instance](06-instancia.md) | Script with retries for A1 and Micro as plan B |
| 07 | [First VM boot](07-primer-arranque.md) | SSH, swap, Oracle's `iptables`, updates |
| 08 | [Idle reclamation](08-reclamo-por-inactividad.md) | The exact rule and the keepalive |
| 09 | [Measuring CPU and status report](09-monitoreo.md) | p95 like Oracle, report every 45 min |
| 10 | [Operations and teardown](10-operacion-y-borrado.md) | Start, stop, back up, delete everything |
| 11 | [Migrating from Micro to A1](11-migrar-a-a1.md) | When ARM capacity shows up |
| 12 | [Problems and solutions](12-problemas-y-soluciones.md) | Everything that failed and how it was fixed |

---

## Conventions

- **Example values:** IP `203.0.113.10` (documentation range), region `sa-santiago-1`, project name `my-vm`. Replace them with your own.
- **Placeholders:** `<TENANCY_OCID>`, `<USER_OCID>`, `<FINGERPRINT>`. OCIDs are not secrets; the private API key is.
- **Terminal:** Linux or WSL2 with `bash`, `curl`, `jq`, and `uv` (or `pipx`).
- **Data as of:** October 2026. Each chapter links to the official source.

`oracle-cloud` `always-free` `oci-cli` `vm` `self-hosting`
