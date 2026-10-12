**06**

# Users, permissions and tokens

[← Index](README.md)

All commands run **on the server** with `sudo`.

---

### Model

- `auth-default-access: deny-all`: without a user or token, nobody can read or publish.
- One **admin** user with full access.
- **One token per publishing system** (your PC, the server report, a CI…): if one leaks, you revoke only that one.

### Users

```bash
sudo ntfy user list
sudo ntfy user add --role=admin admin        # prompts for the password (or takes it from NTFY_PASSWORD)
sudo ntfy user add lector                    # regular user
sudo ntfy user change-pass admin
sudo ntfy user del lector
```

### Per-topic permissions (non-admin users)

```bash
sudo ntfy access lector alertas read-only    # read only
sudo ntfy access ci deploys write-only       # publish only
sudo ntfy access lector 'proyecto-*' rw      # wildcards
sudo ntfy access                             # show all
sudo ntfy access --reset lector alertas      # remove
```

### Tokens

```bash
sudo ntfy token add --label mi-pc admin            # prints tk_...
sudo ntfy token add --label ci --expires=90d admin
sudo ntfy token list admin
sudo ntfy token remove admin tk_xxxxxxxx
```

Tokens used in this guide:

| Token | Where it lives | Purpose |
| :-- | :-- | :-- |
| `mi-pc` | Environment variable on your PC | Alerts from scripts and Claude Code ([chapter 09](09-claude-code.md)) |
| `server-report` | `/etc/ntfy-report.env` on the server (root, `600`) | Status report ([chapter 10](10-reporte-de-estado.md)) |

### Ways to authenticate when publishing

| Method | Example | When |
| :-- | :-- | :-- |
| Token (recommended) | `-H "Authorization: Bearer tk_..."` | Scripts and servers |
| User and password | `-u admin` (prompts for the password) | Manual tests; the phone app |
| In the URL | `?auth=<base64>` | Only when headers are not possible; it ends up in logs |

### Good practices

- Never paste a token into a repo, chat or ticket.
- Revoke and recreate any exposed token.
- Use `--expires` for temporary tokens.

`ntfy` `auth` `tokens` `acl`
