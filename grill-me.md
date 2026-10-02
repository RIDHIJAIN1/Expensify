---
name: grill-me
description: Interview the user relentlessly about a plan or design until reaching shared understanding, resolving each open question one by one and recording every answer to a durable log. Use when user wants to stress-test a plan, get grilled on their design, or mentions "grill me".
model: deepseek/deepseek-v4-pro
mode: all
---

Interview me relentlessly about every aspect of this plan until we reach a shared understanding, resolving each open question one-by-one. For each question, provide your recommended answer.

## Establish the slug

Before asking anything, propose a short kebab-case slug for this feature (e.g. `user-changelog`) and confirm it with me. Every later stage (`/write-prd`, `/prd-to-issues`) reuses this exact slug, so all artifacts line up.

## How to interview

Ask the questions **one at a time**.

If a question can be answered by exploring the codebase, explore the codebase instead of asking.

Ask **detailed, in-depth questions — not overview questions.** Cover the concrete details: data shapes / schema, API and interface contracts, edge cases, error / empty / failure behavior, auth and permissions, and non-functional limits. Keep going until the design is concrete enough that `/write-prd` needs to ask nothing further.

## Record every answer — incrementally

Persist the interview to `records/prds/{YYYY}/{MM}/{slug}/grilling-{slug}.md` **as you go**, where `{YYYY}`/`{MM}` are today's year/month. Create the directory tree (`records/prds/{YYYY}/{MM}/{slug}/`) before the first write if it doesn't already exist.

- **Why:** this log is the durable hand-off to `/write-prd`. The PRD is built from this file, not from chat memory — so if the session drops mid-interview, nothing answered so far is lost.
- **When:** write the file once at the start (problem statement), then **append one block immediately after each question is answered.** Do not batch the writes until the end.
- **What:** the full question-and-answer for every question, plus the rationale and where the answer came from.

Use this structure:

```markdown
# Grilling log — {slug}

## Problem statement
[the feature / problem in the user's words]

## Q&A
### Q1 — [the exact question asked]
- **Answer:** [the user's answer / what was decided]
- **Rationale:** [why / trade-off]
- **Source:** user | codebase (file:line)

### Q2 — [...]
- **Answer:** ...

## Open / deferred
- [anything explicitly punted, with why]
```

The only output is this local log file. Do not create any GitHub issue.

When the interview is complete, point me to the next step: `/write-prd` (which reads `records/prds/{YYYY}/{MM}/{slug}/grilling-{slug}.md`).
    