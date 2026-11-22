**08**

# Laya: a classifier that can only ask

[← Index](README.md)

---

### What it is

[Laya](https://github.com/convaiinnovations/laya) is a lightweight classification model (a "System 1": it decides fast, without generating text). Synapse uses it for what rules can't settle: an ambiguous command, a line that might be a secret. It runs locally, on GPU if CUDA is available or on CPU, with no calls to any API.

Two design rules bound it:

1. **Laya never blocks:** at most it escalates to `ask`. A classifier with false positives can't have the last word.
2. **It only sees what's ambiguous:** anything a rule can decide is decided first, by rules.

### How it was tuned

| Version | Change | Measured result |
| :-- | :-- | :-- |
| 1.0.0 | Zero-shot Laya on the command text | 3.8 % FPR on real commands; 5.7 % recall on ShellRisk-Bench risky ones **[measured]** |
| 1.1.0 | Binary question over an **evidence summary** (what it deletes, writes, reads or sends), tuned delta and calibration | 0.29 % FPR, 78 % recall **[measured]** |
| 1.2.0 | Persistent daemon on a Unix socket and a deterministic gate before the model | From ~6 s to ~70 ms per hook; 0.15 % FPR, 81.35 % recall, 28 % fewer queries **[measured]** |

The lesson from 1.1.0: give the classifier structured evidence, not raw text. If the model gives a high score on neutral evidence, it's reacting to vocabulary, and that's fixed with a rule, not by raising the threshold.

### Why it ships off

In one project's real trace, between October and November 2026 **[measured]**:

| Measurement | Value |
| :-- | :-- |
| Laya queries in `block_dangerous` | ~20 thousand |
| Cost per command | ~205 ms with Laya, ~8 ms with rules only |
| Confirmations requested by Laya | 24 |
| Of those, false positives | **24** (`bun run typecheck`, `git worktree list`, `pdfinfo`, …) |

Everything dangerous in that period was stopped by deterministic rules. So in 1.6.0 Laya became off by default, and its false positives turned into routine rules. The delta was also retrained on that trace, but not published: recall dropped from 0.772 to 0.757, and a model that loses recall doesn't ship.

### When to turn it on

It makes sense if you work with unusual commands the rules don't cover, or if you want a second opinion in the secret hooks. It's turned on from the `env` of the agent's configuration:

```jsonc
{ "env": { "SYNAPSE_LAYA": "on" } }                     // every hook
{ "env": { "SYNAPSE_LAYA_HOOKS": "block_dangerous" } }  // only that hook
{ "env": { "SYNAPSE_LAYA": "off" } }                    // off even with a list
```

Requirements: the model delta (~100 MB, via Git LFS), PyTorch and, for speed, a CUDA GPU. The daemon starts on the first query and shuts down after 20 idle minutes to free VRAM. If it doesn't start in time, that hook continues with rules only. It doesn't run on native Windows.

### In my case

Laya is what gave me the confidence to let the agent loose at first: while the rules were few, the classifier caught the odd cases and I slept soundly with autonomous runs going. With weeks of trace, the rules learned what Laya flagged and the model stopped adding value. Today it's off by default, and the work is done by the rules that came out of its trace.

`laya` `classifier` `gpu` `measurements`
