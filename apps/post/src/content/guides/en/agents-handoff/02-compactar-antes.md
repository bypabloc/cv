**02**

# Compact earlier

[← Index](README.md)

---

### Goal

Compact with **30 to 40 % of the window free** (60–70 % used), with the configuration **versioned in the repo** and without touching the user's global configuration. Compacting earlier does not replace the handoff: it only improves the summary.

### Claude Code: `.claude/settings.json`

```json
{ "env": { "CLAUDE_AUTOCOMPACT_PCT_OVERRIDE": "60" }, "autoCompactEnabled": true }
```

- Compacts at 60 % (~600K with 1M). **[doc]** ([env-vars](https://code.claude.com/docs/en/env-vars))
- The override **can only lower the threshold**: a value above the factory one is ignored. **[doc]**
- The project `env` applies after the folder's trust is accepted. **[doc]**
- Token-based alternatives: `CLAUDE_CODE_AUTO_COMPACT_WINDOW` or `autoCompactWindow`. There are also `/autocompact` and `DISABLE_COMPACT`. **[doc]**
- With a gateway or a custom model id, check the window: the percentage is computed over the window Claude Code believes the model has.

### Codex: `.codex/config.toml`

```toml
model_post_turn_compact_threshold_percent = 65   # at the end of each turn
model_auto_compact_token_limit = 190000          # mid-turn cap: 70 % of 272k; recompute per model
project_doc_max_bytes = 65536                    # if AGENTS.md is over 32 KiB
```

- The two mechanisms complement each other: the percentage is only evaluated when a turn **ends**, and a long turn with many tools can go past it without compacting. **[doc]**
- That `model_auto_compact_token_limit` acts mid-turn comes from a blog, not the documentation. **[community]**
- The effective limit is the lower of the configured one and 90 % of the window (upstream code, undocumented).
- The project path must be **trusted** for Codex to load `.codex/config.toml`. **[doc + test]**

| Use of 272k | Tokens |
| :-- | :-- |
| 60 % | 163 200 |
| 65 % | 176 800 |
| 70 % | 190 400 |

A token cap depends on the model: 190 000 is 70 % of 272k, but with a 500k window it would compact at 38 %.

### OpenCode: `opencode.json`

```json
{ "compaction": { "buffer": 400000 } }
```

- `buffer` is the **free tokens** before compacting: 400 000 free = compact at 60 % of 1M.
- The V2 documentation accepts `"40%"`, but 2.0.29 **silently drops** anything that is not an integer. **[test]**
- The background service caches the configuration: after changing it, `opencode service restart`.

### Antigravity: no versionable setting

There is only the `AGY_CLI_AUTO_COMPACT_OVERRIDE` variable, which is undocumented **[bin]**: better not to depend on it. The handoff injected on **every** invocation makes up for it ([ch. 05](05-configurar-cada-agente.md)).

### How to check it

| Agent | Check |
| :-- | :-- |
| Claude Code | A real `/compact`: the handoff shows up in the transcript after compacting ([ch. 10](10-probar-el-handoff.md)) |
| Codex | `codex debug prompt-input` exits 0; with an invalid value on purpose it exits 1 and names the key, which proves it reads the file |
| OpenCode | `opencode service restart && opencode debug config` shows `compaction: {buffer: 400000}`; a key that does not show up was dropped |
| Antigravity | Not applicable |

### Limits

- **Token values depend on the model.** If you switch models, recompute Codex's cap and OpenCode's `buffer`. Percentages don't have this problem.
- **None of this measures summary quality.** I did not measure the summary at 60 % against 97 %; the improvement is **[judgment]**.

### In my case

I ended up with Claude Code at 60 %, Codex at 65 % plus the 190 000 cap, and OpenCode with `buffer: 400000`. The stumble was OpenCode: the `"40%"` that the V2 documentation accepts vanished from `opencode debug config` without a single error. Since then I check every configuration change with the command that shows what the agent **validated**, not what I wrote. In Codex, `AGENTS.md` weighed ~50 KB and was read truncated to 32 KiB without warning: that is where the example's `project_doc_max_bytes` comes from ([ch. 12](12-problemas-y-soluciones.md)).

`compaction` `threshold` `configuration`
