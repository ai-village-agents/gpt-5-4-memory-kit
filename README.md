# GPT-5.4 Memory Kit

Small, self-contained Python + Markdown toolkit for running an AI Village agent under strict session limits.

## Problem This Solves

When sessions are short and context windows are tight, agents commonly fail in three ways:

- re-checking facts that were already settled
- storing everything in one dense memory blob
- repeating public announcements because status is unclear

This kit uses a strict five-part memory model so each memory type has one job.

## Five-Part Memory Model

### 1) `identity_constraints`

What it is:
- stable role, operating constraints, and hard behavior rules

Why it exists:
- avoids drift in identity and process when session context is truncated

What should go here:
- non-negotiable behavior rules (`one-tool-call rule`)
- role + environment anchors (AI Village, room `#rest`, contact email)

What should NOT go here:
- temporary tasks
- observations that might change
- status updates

### 2) `active_frontier`

What it is:
- current priorities and next actions for this phase

Why it exists:
- keeps the agent focused on now, not on full history

What should go here:
- active goals (for day-419: `Improve your memory`)
- immediate tasks and high-priority `do-not-repeat` reminders

What should NOT go here:
- evergreen truths (belongs in `settled_facts`)
- already completed communication logs (belongs in `public_comms`)

### 3) `settled_facts`

What it is:
- facts considered stable enough to stop re-verifying every session

Why it exists:
- prevents repeated verification loops

What should go here:
- durable technical findings with lightweight evidence notes
- proven patterns like commit-hash anchoring
- known unreliable signals (example: Firefox local MP4 playback is not trusted evidence)

What should NOT go here:
- open questions
- TODO items
- speculative claims

### 4) `public_comms`

What it is:
- explicit record of what was already announced publicly, or what must not be repeated

Why it exists:
- removes uncertainty around "did I already announce this?"

What should go here:
- entries with a clear state: `announced` or `do_not_repeat`
- short summary, audience, and date

What should NOT go here:
- internal planning details
- vague notes with no announcement state

### 5) `open_loops`

What it is:
- unresolved questions and external dependencies

Why it exists:
- preserves unfinished work without polluting settled memory

What should go here:
- unanswered questions, owners, and next check actions

What should NOT go here:
- completed outcomes
- broad narrative history

## How This Maps to Memory Best Practices

Plain-language mapping to common ideas in Generative Agents, MemGPT, and long-term-memory guidance:

- Separate memory tiers by purpose, not by time alone.
  - This kit splits stable identity, active working set, stable facts, public communication state, and open loops.
- Keep a small active working set.
  - `active_frontier` should stay short and action-oriented.
- Promote only stable, evidenced items into durable memory.
  - `settled_facts` is for high-confidence facts, not ongoing tasks.
- Track social/public state explicitly.
  - `public_comms` prevents duplicate announcements and coordination mistakes.
- Keep unresolved items isolated.
  - `open_loops` captures uncertainty without contaminating facts.

## Practical Use Pattern

1. Start session with `tools/start_session.py` (or `tools/build_session_brief.py` if you only want the brief).
2. Work from `active_frontier` and `open_loops` only.
3. If something becomes stable, move it into `settled_facts`.
4. If you post publicly, record it in `public_comms` with explicit state.
5. Run `tools/audit_memory_store.py` to catch bloat and schema drift.

## Commands

From project root:

```bash
python3 tools/start_session.py
python3 tools/build_session_brief.py
python3 tools/render_lean_memory.py
python3 tools/audit_memory_store.py
python3 tools/pre_send_chat.py --purpose '...' --recipient '...' --topic '...' --duplicate-check '...'
python3 -m unittest discover -s tests -p 'test_*.py' -v
```

Short consolidation candidate example:

```bash
python3 tools/render_lean_memory.py
```

Optional helper:

```bash
make test
make brief
make audit
```

## Additional Guide

- [`docs/INTERNAL_MEMORY_POLICY.md`](docs/INTERNAL_MEMORY_POLICY.md) — concrete rules for what should stay in internal memory vs. move out to external storage.
- [`docs/GPT54_LEAN_MEMORY_DRAFT.md`](docs/GPT54_LEAN_MEMORY_DRAFT.md) — a compact target shape for future GPT-5.4 memory rewrites.
- [`docs/METRICS_SCHEMA.md`](docs/METRICS_SCHEMA.md) — lightweight shared metric labels for cross-session external-memory evaluation.
