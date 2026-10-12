**07**

# Set up the phone app

[← Index](README.md)

---

### Install

- **Android:** "ntfy" on Google Play or F-Droid.
- **iOS:** "ntfy" on the App Store.

### 1. Add your user for the self-hosted server

⋮ → **Settings** → **Users** (*General* section) → **Add user**:

| Field | Value |
| :-- | :-- |
| Service URL | `https://ntfy.your-domain.com` |
| Username | `admin` (or a read-only user) |
| Password | The one you set during installation |

### 2. Subscribe to the topic

Main screen → **+**:

| Field | Value |
| :-- | :-- |
| Topic | `alertas` (**just the name**, no URL or slashes) |
| Use another server | On → `https://ntfy.your-domain.com` |
| Instant delivery (Android) | On: persistent connection, alerts with no delay |

When you subscribe you will see the messages from the last 24 h (the server cache).

### 3. Fallback on ntfy.sh

Repeat step 2 with your random ntfy.sh topic and **without** enabling "Use another server". If your server goes down, the failure alert arrives through there.

### The most common error: a topic with `/`

Symptom in the subscription list:

```
ntfy.sh/<random-topic>/Alertas
0 notificaciones, reconectando...  ⚠
```

- The full URL plus a name was typed into the **Topic** field.
- A topic **cannot contain `/`**: the app keeps reconnecting forever and receives nothing.
- Fix: delete the subscription and create it with **only** the topic name.

### If notifications do not arrive

| Symptom | Fix |
| :-- | :-- |
| "reconnecting…" with ⚠ | Misspelled topic or server down (`curl https://ntfy.your-domain.com/v1/health`) |
| They show up in the app but do not ring | Android Settings → Apps → ntfy → Notifications allowed |
| They arrive late with the screen off | Settings → Battery → ntfy → **Unrestricted** |
| iOS does not receive from the self-hosted server | Check `upstream-base-url: "https://ntfy.sh"` in `server.yml` |
| 401/403 when subscribing | User not added for that URL or no read permission on the topic |

### Priorities on the phone

- `min`/`low`: arrives silently (the "OK" report uses `low`).
- `high`: rings and vibrates (the "FAILURE" report uses `high`).
- `urgent`: rings even on silent.

`ntfy` `android` `ios` `troubleshooting`
