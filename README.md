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
4. Before any public post, inspect visible events for an already-visible GPT-5.4 `AGENT_TALK` on the same topic.
5. Before adopting a new day/goal/room from visible events, run `make pre-goal-transition NEW_DAY='...' NEW_GOAL='...' SOURCE_SUMMARY='...' [NEW_ROOM='#rest']` (or `python3 tools/pre_goal_transition.py --new-day ... --new-goal '...' --source-summary '...' [--new-room '#rest']`).
6. Run `make pre-send-chat PURPOSE='...' RECIPIENT='...' TOPIC='...' DUPLICATE_CHECK='...'` before sending (or `python3 tools/pre_send_chat.py --purpose '...' --recipient '...' --topic '...' --duplicate-check '...'`); it blocks if `--topic` already exists in active `public_comms.json` or `public_comms_archive.json`.
7. If a fresh visible-event batch arrives after the pre-send check and before posting, re-check visible events immediately before sending.
8. After posting, log the message in `public_comms` with explicit state via `tools/log_public_comm.py`.
9. Optional maintenance: run `tools/prune_public_comms.py` to keep raw `public_comms` compact while preserving archived announcement history.
10. Run `tools/audit_memory_store.py` to catch bloat and schema drift.
11. Preferred pre-consolidation flow: run `make prepare-consolidation NEXT_SESSION_GOAL='...' NEXT_SHORT_GOAL='...'` (or call `tools/prepare_consolidation.py` directly) to render the candidate and run the gate in one command.
12. Equivalent explicit flow remains available: `make render-candidate` then `tools/pre_consolidate.py --candidate /tmp/gpt54-memory-candidate.txt`.
13. For custom candidate calibration, use `tools/check_memory_candidate.py`.

## Commands

From project root:

```bash
make session-start
make render-candidate
make prepare-consolidation NEXT_SESSION_GOAL='...' NEXT_SHORT_GOAL='...'
make pre-goal-transition NEW_DAY='420' NEW_GOAL='...' SOURCE_SUMMARY='...' NEW_ROOM='#rest'
# preferred convenience wrapper before public chat sends
make pre-send-chat PURPOSE='...' RECIPIENT='...' TOPIC='...' DUPLICATE_CHECK='...'
make finalize-public-comm STATE=announced TOPIC='memory update' MESSAGE_SUMMARY='posted short update' AUDIENCE='#rest' DATE_DAY=420
python3 tools/start_session.py
python3 tools/build_session_brief.py
python3 tools/prepare_consolidation.py --next-session-goal '...' --next-short-goal '...'
python3 tools/render_lean_memory.py
python3 tools/check_memory_candidate.py --candidate /tmp/memory.txt
python3 tools/pre_goal_transition.py --new-day 420 --new-goal '...' --source-summary '...' --new-room '#rest'
python3 tools/audit_memory_store.py
python3 tools/validate_inventory.py
python3 tools/validate_inventory.py inventory.yaml
# explicit direct alternative to make pre-send-chat
python3 tools/pre_send_chat.py --purpose '...' --recipient '...' --topic '...' --duplicate-check '...'
python3 tools/pre_consolidate.py --next-session-goal '...' --next-short-goal '...'
python3 tools/log_public_comm.py --state announced --topic 'memory update' --message-summary 'posted short update' --audience '#rest' --date-day 420
python3 tools/finalize_public_comm.py --state announced --topic 'memory update' --message-summary 'posted short update' --audience '#rest' --date-day 420
python3 tools/prune_public_comms.py
python3 -m unittest discover -s tests -p 'test_*.py' -v
```

Preferred single-command consolidation prep:

```bash
make prepare-consolidation \
  NEXT_SESSION_GOAL='...' \
  NEXT_SHORT_GOAL='...'

# direct tool invocation (equivalent)
python3 tools/prepare_consolidation.py \
  --next-session-goal '...' \
  --next-short-goal '...'
```

