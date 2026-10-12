**04**

# API key and the `oci` CLI

[← Index](README.md)

---

### Why the CLI

- Everything becomes repeatable commands (and lives in this guide).
- It lets you **automatically retry** instance creation when there's no capacity, which is tedious from the web console.
- Oracle doesn't use a simple token: it uses an **API signing key** (RSA pair) tied to your user.

### 1. Generate the API key in the console

1. Profile icon (top right) → **My profile**.
2. Under *Resources* (bottom left) → **API keys** → **Add API key**.
3. **Generate API key pair** → **Download private key** (`.pem`) → **Add**.
4. Copy the **Configuration file preview** block:

```ini
[DEFAULT]
user=ocid1.user.oc1..<...>
fingerprint=aa:bb:cc:...
tenancy=ocid1.tenancy.oc1..<...>
region=sa-santiago-1
key_file=<path to your private keyfile>
```

### 2. Save the key and config

```bash
mkdir -p ~/.oci
mv ~/Downloads/<your-key>.pem ~/.oci/oci_api_key.pem

cat > ~/.oci/config <<'EOF'
[DEFAULT]
user=<USER_OCID>
fingerprint=<FINGERPRINT>
tenancy=<TENANCY_OCID>
region=sa-santiago-1
key_file=~/.oci/oci_api_key.pem
EOF

chmod 700 ~/.oci && chmod 600 ~/.oci/*
```

Check that the fingerprint matches the key:

```bash
openssl rsa -in ~/.oci/oci_api_key.pem -pubout -outform DER | openssl md5 -c
```

### 3. Install the CLI

```bash
uv tool install oci-cli      # or: pipx install oci-cli
oci --version
```

If it says `command not found`: run `uv tool update-shell` and open a new terminal.

### 4. Verify access (read-only)

```bash
T=$(awk -F= '/^tenancy=/{print $2}' ~/.oci/config)
oci iam region-subscription list --tenancy-id "$T" --output table
```

Expected output:

```
| is-home-region | region-key | region-name   | status |
| True           | SCL        | sa-santiago-1 | READY  |
```

> **Watch out:** `oci iam region-subscription list` without `--tenancy-id` fails with `Missing option(s) --tenancy-id`.

### 5. Check your quotas

```bash
oci iam availability-domain list --compartment-id "$T" --query 'data[].name'
for l in standard-a1-core-count standard-a1-memory-count; do
  oci limits value list --compartment-id "$T" --service-name compute --name "$l" \
    --query 'data[].{ad:"availability-domain",value:value}' --output table
done
```

### Security

- The key has **the power of your administrator user** over the entire account.
- Never paste it into a chat, repo, or ticket. Keep it only in `~/.oci/`.
- Revoke it under **API keys → Delete** if it leaks.
- To limit its scope: create a separate user with a policy restricted to the project's compartment.

### Common errors

| Error | Cause or fix |
| :-- | :-- |
| `NotAuthenticated` | Fingerprint, `user`, or `tenancy` copied incorrectly |
| Permissions warning | `oci setup repair-file-permissions --file ~/.oci/config` |
| `Missing option(s) --tenancy-id` | That command requires the tenancy explicitly |

`oci-cli` `api-key` `authentication`
