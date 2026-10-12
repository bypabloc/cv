**08**

# Idle reclamation: the rule and how to avoid it

[← Index](README.md)

---

### The official rule

Exact text from [Always Free Resources](https://docs.oracle.com/en-us/iaas/Content/FreeTier/freetier_topic-Always_Free_Resources.htm):

> Oracle will deem virtual machine and bare metal compute instances as idle if, during a 7-day period, the following are true:
> - CPU utilization for the 95th percentile is less than 20%
> - Network utilization is less than 20%
> - Memory utilization is less than 20% *(applies to A1 shapes only)*

> Idle Always Free compute instances may be reclaimed by Oracle.

### How to read it

- The conditions are **joined by "and"**: the instance is idle only if **all** of them are true. **It's enough for one to exceed 20%** for it not to be.
- **7-day 95th percentile:** all of the week's measurements are sorted and the one with 95% below it is taken. If CPU exceeds 20% for a bit more than **5% of the time**, the p95 is above 20%.
- **Memory only counts on A1.** On the Micro, only CPU and network count.
- A lightweight service (a bot, a webhook, a notification server) barely uses CPU or network: **it's idle by definition**.
- The documentation **doesn't say** whether or how it warns before reclaiming.
- Forums recommend upgrading the account to *Pay As You Go*, but the documentation **doesn't** say it exempts you from reclamation.
- A **stopped** instance doesn't use CPU either: don't leave it off for days.

### Strategies

| Strategy | Applies to | How | Assessment |
| :-- | :-- | :-- | :-- |
| **Small instance** | A1 | 1 OCPU and 1 GB: normal usage (~400 MB) exceeds 20% of RAM | Clean, no artificial load. **The best** |
| **CPU keepalive** | Micro (and A1 if desired) | Cron job that uses CPU for a few seconds every few minutes | Works; it's artificial load (gray area under the terms) |
| Network traffic | Both | Generate sustained traffic | Wastes bandwidth; discarded |

### The keepalive (Micro)

```bash
ssh my-vm "echo \"*/10 * * * * root timeout 75 nice -n 19 sh -c 'cat /dev/urandom | sha256sum >/dev/null' 2>/dev/null || true\" | sudo tee /etc/cron.d/oci-keepalive"
```

Contents of `/etc/cron.d/oci-keepalive`:

```cron
*/10 * * * * root timeout 75 nice -n 19 sh -c 'cat /dev/urandom | sha256sum >/dev/null' 2>/dev/null || true
```

| Part | Why |
| :-- | :-- |
| `*/10` | Every 10 minutes |
| `timeout 75` | 75 s of load ≈ 12.5% of the time, more than the 5% the p95 needs; it never keeps running |
| `nice -n 19` | Lowest priority: your services always get the CPU first |
| `sha256sum` of `/dev/urandom` | Uses CPU without touching disk or network |

### Evidence

Maximum CPU per minute according to Oracle Monitoring (UTC):

```
21:11  50%   21:12  88%   ← keepalive
21:13   0%  …  21:20   0%
21:21  56%   21:22  47%   ← keepalive
```

**95th percentile for the last hour: 49.9%** according to Oracle and **49%** according to the VM's local log. Well above 20%.

### Don't be fooled by "0%"

Seeing **CPU 0%** at a given moment doesn't mean risk: it's a snapshot of an instant without the keepalive. What matters is the **7-day p95**. [Chapter 09](09-monitoreo.md) measures and reports it.

### If it gets reclaimed

- The public IP changes when you recreate the instance: update your DNS.
- Whatever was on the disk is lost: keep your install scripts and backups elsewhere ([chapter 10](10-operacion-y-borrado.md)).
- The status report stops arriving: **the missing report is the alarm**.

`oracle-cloud` `always-free` `idle-reclamation` `keepalive` `p95`
