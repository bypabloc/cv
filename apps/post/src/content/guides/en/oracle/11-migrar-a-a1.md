**11**

# Migrating from Micro to A1

[← Index](README.md)

---

### Why migrate

- A1 with 1 GB avoids reclamation **without artificial load**: used memory already exceeds 20%.
- More CPU and RAM (up to 2 OCPU and 12 GB free).
- The keepalive goes away.

### Step 1: get capacity

Leave the script from [chapter 06](06-instancia.md) retrying in the background:

```bash
NAME=my-vm-a1 nohup bash oci-crear-instancia.sh a1 > instancia-a1.env 2> intentos-a1.log &
```

Once you get it: `eval "$(cat instancia-a1.env)"` sets `I` and `IP` for the new instance.

### Step 2: prepare the A1

```bash
ssh -i ~/.ssh/oci_my_vm ubuntu@$IP 'sudo bash -s' < vm-base.sh       # chapter 07
```

- The architecture is `arm64`: install your service with ARM packages or images.
- **Don't** install the keepalive.

### Step 3: copy data

```bash
ssh my-vm 'sudo tar czf - /path/to/your/data' | ssh -i ~/.ssh/oci_my_vm ubuntu@$IP 'sudo tar xzf - -C /'
```

### Step 4: status report

Install it as in [chapter 09](09-monitoreo.md). On A1 the relevant check is **memory**: replace the CPU p95 line with:

```bash
[ "$mem_pct" -ge 20 ] || fails+=("RAM ${mem_pct}% (Oracle could reclaim it)")
```

### Step 5: update DNS

Point the `A` records to the new IP. With a 300 s TTL it propagates in ~5 min.

### Step 6: delete the Micro

```bash
oci compute instance terminate --instance-id "$I_MICRO" --preserve-boot-volume false --force
```

Estimated total time: ~15 minutes once capacity is available.

`oracle-cloud` `a1-flex` `migration` `arm64`
