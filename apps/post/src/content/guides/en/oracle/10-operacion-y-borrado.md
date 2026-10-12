**10**

# Operations and teardown

[← Index](README.md)

---

### Instance state

```bash
oci compute instance get --instance-id "$I" --query 'data."lifecycle-state"' --raw-output   # RUNNING
oci compute instance list -c "$C" --query 'data[].{n:"display-name",s:"lifecycle-state",forma:shape}' --output table
```

### Start, stop, restart

```bash
oci compute instance action --instance-id "$I" --action SOFTRESET   # graceful restart
oci compute instance action --instance-id "$I" --action STOP
oci compute instance action --instance-id "$I" --action START
```

> A **stopped** instance uses no CPU and counts as idle for reclamation.

### Updates

- `unattended-upgrades` installs security patches on its own.
- If the report says "reboot required":

```bash
ssh my-vm 'sudo apt-get update && sudo apt-get -y upgrade && sudo reboot'
```

Everything `enable`d in systemd (services, the report timer) and the cron jobs start automatically.

### Backups

The VM can be reclaimed. Back up elsewhere:

- **Install scripts:** in a repo; they rebuild the server in minutes.
- **Data and configuration:** whatever your service stores, plus `/etc/cron.d/oci-keepalive` and `/etc/vm-report.env`.

```bash
ssh my-vm 'sudo tar czf - /etc/cron.d /etc/vm-report.env /path/to/your/data' > respaldo-$(date +%F).tgz
```

Oracle also lets you back up the boot volume (5 free backups):

```bash
BV=$(oci compute boot-volume-attachment list -c "$C" --availability-domain "$AD" --instance-id "$I" \
  --query 'data[0]."boot-volume-id"' --raw-output)
oci bv boot-volume-backup create --boot-volume-id "$BV" --display-name "my-vm-$(date +%F)"
```

### Get the public IP

```bash
oci compute instance list-vnics --instance-id "$I" --query 'data[0]."public-ip"' --raw-output
```

### Delete everything

Order: dependent resources first.

```bash
oci compute instance terminate --instance-id "$I" --preserve-boot-volume false --force --wait-for-state TERMINATED
oci network subnet delete --subnet-id "$SN" --force --wait-for-state TERMINATED
oci network route-table update --rt-id "$RT" --route-rules '[]' --force
oci network internet-gateway delete --ig-id "$IG" --force --wait-for-state TERMINATED
oci network vcn delete --vcn-id "$V" --force --wait-for-state TERMINATED
oci iam compartment delete --compartment-id "$C" --force     # may take several minutes
```

Also:

- Delete the DNS records that pointed to the IP.
- Revoke the API key in the console (**My profile → API keys → Delete**) if you won't use it anymore.
- Delete the local SSH key: `rm -f ~/.ssh/oci_my_vm ~/.ssh/oci_my_vm.pub`.

`oracle-cloud` `operations` `backup` `teardown`