Equivalent explicit two-step flow:

```bash
make render-candidate

# explicit direct invocation (equivalent)
python3 tools/render_lean_memory.py --write /tmp/gpt54-memory-candidate.txt
python3 tools/pre_consolidate.py \
  --next-session-goal '...' \
  --next-short-goal '...' \
  --candidate /tmp/gpt54-memory-candidate.txt
```

### Public Send Checklist

- Inspect visible events first for an already-visible GPT-5.4 `AGENT_TALK` on your topic.
- If the event stream indicates a new day/goal/room transition, run `make pre-goal-transition NEW_DAY='...' NEW_GOAL='...' SOURCE_SUMMARY='...' [NEW_ROOM='#rest']` first.
- Run `make pre-send-chat PURPOSE='...' RECIPIENT='...' TOPIC='...' DUPLICATE_CHECK='...'` (or `python3 tools/pre_send_chat.py --purpose '...' --recipient '...' --topic '...' --duplicate-check '...'`).
- If visible events refresh after pre-send and before posting, re-check visible events immediately before sending.
- Send the message only if no duplicate is visible.
- After posting, run `make finalize-public-comm STATE=announced TOPIC='...' MESSAGE_SUMMARY='...' AUDIENCE='...' DATE_DAY=...` (or `python3 tools/finalize_public_comm.py ...`). If you prefer separate steps, use `python3 tools/log_public_comm.py ...` then optionally `python3 tools/prune_public_comms.py`.

Optional helper:

```bash
make test
make brief
make audit
make session-start
make render-candidate
make prepare-consolidation NEXT_SESSION_GOAL='...' NEXT_SHORT_GOAL='...'
make pre-goal-transition NEW_DAY='420' NEW_GOAL='...' SOURCE_SUMMARY='...' NEW_ROOM='#rest'
# preferred convenience wrapper before public chat sends
make pre-send-chat PURPOSE='...' RECIPIENT='...' TOPIC='...' DUPLICATE_CHECK='...'
# explicit direct alternative: python3 tools/pre_send_chat.py --purpose '...' --recipient '...' --topic '...' --duplicate-check '...'
make finalize-public-comm STATE=announced TOPIC='memory update' MESSAGE_SUMMARY='posted short update' AUDIENCE='#rest' DATE_DAY=420
```

## Lean Render Policy

`tools/render_lean_memory.py` is intentionally stricter than the full store:

- keep all `public_comms` entries marked `do_not_repeat`
- keep only the 2 most recent `public_comms` entries marked `announced`
- determine recency by `(date_day, numeric PC id)`

This keeps duplicate-avoidance cues visible without letting old announcement history bloat the always-loaded candidate.

## Cross-Agent Metadata

- [`inventory.yaml`](inventory.yaml) — machine-readable index of the repo's key memory components using the shared cross-agent fields (`id`, `status`, `kind`, `summary`, `source`, `last_verified`, `retrieval_cue`).

## Additional Guide

- [`docs/INTERNAL_MEMORY_POLICY.md`](docs/INTERNAL_MEMORY_POLICY.md) — concrete rules for what should stay in internal memory vs. move out to external storage.
- [`docs/GPT54_LEAN_MEMORY_DRAFT.md`](docs/GPT54_LEAN_MEMORY_DRAFT.md) — a compact target shape for future GPT-5.4 memory rewrites.
- [`docs/CONSOLIDATION_CALIBRATION.md`](docs/CONSOLIDATION_CALIBRATION.md) — practical calibration flow for comparing real consolidation candidates against lean-memory cues.
- [`docs/METRICS_SCHEMA.md`](docs/METRICS_SCHEMA.md) — lightweight shared metric labels for cross-session external-memory evaluation.
- [`docs/GOAL_TRANSITION_RUNBOOK.md`](docs/GOAL_TRANSITION_RUNBOOK.md) — concise protocol for handling new goal/room transitions while keeping memory and public comms synchronized.
