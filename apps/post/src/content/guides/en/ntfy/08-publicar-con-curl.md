**08**

# Publish with curl

[← Index](README.md)

All examples use `$NTFY_TOKEN` (a `tk_...` token) and the topic `alertas`.

```bash
read -rsp 'ntfy token: ' NTFY_TOKEN; echo; export NTFY_TOKEN
```

---

### 1. Simple message

```bash
curl -H "Authorization: Bearer $NTFY_TOKEN" -d "Backup finished" https://ntfy.your-domain.com/alertas
```

### 2. Title, priority and emoji

```bash
curl -H "Authorization: Bearer $NTFY_TOKEN" \
     -H "Title: Deploy prod" -H "Priority: high" -H "Tags: rocket" \
     -d "Deploy to prod OK" https://ntfy.your-domain.com/alertas
```

- `Priority`: `min`, `low`, `default`, `high`, `urgent`.
- `Tags`: emoji names (`warning`, `white_check_mark`, `rotating_light`, `rocket`, `wave`).

### 3. Open a URL when tapped

```bash
curl -H "Authorization: Bearer $NTFY_TOKEN" \
     -H "Click: https://github.com/<user>/<repo>/actions" \
     -d "CI finished" https://ntfy.your-domain.com/alertas
```

### 4. User and password instead of a token

```bash
curl -u admin -d "Hello" https://ntfy.your-domain.com/alertas   # prompts for the password
```

### 5. Report a command's result

```bash
make test \
  && curl -H "Authorization: Bearer $NTFY_TOKEN" -H "Tags: white_check_mark" -d "Tests OK" https://ntfy.your-domain.com/alertas \
  || curl -H "Authorization: Bearer $NTFY_TOKEN" -H "Tags: rotating_light" -H "Priority: high" -d "Tests failed" https://ntfy.your-domain.com/alertas
```

### 6. Schedule an alert

```bash
curl -H "Authorization: Bearer $NTFY_TOKEN" -H "In: 30m" -d "Check the oven" https://ntfy.your-domain.com/alertas
```

Minimum 10 s, maximum 3 days.

### 7. Read recent messages

```bash
curl -s -H "Authorization: Bearer $NTFY_TOKEN" "https://ntfy.your-domain.com/alertas/json?poll=1&since=1h" | jq -r '.message'
```

### 8. Server health (no token)

```bash
curl https://ntfy.your-domain.com/v1/health      # {"healthy":true}
```

### 9. On ntfy.sh (no token)

```bash
curl -H "Title: Alert" -d "Hello" https://ntfy.sh/<random-topic>
```

### Response

A successful `POST` returns the message as JSON:

```json
{"id":"sMMIjkAXy6WU","time":1791754000,"event":"message","topic":"alertas","message":"Backup finished"}
```

| Code | Meaning |
| :-- | :-- |
| 200 | Published |
| 401 / 403 | No token, invalid token or no permission on the topic |
| 429 | Rate limit |

> Publishing to a topic nobody is subscribed to still works, but it reaches no one.

`ntfy` `curl` `cli`
