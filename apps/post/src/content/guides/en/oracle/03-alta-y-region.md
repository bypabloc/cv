**03**

# Account signup and home region

[← Index](README.md)

---

### Steps

1. Go to **https://signup.cloud.oracle.com/**.
2. Country, name, and email; verify the email.
3. Choose the **account name** (*cloud account name* or *tenancy*). You'll need it on every login.
4. Choose the **home region** (see below).
5. Verification card: a temporary charge is made and then reversed. Nothing is billed without an *Upgrade*.
6. Wait for provisioning. The screen says:
   > *We are creating your account; this process can take up to 15 minutes.*

   Two emails arrive: account created and account ready (*fully provisioned*). You can try signing in at **https://cloud.oracle.com/** before the second one.

### The home region: the irreversible decision

- It **cannot be changed** after signup.
- Always Free instances can **only** be created there.
- The form warns:
  > *Free accounts are not available in all commercial data regions. Availability of each region may change over time. Do not attempt to create multiple accounts to change regions.*
- Oracle **doesn't publish** which regions accept free accounts or the A1 capacity of each one. The real source is the form's selector.

### Regions close to South America

| Region | Identifier |
| :-- | :-- |
| Colombia Central (Bogotá) | `sa-bogota-1` |
| Chile Central (Santiago) | `sa-santiago-1` |
| Chile West (Valparaíso) | `sa-valparaiso-1` |
| Brazil East (São Paulo) | `sa-saopaulo-1` |
| Brazil Southeast (Vinhedo) | `sa-vinhedo-1` |
| Mexico Central (Querétaro) | `mx-queretaro-1` |
| Mexico Northeast (Monterrey) | `mx-monterrey-1` |
| US East (Ashburn) | `us-ashburn-1` |

Source: [Regions and Availability Domains](https://docs.oracle.com/en-us/iaas/Content/General/Concepts/regions.htm).

### How to choose

1. Check which ones appear in the selector: those that don't support free accounts are missing or show a warning.
2. Pick the one closest to your users.
3. Large regions (Ashburn, Phoenix, Frankfurt) have a reputation for being out of A1 capacity. This is anecdotal and unverifiable.

### Real case

- Home region: **Chile Central (Santiago)**, with a single availability domain (`AD-1`).
- No A1 capacity on signup day (12 attempts). See [chapter 06](06-instancia.md).

`oracle-cloud` `signup` `regions` `home-region`
