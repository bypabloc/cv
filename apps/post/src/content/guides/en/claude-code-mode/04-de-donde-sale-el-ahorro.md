**04**

# Where the savings come from

[← Index](README.md)

---

### Source 1: fewer tool definitions (fixed)

Instead of a dozen tools with long descriptions, the model gets `REPL` and `Poll`. In `/context`, "System tools" drop from about 25k to about 11k tokens, and every session starts about **13 thousand tokens smaller**, even for a trivial question **[published]**. That saving is paid on every request of the session.

### Source 2: intermediate results don't go back to the model (variable)

When the script processes the tools' output and returns only a summary, everything intermediate (records, files read, logs) never enters the context. This is the big saving, but it only shows up when the task **can be reduced**: a total, a count, a short list. If the script prints the raw data, the saving disappears.

### Source 3: fewer trips to the model (sometimes)

Chaining steps in one block can save requests. But not always: with the mode on there are extra `Poll` requests, and in some tests the number of requests even went up while cost went down, because each request was cheaper.

### The 37 % myth

The "37 % fewer tokens" that circulated in the first days isn't from Code Mode: it comes from a *Programmatic Tool Calling* evaluation on Anthropic's API, from 2025. Other viral numbers (77 %, 98.7 %) come from a single favorable task or from other contexts. A percentage without the task that produced it says nothing **[judgment]**.

### Tokens aren't cost or quota

- Cache reads count as processed tokens but cost a fraction.
- Public tests measured tokens or estimated cost at API prices. **Nobody published how much longer the 5-hour or weekly quota** of a subscription lasts.
- Time is another metric: a cheaper mode can take longer.

### In my case

In my sessions with the mode, each request read much less cached context than in my normal sessions in the same period ([ch. 07](07-mis-mediciones.md)). Part of that is Source 1 and part is Source 2, but I can't separate them without an A/B: that's why chapter 11 explains how to measure it task by task.

`savings` `tokens` `context` `myths`
