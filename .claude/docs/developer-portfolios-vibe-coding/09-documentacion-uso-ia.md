---
title: Documentacion del Uso de IA
description: Como mencionar IA en portfolio sin penalizar, opciones y prompts como portfolio value
parent: developer-portfolios-vibe-coding
---

[← Anterior: Junior/Mid/Senior](08-niveles-junior-mid-senior.md) | [README](README.md) | [Siguiente: Tendencias emergentes →](10-tendencias-emergentes.md)

# Documentacion del Uso de IA

## Como Mencionar IA en Portfolio: The Honest Spectrum

### EVITAR

```markdown
"Built with Claude Code"        # Sounds like you didn't code
"AI-generated codebase"          # Red flag: can't maintain it
"Entire app written by ChatGPT"  # Recruiter will distrust quality
No mention of AI at all          # Suspicious if it's obviously fast
```

### APPROACH CORRECTO

**Option 1: Transparent Workflow (Recomendado)**

```markdown
## Technical Approach

This project was built with:
- **Architecture & design**: Hand-crafted (3 days planning)
- **Boilerplate & utilities**: AI-assisted (Cursor) → reviewed & tested
- **Complex features**: Pair of Claude Code for logic + manual testing
- **Code quality**: 100% covered by tests I wrote

**Time savings**: ~35% in routine code patterns, 0% in architecture  
**Quality**: Same as hand-crafted, fully audited

*Why transparency:* Knowing HOW code was built determines if I can maintain it.
```

**Option 2: Feature-Focused (Alternative)**

```markdown
## Key Features
1. **Real-time sync** — WebSocket + Postgres LISTEN/NOTIFY
2. **Conflict resolution** — Last-write-wins with timestamps
3. **Full-text search** — PostgreSQL pg_trgm with ranking

Built solo with Cursor + manual testing. Shipped in 6 weeks.
```

(Implicitly signals "I shipped solo" = strong signal, whether AI-assisted or not.)

**Option 3: Honest (Best for Recruiters)**

En la seccion "Build Process" en tu README:

```markdown
## How It Was Built

**Tooling & Time-saving:**
- Cursor for inline suggestions (autocomplete + small edits)
- Claude Code for refactoring (multi-file changes)
- Tests written manually (non-negotiable quality gate)

**Why this approach?**
Vibe coding lets me focus on architecture instead of typing.  
All AI output audited before commit—hallucinations caught early.

**Verify code quality:**
- Run tests: `npm test` (100% coverage)
- Audit diff: git log shows human intent
- Check architecture: [ADR doc](links) explains design decisions
```

## Prompts You Showed = Portfolio Value

**Nueva tendencia:** Documentar el PROCESO, no ocultar.

```markdown
## How I Built [Feature] With AI

**Problem:** Implement 3-month feature in 2 weeks.

**My approach:**
1. Architecture doc (hand-sketched)
2. Asked Claude Code: "Generate 80% boilerplate given this schema"
3. Manual review & test writing (1-2h per 100 LOC)
4. Iterative refactoring: prompt engineer edge cases

**Prompt used:**
```

```
Given this PostgreSQL schema and this Jest test file, 
generate TypeScript services with proper error handling.
Requirements:
- Use constructor injection
- Throw custom ApplicationError
- Add logging to critical points
```

```
Result: [GitHub link] — Takes 2 weeks, I did it in 3 days.
```

## What Recruiters Infer

| Si dices... | Recruiter piensa... |
|------------|-------------------|
| "Built with Claude Code" | "No programas, delegaste" |
| "AI-assisted, all reviewed" | "Entiende limitaciones, quality-conscious" |
| "Hand-crafted architecture, AI boilerplate" | "Separas concerns, knows what AI does well" |
| No mention | "Oculta, tal vez AI heavy o ashamed" |
| "Built solo in 2 weeks vs 6 months normally" | "Productivo, BUT—will this scale?" |

---

[← Anterior: Junior/Mid/Senior](08-niveles-junior-mid-senior.md) | [README](README.md) | [Siguiente: Tendencias emergentes →](10-tendencias-emergentes.md)
