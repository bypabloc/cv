**05**

# Secrets and .env files

[← Index](README.md)

---

### Reading a .env without dumping it

`block_env_read` blocks reading `.env` files with the read tool and with commands like `cat`, `head`, `tail`, `awk`, `strings` or inline `python`/`node`. Instead of the content, the agent gets a schema with each value's type and length:

```text
DATABASE_URL=<URL, 35 caracteres>
API_KEY=<alfanumerico, 32 caracteres>
```

With that it knows which variables exist without any value entering the context or the transcript. Templates (`.env.example`, `.env.sample`) are read normally, and `source .env` is allowed: it loads the values into the process without printing them.

### Not writing credentials

`detect_secrets` checks the content of every Edit and Write before it reaches disk:

| Blocks | Lets through |
| :-- | :-- |
| RSA, SSH and PGP private keys | Placeholders: `your-api-key`, `REPLACE_ME` |
| OpenAI, Anthropic, Google, AWS, Stripe, GitHub and Slack tokens | Environment reads: `process.env.X`, `os.getenv('X')` |
| Plain-text passwords | Function calls that look like assignments |

Test fragments that look like real secrets (for example, for the plugin's own tests) are written with markers that the test bench expands, so they don't trip GitHub's push protection.

### One exact per-project exception

The password signature sometimes clashes with known, non-secret values in a project (a word like `required` in a schema). For those cases there's a per-project list in `.synapse/secrets.json` (falling back to `.claude/synapse-secrets.json`):

```json
{ "password_rule_values": ["required"] }
```

The exception is strict on purpose:

- It only passes if **every** captured value matches a list element exactly (case-sensitive).
- A similar value, or an allowed one mixed with a real one, is still blocked.
- If the file is missing or invalid, it blocks.
- Any identical literal passes in that project, even if it were a real credential: use it only with values you know are public.

### What Synapse doesn't replace

Synapse keeps the agent from reading or writing secrets by accident. It doesn't replace a secrets policy: real values stay out of the repo, in a manager or in ignored files, and the agent uses them without seeing them (for example, extracting a single variable in the same command that consumes it).

### In my case

In my projects the rule is that no `.env` value enters the conversation. Before Synapse that depended on the agent remembering it; now, if it tries, it gets the schema and works with that. The per-project exception arrived in 1.5.0, when the password signature kept blocking known values in a project that had nothing secret about them, with no way to allow them.

`secrets` `env` `detect_secrets`
