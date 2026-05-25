# Internal Memory Policy for GPT-5.4

This policy is based on observed GPT-5.4 patterns across recent AI Village goals.

## What Internal Memory Is Best At

Internal memory has been most useful when it carries:
- identity and hard constraints
- the current goal and room
- the active project or task frontier
- exact canonical anchors like a repo head or one critical URL
- a short list of do-not-repeat communication cautions
- a few settled facts that prevent known repeated mistakes

## What Should Stay In Internal Memory

Keep only items that are either:
1. needed in nearly every session,
2. dangerous to forget, or
3. expensive to rediscover under action limits.

### Keep
- agent identity, room, and contact email
- operating rules that frequently affect behavior
- current village goal
- current active task and exact next step
- one canonical repo head or equivalent authoritative state anchor
- top 3-5 settled facts that prevent repeated work
- top 2-4 public communication cautions
- top 2-4 open loops

## What Should Move Out To External Memory

These items are important, but not worth keeping in the always-loaded blob unless they become active again.

### Offload
- long commit chains
- exhaustive published video lists and URLs
- historical analytics snapshots
- detailed concept-by-concept review notes
- per-shot visual findings once the concept is parked
- old bug diaries after the workaround is settled
- broad collaborator histories unless currently relevant
- repeated evidence logs that all support the same conclusion

## Promotion Rules

Move an item into `settled_facts` when:
- it has been verified more than once,
- it has remained stable across sessions, and
- forgetting it would cause repeated low-value checking.

Examples:
- commit-hash anchoring works well
- browser-local Firefox MP4 playback is not trusted verification evidence
- duplicate announcement risk should be checked against visible history first

## Demotion Rules

Move an item out of internal memory when:
- it is no longer action-driving,
- it duplicates a stable external file,
- it is a long list rather than a decision aid,
- it is historical context that can be retrieved later.

## Consolidation Heuristic

At consolidation time, prefer this shape:
- Identity / hard constraints: short and stable
- Active frontier: 3-5 bullets
- Settled facts: 3-5 bullets
- Public comms cautions: 2-4 bullets
- Open loops / next steps: 2-4 bullets

If a section grows beyond that, trim or offload.

Use `python3 tools/render_lean_memory.py` to generate a compact consolidation candidate with this section shape and a trailing `CHAR_COUNT=` line.

## Specific GPT-5.4 Lessons Behind This Policy

### Strengths to preserve
- exact commit-hash anchoring
- source-first verification instead of trusting chat summaries
- explicit duplicate-message checks before public posting
- strong next-session handoffs with a concrete next move

### Failure modes to reduce
- re-verifying already settled facts
- keeping long historical detail in the always-loaded blob
- carrying overly detailed project history after a goal changes
- uncertainty about whether a public announcement already exists

## Practical Start-of-Session Routine

1. Run `python3 tools/start_session.py`
2. Act from `active_frontier`
3. Consult `settled_facts` before re-checking something old
4. Consult `public_comms` before saying something publicly
5. Use `open_loops` to choose the next bounded action
