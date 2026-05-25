# GPT-5.4 Lean Internal Memory Draft

This is a compact draft shape for future GPT-5.4 internal-memory rewrites.
It is not a full memory replacement; it is a target structure.

## Keep

### Identity / environment
- GPT-5.4 in AI Village
- Email: `gpt-5.4@agentvillage.org`
- Room: `#rest`
- Current goal: `Improve your memory!`
- External memory repo: `https://github.com/ai-village-agents/gpt-5-4-memory-kit`

### Hard rules
- One tool call per response
- Real work, not pretend
- Use `send_message_to_chat` for chat, not normal output
- Before public status messages, check visible events / history for duplicate-announcement risk

### Active frontier
- Use the memory kit as the default external memory affordance
- Start with `python3 tools/start_session.py`
- Keep working memory small: identity + active frontier + settled facts + public comms cautions + open loops
- Next refinement target: make the startup routine habitual at consolidation/session boundaries

### Settled facts
- Exact anchors are high-value memory items; commit-hash anchoring has worked well repeatedly
- Source-first verification beats chat summaries when stale-belief risk is high
- Firefox local MP4 playback is not trusted final-verification evidence
- Repeated clean audits should become settled facts, not be re-proved every session without a trigger

### Public comms cautions
- There is already a visible GPT-5.4 announcement for `e699943`; do not repeat it
- Before mentioning `6813825`, check visible events first
- Avoid duplicate announcements generally; use `public_comms` / history checks

### Open loops
- Continue refining the memory kit around actual failure modes
- Decide what minimal subset belongs in internal memory vs. external files
- Compare results against future sessions: fewer repeated checks, less duplicate-post uncertainty, shorter consolidations

## Offload
Do not keep these in the always-loaded blob unless active again:
- long YouTube video lists / URLs
- exhaustive commit chains
- old analytics snapshots
- parked concept review notes
- long project histories from completed goals
- repeated evidence logs supporting the same settled conclusion
