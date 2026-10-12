**01**

# Why Oracle Cloud

[← Index](README.md)

---

### The problem

- Many small services need a machine that is **always on** with a **public IP**: a bot, a webhook, a notification server, an internal API.
- Free PaaS tiers "sleep" the service when it gets no traffic.
- AWS and GCP free tiers expire or charge for the IPv4 address.

### What Oracle Always Free offers

- A free VM **with no expiration date** (not a 12-month trial).
- Public IP included and **10 TB** of outbound traffic per month.
- Up to 2 AMD Micro VMs (1 GB) or the equivalent of 2 OCPU and 12 GB on ARM.
- It doesn't shut down for lack of traffic: it stays on 24/7.

### Comparison

Approximate prices as of October 2026.

| Option | Monthly cost | Always on | Persistent disk | Drawback |
| :-- | :-- | :-- | :-- | :-- |
| **Oracle Always Free** | **USD 0** | Yes | Yes (up to 200 GB) | Idle reclamation; clunky signup; A1 out of capacity |
| Render Free | USD 0 | **No**: sleeps after 15 min without traffic | **No** | ~1 min cold start; 750 h/month; arbitrary restarts |
| Hetzner (smallest VPS) | ~EUR 4–5 | Yes | Yes | It's paid |
| AWS `t4g.nano` | ~USD 3 + ~USD 3.6 for the IPv4 | Yes | Yes | ~USD 7 for a minimal machine |
| Your own PC | USD 0 | Only while it's on | Yes | No fixed public IP; depends on your hardware |

### Render Free in detail

Source: [render.com/docs/free](https://render.com/docs/free).

- Spins down after **15 min** without inbound traffic and takes **~1 min** to come back: the first request fails or waits.
- **750 h** per month per workspace: a 24/7 service uses 744 h in a 31-day month, so only one fits.
- **No persistent disk**: anything local is lost on every restart or redeploy.
- It may restart free services at any time.

Good for demos; not for something that must always respond.

### When NOT to use Oracle Always Free

- **Production with customers:** Oracle can reclaim the instance and documents no advance notice.
- **Data without backups:** the VM can disappear.
- **If you don't want to manage a server:** patches, firewall, and monitoring are your responsibility.

`oracle-cloud` `always-free` `comparison` `render` `hetzner` `aws`
