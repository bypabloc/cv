**02**

# What the free tier includes

[← Index](README.md)

Source: [Always Free Resources](https://docs.oracle.com/en-us/iaas/Content/FreeTier/freetier_topic-Always_Free_Resources.htm) (accessed October 2026).

---

### Free Trial vs. Always Free

After creating the account, the console shows:

> *Free Tier account · You are in a Free Trial. When your trial is over, your account is limited to Always Free resources.*

| | Free Trial | Always Free |
| :-- | :-- | :-- |
| What it is | **USD 300** credit for any service | Free resources with no expiration date |
| Duration | Usually 30 days (the official page doesn't specify; check your console) | Indefinite, as long as the account exists and the resource isn't reclaimed |
| When it ends | Anything not Always Free is stopped and later deleted | Keeps running |
| Charges | None, unless you *Upgrade* to Pay As You Go | None |

**Rule of thumb:** only create resources labeled **Always Free-eligible**. Everything else disappears when the trial ends.

### Compute

| Shape | Free quantity | CPU | RAM | Network |
| :-- | :-- | :-- | :-- | :-- |
| `VM.Standard.E2.1.Micro` (AMD x86) | Up to **2** instances | 1/8 OCPU (burstable) | **1 GB** | Up to 50 Mbps to the internet |
| `VM.Standard.A1.Flex` (Ampere ARM) | **1,500 OCPU hours + 9,000 GB hours per month** | Equivalent to **2 OCPU** | Equivalent to **12 GB** | Depends on the shape |

- A1 can be used as one 2 OCPU/12 GB instance or as two 1 OCPU instances.
- Always Free instances **can only be created in the home region**.
- During the trial, `oci limits` shows much larger quotas (for example 41 OCPU and 277 GB of A1). Those come from the credit, not Always Free.

### Storage and networking

| Resource | Free |
| :-- | :-- |
| Block Volume (boot + data) | **200 GB** total, home region only |
| Boot volume | Minimum ~47–50 GB per instance (the page is inconsistent) |
| Volume backups | 5 total |
| Object Storage | 20 GB and 50,000 requests per month |
| Outbound traffic | **10 TB per month** |
| VCN | Up to 2 |
| Load Balancer | 1 flexible 10 Mbps + 1 Network Load Balancer |

### Other services

| Service | Free |
| :-- | :-- |
| Monitoring | 500 million datapoints ingested, 1 billion retrieved |
| Notifications | 1 million HTTPS and 1,000 emails per month |
| Email Delivery | 3,000 emails per month |
| Autonomous Database | 2 databases with 1 OCPU and 20 GB |
| Vault | 20 HSM key versions, 150 secrets |

### How long it lasts

- **The account and Always Free resources:** no stated expiration.
- **A specific instance:** as long as it isn't reclaimed for being idle ([chapter 08](08-reclamo-por-inactividad.md)) and you don't delete it.
- **The trial credit:** ~30 days.

`oracle-cloud` `always-free` `free-trial` `limits`
