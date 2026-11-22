**08**

# What others measured

[← Index](README.md)

---

These are tests published by third parties, each with its source. The numbers are theirs **[published]**.

### The most complete benchmark: Bicameral AI

[Bicameral AI](https://github.com/Bicameral-AI/claude-code-mode-benchmark) published prompts, data and verifier: six tasks, four models, two runs per combination, 96 runs on 2.1.326 and another 96 on 2.1.325, all at `medium` effort.

| Processed-token saving (2.1.326) | Opus 5.5 | Sonnet 5.5 | Haiku 5.5 | Fable 5.2 |
| :-- | --: | --: | --: | --: |
| Aggregate 120 records via MCP | 77 % | 67 % | 62 % | 71 % |
| Read and classify 120 records via MCP | 68 % | 49 % | 40 % | 61 % |
| Search and modify local files | 37 % | 54 % | **−9 %** | 15 % |
| Answer a question about one file | 29 % | 30 % | 29 % | 29 % |

- In the MCP aggregation, added context fell 84–94 % and all 16 runs answered correctly.
- On file tasks, added context **grew** with Code Mode in 14 of 16 comparisons.
- Haiku's −9 % came mostly from one run that searched the wrong directory.
- Their own caveats: the data was synthetic with patterns that favored filtering, and they advise against quoting a single percentage.

### Tests on real repositories

| Test | Without → with Code Mode | What was observed |
| :-- | :-- | :-- |
| [wmedia](https://wmedia.es/es/tips/claude-code-code-mode-activar): aggregate orders from 40 JSON files, Opus 5.5 | 150,364 → 94,659 input tokens (cache included); **15 → 37 s** | Same answer and four requests in both; in normal mode Claude already used a Python script |
| [Flavio Copes](https://flaviocopes.com/claude-code-code-mode/): broken links and checks in an Astro project | Links 35 → 15 s; checks 17 → 14 s | Normal mode already parallelized independent commands |
| [Issue #111033](https://github.com/anthropics/claude-code/issues/111033): broken links in 432 Markdown files, Opus 5.5 on WSL2 | **40 → 96 s**; US$0.58 → US$0.62 | Same result; Claude went from a Python scan to 742 reads |
| [Issue #111178](https://github.com/anthropics/claude-code/issues/111178): edit 100 files and 10 web questions | Edit 17.6 → 48.7 s, US$0.341 → US$0.285; web 34.0 → 27.7 s, US$0.498 → US$0.303 | Three runs per mode; delegating to an orchestrator subagent gained nothing |
| [bestagent.dev](https://bestagent.dev/claude-code-code-mode-cost-tested-2026/): implement a CLI option with tests, Opus 5.5 | 10–13 → 6–8 requests; 71–97 → 57–63 s; US$0.43–0.47 → US$0.34–0.36 | Tests green in all; editing 20 files cost and took the same |
| [claude-code-lab](https://www.claude-code-lab.com/blog/claude-code-code-mode): 72 runs, 3 models | Lower estimated cost in all 12 conditions (~41–44 %) | Best case, 40 MCP queries with Opus; broken links 12–32 % slower |

### What they say together

1. The fixed saving (~13 thousand tokens per session) is consistent across all of them.
2. The big saving shows up with many aggregatable MCP calls.
3. On local files, little or nothing, and sometimes slower.
4. Filters can hide data.
5. Nobody measured the effect on plan limits.

`benchmarks` `community` `comparison`
