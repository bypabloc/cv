**01**

# What ntfy is and when to run your own

[← Index](README.md)

---

### In one line

- An **HTTP pub/sub server**: you publish with a `POST` to `https://<server>/<topic>` and every device subscribed to that topic gets a push notification.
- Open source (Apache 2.0 / GPLv2), written in Go, a single binary.
- **ntfy.sh** is the author's public instance; anyone can install their own.

### How the message reaches the phone

```mermaid
flowchart LR
    S["Script / PC\n(curl POST)"] -->|HTTPS + token| N["Your ntfy server\nntfy.your-domain.com"]
    N -->|persistent connection\n(instant delivery)| A["Android app"]
    N -->|"content-free poke"| R["ntfy.sh (relay)"]
    R -->|APNs| I["iOS app"]
```

| Piece | How it works |
| :-- | :-- |
| Publish | `POST`/`PUT` to `/<topic>`. The topic is created on first use |
| Android | The app keeps an open connection (WebSocket or JSON stream) to your server |
| iOS | Apple only allows push from whoever signed the app: your server notifies ntfy.sh (`upstream-base-url`), which wakes the app via APNs; the app then fetches the content from your server |
| Storage | SQLite with a short cache (24 h here); it is not a persistent queue |

### Concepts

| Concept | What it is |
| :-- | :-- |
| **Topic** | A channel. Without authentication, its name acts as the password |
| **User** | An account with read/write permissions per topic |
| **Token** | A user's `tk_...` credential, ideal for scripts; revocable independently |
| **Priority** | `min` to `urgent`; `urgent` rings even when the phone is on silent |
| **Tags** | Emojis by name (`warning`, `rocket`) shown in the notification |

### Options

| Option | Cost | Private | Maintenance | When |
| :-- | :-- | :-- | :-- | :-- |
| Free ntfy.sh | USD 0 | No: anyone who guesses the topic can read it | None | Personal alerts with no sensitive data |
| ntfy.sh Supporter | USD 5 (billing period: see [ch. 02](02-ntfy-sh-limites.md)) | Yes (3 reserved topics) | None | Privacy without running a server |
| **Self-hosted server** | The VM's cost | Yes | Medium | Full control, your own domain, your own limits |

### What running your own server means

| You gain | You take on |
| :-- | :-- |
| Private topics with user and token | Patches, certificates and monitoring |
| No 250-messages-per-day limit | If the server goes down, no alerts (that is why ntfy.sh stays as a fallback) |
| Your domain | A VM that is always on with a public IP |

`ntfy` `push-notifications` `pub-sub` `alternatives`
