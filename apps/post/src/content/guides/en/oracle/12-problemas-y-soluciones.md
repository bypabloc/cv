**12**

# Problems and solutions

[← Index](README.md)

---

### Signup and CLI

| Problem | Cause | Solution |
| :-- | :-- | :-- |
| The region I want doesn't appear | It doesn't support free accounts or availability changed | Pick another one from the list; the region can't be changed later |
| `NotAuthenticated` | Fingerprint, `user`, or `tenancy` copied incorrectly in `~/.oci/config` | Recopy the *Configuration file preview* and verify the fingerprint with `openssl` |
| `Missing option(s) --tenancy-id` | `iam region-subscription list` requires the tenancy | `--tenancy-id "$(awk -F= '/^tenancy=/{print $2}' ~/.oci/config)"` |
| Config permissions warning | Files readable by others | `oci setup repair-file-permissions --file ~/.oci/config` |
| `oci: command not found` after installing | `uv` PATH not loaded | `uv tool update-shell` and open a new terminal |

### Networking and instance

| Problem | Cause | Solution |
| :-- | :-- | :-- |
| `NotAuthorizedOrNotFound` right after creating the compartment | Propagation | `sleep 20` before creating the VCN |
| "Out of host capacity" on A1 | No free ARM hosts for the free tier | Retry in a loop every 2 min or use Micro |
| Huge A1 quotas in `oci limits` | They come from the trial credit | Stick to the Always Free 2 OCPU / 12 GB |
| SSH `Connection refused` | cloud-init still starting up | Wait 1–2 min and retry |
| 80/443 don't respond even though the Security List allows them | The image's `iptables` with a final `REJECT` | Insert the `ACCEPT` before the `REJECT` and run `netfilter-persistent save` |
| `apt` dies from lack of memory on the Micro | 1 GB without swap | 1 GB swap (chapter 07) |

### Reclamation and monitoring

| Problem | Cause | Solution |
| :-- | :-- | :-- |
| A report says "CPU 0%" | Snapshot of an instant | Look at the **7-day p95** |
| On Micro, high RAM doesn't protect you | The memory rule only applies to A1 | CPU keepalive |
| "Every 45 min" with cron fires at :00 and :45 | `*/45` isn't a real interval | systemd timer with `OnUnitActiveSec=45min` |
| A cron line with `%` gets cut off | `%` is special in crontab | Escape it as `\%` |
| A downed VM doesn't alert | It can't report if it's dead | The **absence** of a report for more than 45 min is the alarm |
| Instance reclaimed | CPU p95 (and network; on A1, memory too) below 20% for 7 days | Recreate it with the scripts; new IP → update DNS |

`troubleshooting` `oracle-cloud`
