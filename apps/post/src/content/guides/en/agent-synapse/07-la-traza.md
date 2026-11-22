**07**

# The trace: who decided and why

[← Index](README.md)

---

### One step per line

Every hook run writes to a daily JSONL trace (`YYYY-MM-DD.jsonl`), grouped by `run` and with the agent's session id. Write and Edit content is never logged, and tokens are masked.

```bash
python3 <plugin>/scripts/synapse_log.py --since 30m          # 30m, 2h, 1d
python3 <plugin>/scripts/synapse_log.py --decision block     # allow | ask | block | pass
python3 <plugin>/scripts/synapse_log.py --session 49c43f62 --hook block_dangerous
python3 <plugin>/scripts/synapse_log.py --json | jq .        # raw JSONL
python3 <plugin>/scripts/synapse_log.py --follow             # live
python3 <plugin>/scripts/synapse.py log --host codex         # another agent's traces
```

### How to read it

```text
━━ 2026-10-02 09:00:56.720 ━━ block_dangerous ━━ run 29e84acc ━━ session 49c43f62
   tool    Bash
   cwd     ~/code/my-app
   engine  laya-daemon-gpu
   input   p=~; rm -rf "$p/other"
   ├─ regex.catastrophic         result=no_match  checked=21
   ├─ structure.outside_project  result=match  subcmd=rm -rf "$p/other"  target=~/other
   └─ DECISION  BLOCK  python · structure.outside_project  (7.6 ms)
      evidencia  {"subcmd": "rm -rf \"$p/other\"", "target": "~/other"}
```

- **engine:** which engine was available (rules only, Laya on GPU or on CPU).
- **Each step** shows the rule evaluated and its result.
- **DECISION** says who decided (`python` = a rule, `laya` = the classifier), with which rule, the time and the evidence.

### Debugging a false positive

1. Find it: `synapse_log.py --decision ask --since 1d` (or `block`).
2. Look at `decided_by` and `rule`: if a rule decided, the case goes to that rule; if Laya did, a deterministic rule is probably missing.
3. Pin it in a test case ([ch. 11](11-probar-y-operar.md)), **along with a similar value that must keep its decision**, so closing the false positive doesn't open a hole.

### Why attribution matters

Up to 1.2.0, a `block` or `ask` didn't say whether it came from a rule or the model, and debugging a false positive was guesswork. Since then a test requires **every** `block` or `ask` decision to name who made it. Without that, the trace is useless as a test bench.

### In my case

The trace is the source of almost every plugin version. The periodic review is always the same: filter the last few days' `ask`s and `block`s, separate the correct ones from false positives and turn each false positive into a case. In November, that review over weeks of use is what led to turning Laya off by default ([ch. 08](08-laya.md)).

`trace` `logs` `debugging`
