**02**

# Free ntfy.sh and its limits

[← Index](README.md)

Sources: [docs.ntfy.sh/publish, Limitations section](https://docs.ntfy.sh/publish/) and [ntfy.sh/#pricing](https://ntfy.sh/#pricing) (October 2026).

---

### Free limits (per IP, no account)

| Limit | ntfy.sh |
| :-- | :-- |
| Messages per day | **250** |
| Burst | 60 requests in a row, then 1 every 5 s |
| Message size | 4,096 bytes (title 1 KB, tags 512 bytes) |
| Attachments | 2 MB each, 20 MB total, deleted after 3 h |
| Emails | 5 per day |
| Subscription connections | 30 |
| Traffic | 200 MB per day |
| Message cache | ~12 h |
| Reserved topics | None |

### Paid plans

| Plan | USD | Messages/day | Reserved topics | Attachments |
| :-- | :-- | :-- | :-- | :-- |
| Supporter | 5 | 2,500 | 3 | 25 MB |
| Pro | 10 | 20,000 | 10 | 250 MB |
| Business | 20 | 50,000 | 50 | 1 GB |

The page does not say whether the price is monthly or yearly.

### Using it well

- A **long, random** topic name (it acts as a password):

```bash
echo "avisos-$(head -c 12 /dev/urandom | od -An -tx1 | tr -d ' \n')"
```

- Never send sensitive data: anyone who knows the name can read everything.

### ntfy.sh's role alongside a self-hosted server

- **Fallback**: the status report also publishes there; if your server goes down, the failure alert still arrives.
- **iOS relay**: required even if you have your own server.

`ntfy` `ntfy-sh` `limits` `pricing`
